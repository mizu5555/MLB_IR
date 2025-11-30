"""
MLB Team Manager Assistant - Flask Backend
支援純 RAG 和 RAG + LLM 兩種模式
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_router import QueryRouter
from prompt_templates import PromptTemplates
from phase6_hybrid_search import HybridSearch
import json

app = Flask(__name__, static_folder='static')
CORS(app)

# 初始化組件
print("\n初始化 MLB RAG 系統...")
query_router = QueryRouter()
prompt_templates = PromptTemplates()
hybrid_search = HybridSearch()
print("✅ 系統初始化完成！\n")

# 檢查 Ollama 是否可用
OLLAMA_AVAILABLE = False
try:
    import ollama
    models = ollama.list()
    if hasattr(models, 'models') and models.models:
        OLLAMA_AVAILABLE = True
        OLLAMA_MODEL = models.models[0].model if hasattr(models.models[0], 'model') else 'llama3.2'
        if ':' in OLLAMA_MODEL:
            OLLAMA_MODEL = OLLAMA_MODEL.split(':')[0]
        print(f"✅ Ollama 可用，模型: {OLLAMA_MODEL}")
    else:
        print("⚠️ Ollama 未檢測到模型")
except:
    print("⚠️ Ollama 不可用，僅支援純 RAG 模式")


@app.route('/')
def index():
    """主頁面"""
    return send_from_directory('static', 'index.html')


@app.route('/api/status')
def status():
    """系統狀態"""
    return jsonify({
        'status': 'ok',
        'ollama_available': OLLAMA_AVAILABLE,
        'ollama_model': OLLAMA_MODEL if OLLAMA_AVAILABLE else None,
        'database_size': 4387
    })


def extract_answer_from_results(query, search_results, classification):
    """從檢索結果中提取答案（純 RAG 模式）"""
    
    if not search_results:
        return "抱歉，沒有找到相關數據。"
    
    top_result = search_results[0]
    player_id = top_result['player_id']
    full_text = top_result['full_text']
    
    query_type = classification['query_type']
    language = classification['language']
    
    # 提取球員名和賽季
    import re
    player_match = re.search(r'Player: ([^.]+)\.', full_text)
    season_match = re.search(r'Season: (\d+)', full_text)
    
    player_name = player_match.group(1) if player_match else player_id.split('_')[0]
    season = season_match.group(1) if season_match else 'Unknown'
    
    # 擴展的統計映射（中英文關鍵詞 + 多種可能的字段名）
    stat_mappings = {
        # 全壘打 - 多種可能的字段名
        'home run': ('HR|Home Runs|HomeRuns', '全壘打', 'home runs'),
        'hr': ('HR|Home Runs|HomeRuns', '全壘打', 'home runs'),
        '全壘打': ('HR|Home Runs|HomeRuns', '全壘打', 'home runs'),
        
        # 打擊率
        'batting average': ('BA|AVG|Batting Average', '打擊率', 'batting average'),
        'average': ('BA|AVG|Batting Average', '打擊率', 'batting average'),
        '打擊率': ('BA|AVG|Batting Average', '打擊率', 'batting average'),
        'ba': ('BA|AVG|Batting Average', '打擊率', 'batting average'),
        
        # 防禦率
        'era': ('ERA|Earned Run Average', '防禦率', 'ERA'),
        '防禦率': ('ERA|Earned Run Average', '防禦率', 'ERA'),
        
        # 三振
        'strikeout': ('K%|SO|Strikeouts|K', '三振率', 'strikeout rate'),
        'k%': ('K%|K', '三振率', 'strikeout rate'),
        '三振': ('K%|SO|Strikeouts|K', '三振率', 'strikeout rate'),
        
        # OPS
        'ops': ('OPS|On-base Plus Slugging', 'OPS', 'OPS'),
        
        # wOBA
        'woba': ('wOBA|Expected wOBA', 'wOBA', 'wOBA'),
        
        # 出棒初速
        'exit velocity': ('Exit Velocity|ExitVelo', '出棒初速', 'exit velocity'),
        '出棒初速': ('Exit Velocity|ExitVelo', '出棒初速', 'exit velocity'),
        
        # 跑速
        'sprint speed': ('Sprint Speed|SprintSpeed', '跑速', 'sprint speed'),
        'speed': ('Sprint Speed|SprintSpeed', '跑速', 'sprint speed'),
        '跑速': ('Sprint Speed|SprintSpeed', '跑速', 'sprint speed'),
        
        # 上壘率
        'obp': ('OBP|On-Base Percentage', '上壘率', 'on-base percentage'),
        '上壘率': ('OBP|On-Base Percentage', '上壘率', 'on-base percentage'),
        
        # 長打率
        'slg': ('SLG|Slugging Percentage', '長打率', 'slugging percentage'),
        '長打率': ('SLG|Slugging Percentage', '長打率', 'slugging percentage'),
        
        # 打點
        'rbi': ('RBI|Runs Batted In', '打點', 'RBI'),
        '打點': ('RBI|Runs Batted In', '打點', 'RBI'),
        
        # 得分
        'run': ('R|Runs|Runs Scored', '得分', 'runs'),
        '得分': ('R|Runs|Runs Scored', '得分', 'runs'),
        
        # WHIP
        'whip': ('WHIP|Walks and Hits per Inning Pitched', 'WHIP', 'WHIP'),
        
        # 勝場
        'win': ('W|Wins', '勝場', 'wins'),
        '勝場': ('W|Wins', '勝場', 'wins'),
    }
    
    # 查找查詢中的關鍵詞
    query_lower = query.lower()
    found_stat = None
    stat_name_cn = None
    stat_name_en = None
    stat_value = None
    
    for keyword, (pattern, name_cn, name_en) in stat_mappings.items():
        if keyword in query_lower:
            # 嘗試多種格式匹配（更寬鬆的匹配）
            patterns = [
                f'{pattern}[:\s]+([0-9]+\.?[0-9]*)',  # HR: 62 或 BA: 0.311
                f'{pattern}\s*=\s*([0-9]+\.?[0-9]*)',  # HR = 62
                f'{pattern}\s+([0-9]+\.?[0-9]*)',      # HR 62
                f'{pattern}[:\s]*\(([0-9]+\.?[0-9]*)\)',  # HR: (62)
            ]
            
            for p in patterns:
                match = re.search(p, full_text, re.IGNORECASE)
                if match:
                    stat_value = match.group(1)
                    stat_name_cn = name_cn
                    stat_name_en = name_en
                    found_stat = pattern.split('|')[0]  # 取第一個作為顯示名稱
                    break
            
            if stat_value:
                break
    
    # 生成簡潔答案
    if stat_value:
        if language == 'zh':
            # 根據不同統計類型使用不同的表達方式
            if stat_name_cn == '全壘打':
                answer = f"{player_name} 在 {season} 年打了 {stat_value} 支全壘打"
            elif stat_name_cn in ['打擊率', '上壘率', '長打率', 'OPS', 'wOBA']:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
            elif stat_name_cn in ['防禦率', 'ERA', 'WHIP']:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
            elif stat_name_cn in ['三振率', '保送率']:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}%"
            elif stat_name_cn in ['出棒初速', '跑速']:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
            elif stat_name_cn in ['打點', '得分', '勝場']:
                answer = f"{player_name} 在 {season} 年有 {stat_value} 個{stat_name_cn}"
            else:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
        else:
            # 英文表達
            if stat_name_en == 'home runs':
                answer = f"{player_name} hit {stat_value} home runs in {season}"
            elif stat_name_en in ['batting average', 'on-base percentage', 'slugging percentage', 'OPS', 'wOBA']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en in ['ERA', 'WHIP']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en == 'strikeout rate':
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}%"
            elif stat_name_en in ['exit velocity', 'sprint speed']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en in ['RBI', 'runs', 'wins']:
                answer = f"{player_name} had {stat_value} {stat_name_en} in {season}"
            else:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
    else:
        # 沒找到特定統計，給出簡潔說明
        if language == 'zh':
            answer = f"根據檢索結果，找到 {player_name} {season} 年的數據。請在下方檢索詳情中查看具體統計數據。"
        else:
            answer = f"Found data for {player_name} in {season}. Please check the search details below for specific statistics."
    
    return answer


@app.route('/api/query', methods=['POST'])
def query():
    """處理查詢"""
    
    data = request.json
    user_query = data.get('query', '')
    mode = data.get('mode', 'rag')  # 'rag' 或 'llm'
    
    if not user_query:
        return jsonify({'error': '查詢不能為空'}), 400
    
    try:
        # 步驟 1: 查詢分類
        classification = query_router.classify_query(user_query)
        
        # 步驟 2: 獲取檢索參數
        retrieval_params = query_router.get_retrieval_params(classification)
        k = retrieval_params['k']
        
        # 步驟 3: 執行檢索
        search_results = hybrid_search.auto_search(user_query, k=k)
        
        # 格式化檢索結果
        formatted_results = []
        for i, result in enumerate(search_results[:5], 1):
            formatted_results.append({
                'rank': i,
                'player_id': result['player_id'],
                'score': round(result['score'], 4),
                'preview': result['text_preview'][:200],
                'full_text': result['full_text']
            })
        
        # 根據模式決定是否使用 LLM
        if mode == 'llm' and OLLAMA_AVAILABLE:
            # 生成提示詞
            prompt = prompt_templates.get_prompt(
                query_type=classification['query_type'],
                query=user_query,
                search_results=search_results,
                language=classification['language']
            )
            
            # 調用 Ollama
            try:
                import ollama
                response = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                answer = response['message']['content']
                
                return jsonify({
                    'mode': 'llm',
                    'query': user_query,
                    'classification': {
                        'type': classification['query_type'],
                        'confidence': classification['confidence'],
                        'language': classification['language']
                    },
                    'search_results': formatted_results,
                    'answer': answer,
                    'model': OLLAMA_MODEL
                })
            
            except Exception as e:
                # LLM 失敗，降級到純 RAG
                return jsonify({
                    'mode': 'rag',
                    'query': user_query,
                    'classification': {
                        'type': classification['query_type'],
                        'confidence': classification['confidence'],
                        'language': classification['language']
                    },
                    'search_results': formatted_results,
                    'error': f'LLM 調用失敗，降級到純 RAG: {str(e)}'
                })
        
        else:
            # 純 RAG 模式 - 提取答案
            extracted_answer = extract_answer_from_results(user_query, search_results, classification)
            
            return jsonify({
                'mode': 'rag',
                'query': user_query,
                'classification': {
                    'type': classification['query_type'],
                    'confidence': classification['confidence'],
                    'language': classification['language']
                },
                'search_results': formatted_results,
                'answer': extracted_answer  # 添加提取的答案
            })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/examples')
def examples():
    """預定義查詢範例"""
    
    return jsonify({
        'rag_examples': [
            {
                'category': 'Factual - 球員數據',
                'queries': [
                    'Aaron Judge 2022年打了幾支全壘打？',
                    'What was Juan Soto\'s batting average in 2024?',
                    'Shohei Ohtani 2023年的ERA是多少？',
                    'Gerrit Cole 的三振率是多少？'
                ]
            },
            {
                'category': 'Ranking - 排名查詢',
                'queries': [
                    '2024年打擊率前5名球員',
                    'Who are the top 3 home run hitters in 2023?',
                    '最高出棒初速的打者有誰？',
                    '三振率最高的5位投手'
                ]
            }
        ],
        'llm_examples': [
            {
                'category': 'Factual - 詳細解釋',
                'queries': [
                    'Aaron Judge 2022年打了幾支全壘打？請說明他的表現',
                    'Explain Juan Soto\'s 2024 batting performance',
                    '分析 Shohei Ohtani 2023年的投球數據'
                ]
            },
            {
                'category': 'Comparison - 比較分析',
                'queries': [
                    '比較 Aaron Judge 2022 和 2023 的表現',
                    'Compare Juan Soto and Mookie Betts batting stats',
                    'Gerrit Cole vs Jacob deGrom 誰的表現更好？'
                ]
            },
            {
                'category': 'Analysis - 深度分析',
                'queries': [
                    '分析 Aaron Judge 近年來的打擊趨勢',
                    'Why is Shohei Ohtani valuable as a two-way player?',
                    '評估 Dodgers 的投手陣容強度'
                ]
            },
            {
                'category': 'Ranking - 詳細排名',
                'queries': [
                    '列出2024年打擊率前5名球員並說明原因',
                    'Who are the fastest runners in 2024? Explain.',
                    '分析2023年最佳投手的表現特點'
                ]
            }
        ]
    })


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🚀 MLB Team Manager Assistant 啟動中...")
    print("=" * 80)
    print(f"\n✅ Ollama 狀態: {'可用 (' + OLLAMA_MODEL + ')' if OLLAMA_AVAILABLE else '不可用'}")
    print(f"✅ 資料庫大小: 4,387 球員記錄")
    print("\n訪問: http://127.0.0.1:5000")
    print("\n按 Ctrl+C 停止服務器")
    print("=" * 80 + "\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')
