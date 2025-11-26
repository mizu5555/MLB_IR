"""
Week 2: 完整 MLB Assistant
整合所有功能：Query 分類 → 智能路由 → LLM 生成回答

功能：
1. 自動分類 query 類型
2. 根據類型使用不同檢索策略
3. 生成自然語言回答
"""

import json
import os
import pandas as pd
import re
from typing import Dict, List
import requests

print("=" * 80)
print("MLB Team Manager Assistant")
print("=" * 80)

# ============================================
# 配置
# ============================================

DATA_DIR = "./mlb_data"
OLLAMA_MODEL = "llama3.2"
OLLAMA_BASE_URL = "http://localhost:11434"

print(f"\n配置：")
print(f"  資料目錄：{DATA_DIR}")
print(f"  LLM 模型：{OLLAMA_MODEL}")

# ============================================
# 載入所有組件
# ============================================

print(f"\n[初始化] 載入組件...")

# 載入 LanceDB
try:
    import lancedb
    from sentence_transformers import SentenceTransformer
    
    config_file = os.path.join(DATA_DIR, "search_config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    db = lancedb.connect(config['db_path'])
    table = db.open_table(config['table_name'])
    model = SentenceTransformer(config['embedding_model'])
    
    print(f"  ✅ Vector Search 系統已載入")
except Exception as e:
    print(f"  ❌ Vector Search 載入失敗：{e}")
    exit(1)

# 載入原始數據
docs_file = os.path.join(DATA_DIR, "mlb_documents.json")
with open(docs_file, 'r', encoding='utf-8') as f:
    all_documents = json.load(f)
docs_df = pd.DataFrame(all_documents)

print(f"  ✅ 資料庫已載入：{len(docs_df)} 筆記錄")

# ============================================
# LLM 接口
# ============================================

def call_llm(prompt: str, max_tokens: int = 500) -> str:
    """調用 Ollama LLM"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": max_tokens,
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['response'].strip()
        else:
            return f"LLM 錯誤：{response.status_code}"
    except Exception as e:
        return f"LLM 調用失敗：{e}"

# ============================================
# Query 分類器
# ============================================

def classify_query(query: str) -> str:
    """分類 query 類型"""
    
    query_lower = query.lower()
    
    # 規則 1：檢測 ranking 關鍵詞（英文 + 中文）
    ranking_keywords = [
        # 英文關鍵詞
        'highest', 'lowest', 'best', 'worst', 'top', 'bottom', 
        'most', 'least', 'greatest', 'smallest', 'who has',
        'which player', 'compare', 'versus', 'vs',
        # 中文關鍵詞
        '最高', '最低', '最多', '最少', '最強', '最弱', '最好', '最差',
        '排名', '排行', '前', '誰是', '哪位', '哪個', '比較'
    ]
    
    for keyword in ranking_keywords:
        if keyword in query_lower:
            return 'ranking'
    
    # 規則 2：檢測 analysis 關鍵詞（英文 + 中文）
    analysis_keywords = [
        # 英文關鍵詞
        'why', 'how', 'explain', 'analyze', 'what makes',
        'reason', 'because', 'effective', 'performance',
        # 中文關鍵詞
        '為什麼', '為何', '怎麼', '如何', '解釋', '分析',
        '原因', '表現', '有效', '壓制力'
    ]
    
    for keyword in analysis_keywords:
        if keyword in query_lower:
            return 'analysis'
    
    # 規則 3：如果沒有明確關鍵詞，使用 LLM 分類
    prompt = f"""You are a query classifier for a baseball statistics system.

Classify the following query into ONE of these types:

1. **factual**: Query asks for specific data about a specific player
2. **ranking**: Query asks for top/best/worst players or comparisons
3. **analysis**: Query asks for explanation, reasoning, or deep analysis

Query: "{query}"

CRITICAL: Respond with ONLY ONE WORD: factual, ranking, or analysis
"""
    
    response = call_llm(prompt, max_tokens=10)
    response_lower = response.lower().strip()
    
    if 'factual' in response_lower:
        return 'factual'
    elif 'ranking' in response_lower:
        return 'ranking'
    elif 'analysis' in response_lower:
        return 'analysis'
    else:
        return 'factual'  # 預設

# ============================================
# 檢索函數
# ============================================

def vector_search(query: str, k: int = 3) -> List[Dict]:
    """Vector Search"""
    query_embedding = model.encode(query).tolist()
    results = table.search(query_embedding).limit(k).to_list()
    return results

def ranking_search(query: str, top_n: int = 5) -> Dict:
    """Ranking Search with 門檻過濾"""
    
    query_lower = query.lower()
    
    # 統計項目映射
    batter_stats = {
        'wrc+': ('stat_wRC+', False),
        'wrc plus': ('stat_wRC+', False),
        'woba': ('stat_wOBA', False),
        'ops': ('stat_OPS', False),
        'home run': ('stat_HR', False),
        'hr': ('stat_HR', False),
        'avg': ('stat_AVG', False),
        'average': ('stat_AVG', False),
        'obp': ('stat_OBP', False),
        'slg': ('stat_SLG', False),
    }
    
    pitcher_stats = {
        'era': ('stat_ERA', True),
        'whip': ('stat_WHIP', True),
        'fip': ('stat_FIP', True),
        'k/9': ('stat_K_9', False),
        'strikeout': ('stat_K_9', False),
    }
    
    # 識別統計項目
    stat_col = None
    player_type = None
    ascending = True
    
    for keyword, (col, is_ascending) in batter_stats.items():
        if keyword in query_lower:
            stat_col = col
            player_type = 'batter'
            ascending = is_ascending
            break
    
    if not stat_col:
        for keyword, (col, is_ascending) in pitcher_stats.items():
            if keyword in query_lower:
                stat_col = col
                player_type = 'pitcher'
                ascending = is_ascending
                break
    
    if not stat_col:
        stat_col = 'stat_WAR'
        ascending = False
        player_type = 'batter' if 'batter' in query_lower or 'hitter' in query_lower else 'pitcher'
    
    # 過濾和排序
    filtered_df = docs_df[docs_df['type'] == player_type].copy()
    
    # 年份過濾（動態）
    year_pattern = r'\b(202[0-9])\b'
    match = re.search(year_pattern, query)
    
    if match:
        target_year = int(match.group(1))
        filtered_df = filtered_df[filtered_df['season'] == target_year]
    else:
        # 如果沒指定年份，使用最新賽季
        max_season = filtered_df['season'].max()
        filtered_df = filtered_df[filtered_df['season'] == max_season]
    
    filtered_df['sort_stat'] = filtered_df['stats'].apply(
        lambda x: x.get(stat_col.replace('stat_', ''), 0) if isinstance(x, dict) else 0
    )
    
    filtered_df = filtered_df[filtered_df['sort_stat'] > 0]
    
    # 樣本門檻
    if player_type == 'batter':
        filtered_df['pa'] = filtered_df['stats'].apply(
            lambda x: x.get('PA', 0) if isinstance(x, dict) else 0
        )
        filtered_df = filtered_df[filtered_df['pa'] >= 100]
    elif player_type == 'pitcher':
        filtered_df['ip'] = filtered_df['stats'].apply(
            lambda x: x.get('IP', 0) if isinstance(x, dict) else 0
        )
        filtered_df = filtered_df[filtered_df['ip'] >= 20]
    
    sorted_df = filtered_df.sort_values('sort_stat', ascending=ascending)
    top_players = sorted_df.head(top_n)
    
    results = []
    for idx, row in top_players.iterrows():
        results.append({
            'rank': len(results) + 1,
            'name': row['player_name'],
            'team': row['team'],
            'stat_value': row['sort_stat'],
            'stat_name': stat_col.replace('stat_', ''),
            'type': row['type']
        })
    
    return {
        'stat_name': stat_col.replace('stat_', ''),
        'player_type': player_type,
        'results': results
    }

# ============================================
# LLM 回答生成
# ============================================

def generate_factual_answer(query: str, search_results: List[Dict]) -> str:
    """生成 Factual 查詢的回答"""
    
    if not search_results:
        return "抱歉，我找不到相關的球員數據。"
    
    player = search_results[0]
    
    # 提取所有統計數據
    stats_dict = {}
    for key, value in player.items():
        if key.startswith('stat_'):
            stat_name = key.replace('stat_', '')
            stats_dict[stat_name] = value
    
    # 格式化為易讀的文字
    stats_lines = []
    for stat_name, value in stats_dict.items():
        if value > 0:
            if isinstance(value, float):
                stats_lines.append(f"  - {stat_name}: {value:.3f}")
            else:
                stats_lines.append(f"  - {stat_name}: {value}")
    
    stats_text = "\n".join(stats_lines[:15])  # 前15個統計
    
    prompt = f"""You are a baseball statistics assistant. Answer the query in a structured way.

Query: {query}

Player Information:
- Name: {player['player_name']}
- Team: {player['team']}
- Season: {player['season']}
- Position: {player['position']}
- Type: {player['type']}

Statistics:
{stats_text}

CRITICAL INSTRUCTIONS:
1. ALWAYS start with the direct answer to the question (the specific number)
2. Keep the first sentence SHORT and DIRECT
3. Then provide brief context if helpful (1-2 sentences)
4. Use the exact statistics provided above
5. Do NOT say data is unavailable

Response Structure:
[Direct Answer with Number] + [Optional Brief Context]

Examples:
Query: "What is Aaron Judge's wRC+?"
Answer: "Aaron Judge's wRC+ is 220.0 in the 2024 season. This indicates he is performing exceptionally well, creating runs at more than twice the league average rate."

Query: "How many home runs did Juan Soto hit?"
Answer: "Juan Soto hit 41 home runs in the 2024 season."

Now answer the query:"""
    
    return call_llm(prompt, max_tokens=150)

def generate_ranking_answer(query: str, ranking_results: Dict) -> str:
    """生成 Ranking 查詢的回答"""
    
    if not ranking_results['results']:
        return "抱歉，找不到符合條件的球員。"
    
    # 建立排名列表
    ranking_text = []
    for r in ranking_results['results']:
        ranking_text.append(
            f"{r['rank']}. {r['name']} ({r['team']}) - {r['stat_name']}: {r['stat_value']:.3f}"
        )
    
    ranking_str = "\n".join(ranking_text)
    
    prompt = f"""Based on the following baseball statistics ranking, provide a structured answer.

Query: {query}

Top Players by {ranking_results['stat_name']}:
{ranking_str}

CRITICAL INSTRUCTIONS:
1. ALWAYS start with a brief introduction using "根據 [stat] 數據，排名如下："
2. Then list the top 3-5 players concisely
3. THEN provide optional analysis (2-3 sentences)
4. Be OBJECTIVE - all listed players are performing excellently
5. Do NOT make negative comments about ANY player on the list
6. Use ONLY Chinese or English - NO other languages (no Thai, Japanese, etc.)
7. Keep the language natural and professional

Response Structure:
[Brief Introduction: "根據...數據，排名如下："]
[Rankings 1-5]
[Brief Analysis]

Good Example:
"根據 2024 賽季 wRC+ 數據，排名如下：
1. Aaron Judge (NYY) - 220.0
2. Juan Soto (NYY) - 181.0
3. Shohei Ohtani (LAD) - 180.0
4. Kyle Tucker (HOU) - 179.0
5. Bobby Witt Jr. (KCR) - 169.0

Aaron Judge 以 220.0 的 wRC+ 領先全聯盟，展現卓越的打擊能力。Juan Soto 和 Shohei Ohtani 也都有優異的表現，證明他們是聯盟中的頂尖打者。"

IMPORTANT: Use simple Chinese words. Avoid rare or foreign characters.

Now answer the query:"""
    
    return call_llm(prompt, max_tokens=200)

def generate_analysis_answer(query: str, player_name: str, stats_over_time: List[Dict]) -> str:
    """生成 Analysis 查詢的回答"""
    
    # 整理多賽季數據
    seasons_text = []
    for season_data in stats_over_time:
        season = season_data['season']
        stats = season_data['stats']
        
        # 選擇關鍵統計
        if season_data['type'] == 'batter':
            key_stats = f"wRC+: {stats.get('wRC+', 'N/A')}, OPS: {stats.get('OPS', 'N/A')}, HR: {stats.get('HR', 'N/A')}"
        else:
            key_stats = f"ERA: {stats.get('ERA', 'N/A')}, WHIP: {stats.get('WHIP', 'N/A')}, K/9: {stats.get('K/9', 'N/A')}"
        
        seasons_text.append(f"{season}: {key_stats}")
    
    seasons_str = "\n".join(seasons_text)
    
    prompt = f"""Based on multi-season baseball statistics, provide an analytical answer.

Query: {query}

Player: {player_name}
Performance Over Time:
{seasons_str}

CRITICAL INSTRUCTIONS:
1. ALWAYS start with a brief conclusion (1 sentence)
2. THEN provide detailed analysis with specific data (2-3 sentences)
3. Focus on trends, improvements, or patterns
4. Use the actual statistics provided
5. Be objective and data-driven

Response Structure:
[Brief Conclusion] + [Detailed Analysis with Data]

Good Example:
"Aaron Judge's exceptional performance is driven by his elite power and plate discipline. His wRC+ improved from 173 in 2023 to 220 in 2024, while his home run total jumped from 37 to 58, demonstrating significant growth in power production. Combined with his improved OPS from 1.019 to 1.159, these metrics show he has refined his approach to become one of baseball's most dominant hitters."

Now answer the query:"""
    
    return call_llm(prompt, max_tokens=250)

# ============================================
# 主要 Assistant 函數
# ============================================

def mlb_assistant(query: str) -> Dict:
    """
    MLB Assistant 主函數
    
    Returns:
        {
            'query': str,
            'query_type': str,
            'answer': str,
            'data': dict (原始數據)
        }
    """
    
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    # Step 1: 分類
    print(f"\n[1] 分類查詢類型...")
    query_type = classify_query(query)
    print(f"    類型：{query_type}")
    
    # Step 2: 檢索
    print(f"\n[2] 執行檢索...")
    
    if query_type == 'factual':
        print(f"    策略：Vector Search")
        search_results = vector_search(query, k=3)
        print(f"    ✅ 找到 {len(search_results)} 筆結果")
        
        # Step 3: 生成回答
        print(f"\n[3] 生成回答...")
        answer = generate_factual_answer(query, search_results)
        
        return {
            'query': query,
            'query_type': query_type,
            'answer': answer,
            'data': {
                'top_result': search_results[0] if search_results else None,
                'all_results': search_results
            }
        }
    
    elif query_type == 'ranking':
        print(f"    策略：資料庫排序")
        ranking_results = ranking_search(query, top_n=5)
        print(f"    ✅ 找到 Top {len(ranking_results['results'])}")
        
        # Step 3: 生成回答
        print(f"\n[3] 生成回答...")
        answer = generate_ranking_answer(query, ranking_results)
        
        return {
            'query': query,
            'query_type': query_type,
            'answer': answer,
            'data': ranking_results
        }
    
    elif query_type == 'analysis':
        print(f"    策略：多維檢索")
        # Vector search 找主要球員
        search_results = vector_search(query, k=1)
        if not search_results:
            return {
                'query': query,
                'query_type': query_type,
                'answer': '抱歉，找不到相關球員數據。',
                'data': None
            }
        
        player_name = search_results[0]['player_name']
        print(f"    主要球員：{player_name}")
        
        # 收集多賽季數據
        player_data = docs_df[docs_df['player_name'] == player_name].sort_values('season')
        stats_over_time = []
        for idx, row in player_data.iterrows():
            stats_over_time.append({
                'season': row['season'],
                'team': row['team'],
                'type': row['type'],
                'stats': row['stats']
            })
        
        print(f"    ✅ 收集到 {len(stats_over_time)} 個賽季數據")
        
        # Step 3: 生成回答
        print(f"\n[3] 生成回答...")
        answer = generate_analysis_answer(query, player_name, stats_over_time)
        
        return {
            'query': query,
            'query_type': query_type,
            'answer': answer,
            'data': {
                'player_name': player_name,
                'stats_over_time': stats_over_time
            }
        }

# ============================================
# 測試案例
# ============================================

if __name__ == "__main__":
    
    print("\n" + "=" * 80)
    print("測試 MLB Assistant")
    print("=" * 80)
    
    test_queries = [
        "Aaron Judge 2024 wRC+ 是多少？",
        "Who has the highest wRC+ in 2024?",
        "Top 5 pitchers by ERA in 2024",
        "Why is Aaron Judge so good?",
    ]
    
    results = []
    
    for query in test_queries:
        result = mlb_assistant(query)
        results.append(result)
        
        # 顯示回答
        print(f"\n{'='*80}")
        print(f"💬 回答：")
        print(f"{'='*80}")
        print(result['answer'])
        print()
    
    # 儲存結果
    output_file = os.path.join(DATA_DIR, "assistant_test_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 測試結果已儲存：{output_file}")
    
    print("\n" + "=" * 80)
    print("✨ MLB Assistant 測試完成！")
    print("=" * 80)
    print("\n🎯 下一步：執行 week2_streamlit_demo.py 建立 Web UI")
    print("=" * 80)
