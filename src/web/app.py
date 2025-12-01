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
from src.generation.prompt_templates import PromptTemplates

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
    
    query_lower = query.lower()
    query_type = classification['query_type']
    language = classification['language']
    
    matched_names = set()
    for result in search_results[:5]:
        # player_id 格式為 "Name_Year"
        player_full_name = result['player_id'].split('_')[0]
        name_parts = player_full_name.lower().split()
        if any(part in query_lower for part in name_parts if len(part) > 1):
            matched_names.add(player_full_name)
    
    # 如果找到了 2 個以上的不同球員
    if len(matched_names) > 1:
        # 轉換成列表以便顯示
        names_list = list(matched_names)
        names_str = "、".join(names_list[:3]) # 最多列出 3 個例子
        if len(names_list) > 3:
            names_str += "..."
            
        if language == 'zh':
            return f"找到多位與「{query}」相關的選手（如：{names_str}）。請輸入完整姓名以精確搜尋。"
        else:
            return f"Multiple players found matching '{query}' (e.g., {names_str}). Please enter the full name for a precise search."
    
    target_result = search_results[0]
    
    # 嘗試尋找與 query 更匹配的球員 (如果您上一輪有加上這段，請保留)
    for result in search_results:
        player_id_name = result['player_id'].split('_')[0].lower()
        name_parts = player_id_name.split()
        if any(part in query_lower for part in name_parts if len(part) > 1):
            target_result = result
            break
            
    player_id = target_result['player_id']
    full_text = target_result['full_text']
    
    # 提取球員名和賽季
    import re
    player_match = re.search(r'Player: ([^.]+)\.', full_text)
    season_match = re.search(r'Season: (\d+)', full_text)
    
    player_name = player_match.group(1) if player_match else player_id.split('_')[0]
    season = season_match.group(1) if season_match else 'Unknown'
    
    # 基於實際數據格式的統計映射
    # 實際數據包含：wOBA, wRC+, WAR, Exit Velocity, Launch Angle, Barrel Rate 等
    stat_mappings = {
        # --- 基礎數據 ---
        'average': ('AVG', '打擊率', 'Batting Average'),
        '打擊率': ('AVG', '打擊率', 'Batting Average'),
        'home run': ('HR', '全壘打', 'Home Runs'),
        '全壘打': ('HR', '全壘打', 'Home Runs'),
        'rbi': ('RBI', '打點', 'RBI'),
        '打點': ('RBI', '打點', 'RBI'),
        
        # --- 進階數據 ---
        'woba': ('wOBA', 'wOBA', 'wOBA'),
        'xwoba': ('xwOBA', 'xwOBA', 'xwOBA'),
        # 注意：wRC+ 的 + 符號需要轉義
        'wrc+': ('wRC\+', 'wRC+', 'wRC+'),
        'wrc': ('wRC\+', 'wRC+', 'wRC+'),
        'war': ('WAR', 'WAR', 'WAR'),
        'ops': ('OPS', 'OPS', 'OPS'),
        
        # --- Statcast ---
        'exit velocity': ('EV', '出棒速度', 'Exit Velocity'),
        '出棒速度': ('EV', '出棒速度', 'Exit Velocity'),
        'launch angle': ('LA', '擊球仰角', 'Launch Angle'),
        '仰角': ('LA', '擊球仰角', 'Launch Angle'),
        'barrel': ('Barrel%', '強勁擊球率', 'Barrel Rate'),
        'hard hit': ('HardHit%', '強擊球率', 'Hard Hit Rate'),
        
        # --- 投手/其他 ---
        'strikeout': ('K%', '三振率', 'Strikeout Rate'),
        '三振': ('K%', '三振率', 'Strikeout Rate'),
        'walk': ('BB%', '保送率', 'Walk Rate'),
        '保送': ('BB%', '保送率', 'Walk Rate'),
        'speed': ('Spd', '跑壘速度', 'Sprint Speed'),
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
                f'({pattern})[:\s]+([0-9]+\.?[0-9]*)',     
                f'({pattern})\s*=\s*([0-9]+\.?[0-9]*)',
            ]
            
            for p in patterns:
                match = re.search(p, full_text, re.IGNORECASE)
                if match:
                    found_stat = match.group(1)
                    stat_value = match.group(2)
                    stat_name_cn = name_cn
                    stat_name_en = name_en
                    break
            
            if stat_value:
                break
    
    # 生成簡潔答案
    if stat_value:
        if language == 'zh':
            answer = f"{player_name} 在 {season} 年的 {stat_name_cn} 為 {stat_value}"
        else:
            answer = f"{player_name}'s {stat_name_en} in {season} was {stat_value}"
    else:
        # 沒找到特定統計
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
    mode = data.get('mode', 'rag')
    history = data.get('history', [])
    
    if not user_query:
        return jsonify({'error': '查詢不能為空'}), 400
    
    try:
        # 1. 查詢分類
        classification = query_router.classify_query(user_query)
        
        # 2. 檢索
        retrieval_params = query_router.get_retrieval_params(classification)
        k = retrieval_params['k']
        # 如果是對話的簡短回應（如人名），可能需要更多結果以防漏掉
        if len(user_query.split()) < 3: 
            k = max(k, 8)
            
        search_results = hybrid_search.auto_search(user_query, k=k)
        
        formatted_results = []
        for i, result in enumerate(search_results[:5], 1):
            formatted_results.append({
                'rank': i,
                'player_id': result['player_id'],
                'score': round(result['score'], 4),
                'preview': result['text_preview'][:200],
                'full_text': result['full_text']
            })
        
        # 3. 生成回答
        if mode == 'llm' and OLLAMA_AVAILABLE:
            # 將 history 傳入
            prompt = prompt_templates.get_prompt(
                query_type=classification['query_type'],
                query=user_query,
                search_results=search_results,
                language=classification['language'],
                history=history 
            )
            
            try:
                import ollama
                response = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                answer = response['message']['content']
                
                return jsonify({
                    'mode': 'llm',
                    'classification': {
                        'type': classification['query_type'],
                        'language': classification['language']
                    },
                    'search_results': formatted_results,
                    'answer': answer,
                    'model': OLLAMA_MODEL
                })
            
            except Exception as e:
                # 降級處理
                print(f"LLM Error: {e}")
                extracted_answer = extract_answer_from_results(user_query, search_results, classification)
                return jsonify({
                    'mode': 'rag',
                    'search_results': formatted_results,
                    'answer': extracted_answer,
                    'error': f'LLM 調用失敗: {str(e)}'
                })
        
        else:
            # 純 RAG 模式
            extracted_answer = extract_answer_from_results(user_query, search_results, classification)
            
            return jsonify({
                'mode': 'rag',
                'classification': {
                    'type': classification['query_type'],
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
