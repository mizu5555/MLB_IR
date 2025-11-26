"""
Week 2: Streamlit Demo UI
可互動的 Web 界面展示 MLB Assistant

執行方式：
streamlit run week2_streamlit_demo.py
"""

import streamlit as st
import json
import os
import pandas as pd
import re
from typing import Dict, List
import requests

# ============================================
# 頁面配置
# ============================================

st.set_page_config(
    page_title="MLB Team Manager Assistant",
    page_icon="⚾",
    layout="wide"
)

st.title("⚾ MLB Team Manager Assistant")
st.markdown("---")

# ============================================
# 配置
# ============================================

DATA_DIR = "./mlb_data"
OLLAMA_MODEL = "llama3.2"
OLLAMA_BASE_URL = "http://localhost:11434"

# ============================================
# 輔助函數
# ============================================

def extract_year_from_query(query: str) -> int:
    """從查詢中提取年份"""
    
    # 尋找 4 位數年份（2020-2029）
    year_pattern = r'\b(202[0-9])\b'
    match = re.search(year_pattern, query)
    
    if match:
        return int(match.group(1))
    
    return None

# ============================================
# 初始化（使用 session_state 避免重複載入）
# ============================================

@st.cache_resource
def load_system():
    """載入所有系統組件（只執行一次）"""
    
    try:
        import lancedb
        from sentence_transformers import SentenceTransformer
        
        config_file = os.path.join(DATA_DIR, "search_config.json")
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        db = lancedb.connect(config['db_path'])
        table = db.open_table(config['table_name'])
        model = SentenceTransformer(config['embedding_model'])
        
        # 載入原始數據（Week 4 更新）
        # 優先使用新的數據文件，如果不存在則使用舊的
        docs_file_new = os.path.join(DATA_DIR, "mlb_players_2022_2025.json")
        docs_file_old = os.path.join(DATA_DIR, "mlb_documents.json")
        
        if os.path.exists(docs_file_new):
            docs_file = docs_file_new
            st.info("📊 使用擴充數據（2022-2025）")
        else:
            docs_file = docs_file_old
            st.warning("⚠️ 使用舊數據（2023-2024），建議執行 Week 4 數據收集")
        
        with open(docs_file, 'r', encoding='utf-8') as f:
            all_documents = json.load(f)
        docs_df = pd.DataFrame(all_documents)
        
        return {
            'table': table,
            'model': model,
            'docs_df': docs_df,
            'status': 'success'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

# 載入系統
system = load_system()

if system['status'] == 'error':
    st.error(f"❌ 系統初始化失敗：{system['error']}")
    st.stop()

table = system['table']
model = system['model']
docs_df = system['docs_df']

st.success(f"✅ 系統已載入：{len(docs_df)} 筆球員記錄")

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
    
    # 規則 3：預設為 factual
    return 'factual'

# ============================================
# 檢索函數（簡化版）
# ============================================

def vector_search(query: str, k: int = 3) -> List[Dict]:
    """Vector Search"""
    query_embedding = model.encode(query).tolist()
    results = table.search(query_embedding).limit(k).to_list()
    return results

def ranking_search(query: str, top_n: int = 5) -> Dict:
    """Ranking Search"""
    
    query_lower = query.lower()
    
    # 統計項目映射
    batter_stats = {
        'wrc+': ('stat_wRC+', False),
        'wrc plus': ('stat_wRC+', False),
        'woba': ('stat_wOBA', False),
        'ops': ('stat_OPS', False),
        'home run': ('stat_HR', False),
        'hr': ('stat_HR', False),
    }
    
    pitcher_stats = {
        'era': ('stat_ERA', True),
        'whip': ('stat_WHIP', True),
        'fip': ('stat_FIP', True),
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
        player_type = 'batter'
    
    # 過濾和排序
    filtered_df = docs_df[docs_df['type'] == player_type].copy()
    
    # 年份過濾（動態）
    target_year = extract_year_from_query(query)
    if target_year:
        filtered_df = filtered_df[filtered_df['season'] == target_year]
    else:
        # 如果沒指定年份，使用最新賽季
        max_season = filtered_df['season'].max()
        filtered_df = filtered_df[filtered_df['season'] == max_season]
    
    filtered_df['sort_stat'] = filtered_df['stats'].apply(
        lambda x: x.get(stat_col.replace('stat_', ''), 0) if isinstance(x, dict) else 0
    )
    
    filtered_df = filtered_df[filtered_df['sort_stat'] > 0]
    
    # 門檻過濾
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
        })
    
    return {
        'stat_name': stat_col.replace('stat_', ''),
        'player_type': player_type,
        'results': results
    }

# ============================================
# LLM 回答生成（簡化版）
# ============================================

