"""
MLB Team Manager Assistant - Flask Backend
支援純 RAG 和 RAG + LLM 兩種模式
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.retrieval.query_router import QueryRouter
from src.retrieval.hybrid_search import HybridSearch
from src.generation.prompt_templates_new import PromptTemplates

app = Flask(__name__, static_folder='static')
CORS(app)

# 初始化組件
print("\n初始化 MLB RAG 系統...")
query_router = QueryRouter()
prompt_templates = PromptTemplates()
hybrid_search = HybridSearch()
print("系統初始化完成！\n")

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
        print(f"Ollama 可用，模型: {OLLAMA_MODEL}")
    else:
        print("Ollama 未檢測到模型")
except:
    print("Ollama 不可用，僅支援純 RAG 模式")


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
    
    # 基於實際數據格式的統計映射
    # 實際數據包含：wOBA, wRC+, WAR, Exit Velocity, Launch Angle, Barrel Rate 等
    stat_mappings = {
        # wOBA (加權上壘率)
        'woba': ('wOBA|Expected wOBA', 'wOBA', 'wOBA'),
        
        # wRC+ (加權得分創造指數)
        'wrc+': ('wRC\+', 'wRC+', 'wRC+'),
        'wrc': ('wRC\+', 'wRC+', 'wRC+'),
        
        # WAR (勝場貢獻值)
        'war': ('WAR', 'WAR', 'WAR'),
        
        # 出棒初速
        'exit velocity': ('Exit Velocity', '出棒初速', 'exit velocity'),
        '出棒初速': ('Exit Velocity', '出棒初速', 'exit velocity'),
        'exit velo': ('Exit Velocity', '出棒初速', 'exit velocity'),
        
        # 仰角
        'launch angle': ('Launch Angle', '擊球仰角', 'launch angle'),
        '仰角': ('Launch Angle', '擊球仰角', 'launch angle'),
        'angle': ('Launch Angle', '擊球仰角', 'launch angle'),
        
        # 強勁擊球率
        'barrel rate': ('Barrel Rate', '強勁擊球率', 'barrel rate'),
        'barrel': ('Barrel Rate', '強勁擊球率', 'barrel rate'),
        '強勁擊球': ('Barrel Rate', '強勁擊球率', 'barrel rate'),
        
        # 強擊球率
        'hard hit': ('Hard-Hit Rate', '強擊球率', 'hard-hit rate'),
        'hard-hit rate': ('Hard-Hit Rate', '強擊球率', 'hard-hit rate'),
        '強擊球': ('Hard-Hit Rate', '強擊球率', 'hard-hit rate'),
        
        # 三振率
        'strikeout': ('Strikeout Rate|K%', '三振率', 'strikeout rate'),
        'k%': ('Strikeout Rate|K%', '三振率', 'strikeout rate'),
        '三振': ('Strikeout Rate|K%', '三振率', 'strikeout rate'),
        '三振率': ('Strikeout Rate|K%', '三振率', 'strikeout rate'),
        
        # 保送率
        'walk': ('Walk Rate|BB%', '保送率', 'walk rate'),
        'walk rate': ('Walk Rate|BB%', '保送率', 'walk rate'),
        '保送': ('Walk Rate|BB%', '保送率', 'walk rate'),
        '保送率': ('Walk Rate|BB%', '保送率', 'walk rate'),
        'bb%': ('Walk Rate|BB%', '保送率', 'walk rate'),
        
        # Expected 統計
        'expected batting average': ('Expected Batting Average', '預期打擊率', 'expected batting average'),
        'expected ba': ('Expected Batting Average', '預期打擊率', 'expected batting average'),
        'xba': ('Expected Batting Average', '預期打擊率', 'expected batting average'),
        
        'expected slugging': ('Expected Slugging', '預期長打率', 'expected slugging'),
        'expected slg': ('Expected Slugging', '預期長打率', 'expected slugging'),
        'xslg': ('Expected Slugging', '預期長打率', 'expected slugging'),
        
        # 滾地球率
        'ground ball': ('Ground Ball Rate', '滾地球率', 'ground ball rate'),
        'gb%': ('Ground Ball Rate', '滾地球率', 'ground ball rate'),
        '滾地球': ('Ground Ball Rate', '滾地球率', 'ground ball rate'),
        
        # 飛球率
        'fly ball': ('Fly Ball Rate', '飛球率', 'fly ball rate'),
        'fb%': ('Fly Ball Rate', '飛球率', 'fly ball rate'),
        '飛球': ('Fly Ball Rate', '飛球率', 'fly ball rate'),
        
        # 平飛球率
        'line drive': ('Line Drive Rate', '平飛球率', 'line drive rate'),
        'ld%': ('Line Drive Rate', '平飛球率', 'line drive rate'),
        '平飛球': ('Line Drive Rate', '平飛球率', 'line drive rate'),
        
        # 薪資
        'salary': ('Salary', '薪資', 'salary'),
        '薪資': ('Salary', '薪資', 'salary'),
        '年薪': ('Salary', '薪資', 'salary'),
        
        # 合約年數
        'contract': ('Contract Years', '合約年數', 'contract years'),
        'contract years': ('Contract Years', '合約年數', 'contract years'),
        '合約': ('Contract Years', '合約年數', 'contract years'),
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
            if stat_name_cn in ['wOBA']:
                answer = f"{player_name} 在 {season} 年的 {stat_name_cn} 為 {stat_value}"
            elif stat_name_cn in ['wRC+', 'WAR']:
                answer = f"{player_name} 在 {season} 年的 {stat_name_cn} 為 {stat_value}"
            elif stat_name_cn in ['出棒初速', '擊球仰角']:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
            elif stat_name_cn in ['強勁擊球率', '強擊球率', '三振率', '保送率', '滾地球率', '飛球率', '平飛球率']:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
            elif stat_name_cn in ['預期打擊率', '預期長打率']:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
            elif stat_name_cn in ['薪資']:
                # 格式化薪資顯示
                answer = f"{player_name} 在 {season} 年的年薪為 ${stat_value}"
            elif stat_name_cn in ['合約年數']:
                answer = f"{player_name} 的合約為 {stat_value} 年"
            else:
                answer = f"{player_name} 在 {season} 年的{stat_name_cn}為 {stat_value}"
        else:
            # 英文表達
            if stat_name_en in ['wOBA', 'wRC+', 'WAR']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en in ['exit velocity', 'launch angle']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en in ['barrel rate', 'hard-hit rate', 'strikeout rate', 'walk rate']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en in ['ground ball rate', 'fly ball rate', 'line drive rate']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en in ['expected batting average', 'expected slugging']:
                answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
            elif stat_name_en == 'salary':
                answer = f"{player_name}'s salary in {season} was ${stat_value}"
            elif stat_name_en == 'contract years':
                answer = f"{player_name}'s contract is for {stat_value} years"
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
                'answer': extracted_answer
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
                'category': 'Factual - 高級統計',
                'queries': [
                    'Aaron Judge 2022年的 wOBA 是多少？',
                    'What was Aaron Judge\'s wRC+ in 2022?',
                    'Aaron Judge 2022年的 WAR 是多少？',
                    'Aaron Judge 的出棒初速是多少？'
                ]
            },
            {
                'category': 'Factual - 擊球數據',
                'queries': [
                    'Aaron Judge 的強勁擊球率是多少？',
                    'What is Aaron Judge\'s barrel rate?',
                    'Aaron Judge 的擊球仰角是多少？',
                    'Aaron Judge 的強擊球率？'
                ]
            },
            {
                'category': 'Ranking - 排名查詢',
                'queries': [
                    '2022年 wRC+ 最高的5位球員',
                    'Who had the highest WAR in 2022?',
                    '最高出棒初速的打者有誰？',
                    '2022年最佳打者是誰？'
                ]
            }
        ],
        'llm_examples': [
            {
                'category': 'Factual - 詳細解釋',
                'queries': [
                    'Aaron Judge 2022年的 wOBA 是多少？請說明他的表現',
                    'Explain Aaron Judge\'s 2022 WAR and what it means',
                    '分析 Aaron Judge 2022年的擊球數據'
                ]
            },
            {
                'category': 'Comparison - 比較分析',
                'queries': [
                    '比較 Aaron Judge 2022 和 2023 的表現',
                    'Compare Aaron Judge and Juan Soto in 2024',
                    'Aaron Judge vs Shohei Ohtani 2023 誰更好？'
                ]
            },
            {
                'category': 'Analysis - 深度分析',
                'queries': [
                    '分析 Aaron Judge 2022年為什麼能獲得 MVP',
                    'Why is Aaron Judge\'s 2022 season so valuable?',
                    '評估 Aaron Judge 的整體打擊能力',
                    '為什麼 Aaron Judge 的 wRC+ 這麼高？'
                ]
            },
            {
                'category': 'Awards & Contract - 獎項與合約',
                'queries': [
                    'Aaron Judge 獲得過哪些獎項？',
                    'What awards has Aaron Judge won?',
                    'Aaron Judge 的年薪是多少？',
                    'Aaron Judge 的合約有幾年？'
                ]
            }
        ]
    })


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🚀 MLB Team Manager Assistant 啟動中...")
    print("=" * 80)
    print(f"\nOllama 狀態: {'可用 (' + OLLAMA_MODEL + ')' if OLLAMA_AVAILABLE else '不可用'}")
    print(f"資料庫大小: 4,387 球員記錄")
    print("\n訪問: http://127.0.0.1:5000")
    print("\n按 Ctrl+C 停止服務器")
    print("=" * 80 + "\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')