def generate_answer(query: str, query_type: str, data: Dict) -> str:
    """生成回答"""
    
    if query_type == 'factual':
        player = data['top_result']
        
        # 收集統計數據
        stats_lines = []
        for key, value in player.items():
            if key.startswith('stat_') and value > 0:
                stat_name = key.replace('stat_', '')
                if isinstance(value, float):
                    stats_lines.append(f"  - {stat_name}: {value:.3f}")
                else:
                    stats_lines.append(f"  - {stat_name}: {value}")
        
        stats_text = "\n".join(stats_lines[:20])  # 增加到 20 個統計
        
        # 檢查是否是一般統計查詢
        is_general_stats_query = 'stats' in query.lower() or 'statistics' in query.lower()
        
        if is_general_stats_query:
            # 查詢 "Aaron Judge 2022 stats" - 顯示多個關鍵統計
            prompt = f"""Provide a comprehensive summary of the player's season performance.

Query: {query}

Player: {player['player_name']} ({player['team']}, {player['season']})
Statistics:
{stats_text}

CRITICAL INSTRUCTIONS:
1. Provide a 1-sentence overview of the season
2. Then list 5-8 KEY statistics with their values
3. Focus on the most important stats for this player type
4. Use exact statistics provided

For batters, prioritize: HR, AVG, OPS, wRC_plus, RBI, R, SB, BB
For pitchers, prioritize: ERA, WHIP, W-L, SO, K_9, FIP, SV

Response Structure:
[1-sentence overview]

Key Stats:
HR: [value]
AVG: [value]
OPS: [value]
...

Answer:"""
        else:
            # 查詢特定數據 - 保持簡潔
            prompt = f"""Answer the query in a structured way.

Query: {query}

Player: {player['player_name']} ({player['team']}, {player['season']})
Statistics:
{stats_text}

CRITICAL INSTRUCTIONS:
1. Start with the direct answer (the specific number)
2. Keep the first sentence SHORT and DIRECT
3. Then provide brief context if helpful (1 sentence)
4. Use exact statistics provided

Response Structure:
[Direct Answer with Number] + [Optional Brief Context]

Answer directly:"""
        
        return call_llm(prompt, max_tokens=200)
    
    elif query_type == 'ranking':
        ranking_text = []
        for r in data['results']:
            ranking_text.append(f"{r['rank']}. {r['name']} ({r['team']}) - {r['stat_value']:.3f}")
        
        ranking_str = "\n".join(ranking_text)
        
        prompt = f"""Provide a structured answer for this ranking query.

Query: {query}

Top Players:
{ranking_str}

CRITICAL INSTRUCTIONS:
1. Start with brief introduction: "根據 [stat] 數據，排名如下："
2. List the top 3-5 players concisely
3. Then provide optional analysis (2 sentences)
4. Be OBJECTIVE - all listed players are excellent
5. Do NOT make negative comments
6. Use ONLY Chinese or English - NO other languages
7. Use simple words, avoid rare characters

Response Structure:
[Rankings] + [Optional Analysis]

Answer:"""
        
        return call_llm(prompt, max_tokens=200)
    
    elif query_type == 'analysis':
        # 檢查是否有球員數據
        if not data or not data.get('player_name'):
            return "抱歉，找不到相關球員數據進行分析。"
        
        player_name = data['player_name']
        stats_over_time = data['stats_over_time']
        
        # 整理多賽季數據
        seasons_text = []
        for season_data in stats_over_time:
            season = season_data['season']
            stats = season_data['stats']
            player_type = season_data['type']
            
            # 根據球員類型選擇關鍵統計
            if player_type == 'batter':
                key_stats = f"wRC+: {stats.get('wRC+', 'N/A')}, OPS: {stats.get('OPS', 'N/A')}, HR: {stats.get('HR', 'N/A')}"
            else:
                key_stats = f"ERA: {stats.get('ERA', 'N/A')}, WHIP: {stats.get('WHIP', 'N/A')}, K/9: {stats.get('K/9', 'N/A')}"
            
            seasons_text.append(f"{season}: {key_stats}")
        
        seasons_str = "\n".join(seasons_text)
        
        prompt = f"""Provide an analytical answer.

Query: {query}

Player: {player_name}
Performance Over Time:
{seasons_str}

CRITICAL INSTRUCTIONS:
1. Start with a brief conclusion (1 sentence)
2. Then provide detailed analysis with data (2-3 sentences)
3. Focus on trends and improvements
4. Be data-driven

Response Structure:
[Conclusion] + [Detailed Analysis]

Answer:"""
        
        return call_llm(prompt, max_tokens=250)
    
    return "無法生成回答。"

# ============================================
# 主要 UI
# ============================================

st.markdown("### 🔍 查詢輸入")

# 範例查詢
st.markdown("**範例查詢：**")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Factual: Aaron Judge wRC+"):
        st.session_state.query = "Aaron Judge 2024 wRC+ 是多少？"

with col2:
    if st.button("🏆 Ranking: 最高 wRC+"):
        st.session_state.query = "Who has the highest wRC+ in 2024?"

with col3:
    if st.button("📈 Analysis: 為何強？"):
        st.session_state.query = "Why is Aaron Judge so good?"

# 查詢輸入框
query = st.text_input(
    "輸入你的查詢：",
    value=st.session_state.get('query', ''),
    placeholder="例如：Who has the highest wRC+ in 2024?"
)

if st.button("🚀 查詢", type="primary"):
    
    if not query:
        st.warning("請輸入查詢！")
        st.stop()
    
    with st.spinner("正在處理查詢..."):
        
        # Step 1: 分類
        query_type = classify_query(query)
        
        # Step 2: 檢索
        if query_type == 'factual':
            search_results = vector_search(query, k=10)  # 增加搜尋結果
            
            # 從查詢中提取年份
            target_year = extract_year_from_query(query)
            
            # 如果有指定年份，過濾結果
            if target_year:
                filtered_results = [r for r in search_results if r.get('season') == target_year]
                
                # 如果過濾後有結果，使用過濾結果
                if filtered_results:
                    search_results = filtered_results
                    st.info(f"🎯 已過濾到 {target_year} 賽季")
            
            data = {
                'top_result': search_results[0] if search_results else None,
                'all_results': search_results
            }
        elif query_type == 'ranking':
            data = ranking_search(query, top_n=5)
        else:  # analysis
            # Vector search 找主要球員
            search_results = vector_search(query, k=1)
            
            if search_results:
                player_name = search_results[0]['player_name']
                
                # 收集該球員的所有賽季數據
                player_data = docs_df[docs_df['player_name'] == player_name].sort_values('season')
                stats_over_time = []
                
                for idx, row in player_data.iterrows():
                    stats_over_time.append({
                        'season': row['season'],
                        'team': row['team'],
                        'type': row['type'],
                        'stats': row['stats']
                    })
                
                data = {
                    'player_name': player_name,
                    'stats_over_time': stats_over_time
                }
            else:
                data = None
        
        # Step 3: 生成回答
        answer = generate_answer(query, query_type, data)
    
    # 顯示結果
    st.markdown("---")
    st.markdown("### 📋 結果")
    
    # 查詢類型
    type_emoji = {
        'factual': '📊',
        'ranking': '🏆',
        'analysis': '📈'
    }
    
    st.info(f"{type_emoji.get(query_type, '❓')} **查詢類型：** {query_type.upper()}")
    
    # 回答
    st.markdown("### 💬 回答")
    st.success(answer)
    
    # 原始數據（可展開）
    with st.expander("🔍 查看原始數據"):
        if query_type == 'factual' and data.get('top_result'):
            player = data['top_result']
            st.markdown(f"**球員：** {player['player_name']}")
            st.markdown(f"**球隊：** {player['team']}")
            st.markdown(f"**賽季：** {player['season']}")
            
            # 統計表格
            stats_data = []
            for key, value in player.items():
                if key.startswith('stat_') and value > 0:
                    stats_data.append({
                        '統計項目': key.replace('stat_', ''),
                        '數值': f"{value:.3f}" if isinstance(value, float) else str(value)
                    })
            
            if stats_data:
                st.dataframe(stats_data, use_container_width=True)
        
        elif query_type == 'ranking':
            ranking_df = pd.DataFrame(data['results'])
            st.dataframe(ranking_df, use_container_width=True)
        
        elif query_type == 'analysis' and data:
            st.markdown(f"**球員：** {data.get('player_name', 'N/A')}")
            st.markdown(f"**賽季數量：** {len(data.get('stats_over_time', []))}")
            
            # 顯示各賽季統計
            for season_data in data.get('stats_over_time', []):
                st.markdown(f"**{season_data['season']} 賽季** ({season_data['team']})")
                
                stats_list = []
                stats = season_data['stats']
                
                # 根據球員類型顯示關鍵統計
                if season_data['type'] == 'batter':
                    key_stats = ['wRC+', 'OPS', 'HR', 'AVG', 'OBP', 'SLG']
                else:
                    key_stats = ['ERA', 'WHIP', 'FIP', 'K/9', 'BB/9', 'W', 'L']
                
                for stat in key_stats:
                    if stat in stats:
                        value = stats[stat]
                        if isinstance(value, float):
                            stats_list.append(f"{stat}: {value:.3f}")
                        else:
                            stats_list.append(f"{stat}: {value}")
                
                st.markdown(" | ".join(stats_list))
                st.markdown("---")

# ============================================
# 側邊欄：系統資訊
# ============================================

# 計算實際賽季範圍
min_season = int(docs_df['season'].min())
max_season = int(docs_df['season'].max())

st.sidebar.markdown("## 📊 系統資訊")
st.sidebar.markdown(f"**資料庫：** {len(docs_df)} 筆記錄")
st.sidebar.markdown(f"**賽季：** {min_season}-{max_season}")
st.sidebar.markdown(f"**LLM：** {OLLAMA_MODEL}")

st.sidebar.markdown("---")
st.sidebar.markdown("## 🎯 查詢類型")
st.sidebar.markdown("""
- **Factual** 📊：詢問特定球員的數據
- **Ranking** 🏆：要求排序或比較
- **Analysis** 📈：深度分析或解釋
""")

st.sidebar.markdown("---")
st.sidebar.markdown("## 📝 範例查詢")
st.sidebar.markdown("""
**Factual:**
- Aaron Judge 2024 wRC+
- What is Shohei Ohtani's ERA?

**Ranking:**
- Who has the highest wRC+ in 2024?
- Top 5 pitchers by ERA

**Analysis:**
- Why is Aaron Judge so good?
- Explain his performance
""")
