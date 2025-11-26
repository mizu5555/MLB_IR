"""
Week 2: 智能路由系統
根據 Query 類型使用不同的檢索策略

路由策略：
1. Factual → Vector Search → 提取數據
2. Ranking → 資料庫排序 → Top N
3. Analysis → 多維檢索 → LLM 分析
"""

import json
import os
import pandas as pd
import re
from typing import Dict, List

print("=" * 80)
print("智能路由系統")
print("=" * 80)

# ============================================
# 載入系統組件
# ============================================

print("\n[Step 1] 載入組件...")

# 載入 LanceDB
try:
    import lancedb
    from sentence_transformers import SentenceTransformer
    print("  ✅ LanceDB 和 Embedding 模型")
except ImportError as e:
    print(f"  ❌ 缺少依賴：{e}")
    exit(1)

# 載入配置
DATA_DIR = "./mlb_data"
config_file = os.path.join(DATA_DIR, "search_config.json")

with open(config_file, 'r') as f:
    config = json.load(f)

# 連接資料庫
db = lancedb.connect(config['db_path'])
table = db.open_table(config['table_name'])
model = SentenceTransformer(config['embedding_model'])

print(f"  ✅ 資料庫已連接：{len(table)} 筆記錄")

# 載入原始數據（用於排序查詢）
docs_file = os.path.join(DATA_DIR, "mlb_documents.json")
with open(docs_file, 'r', encoding='utf-8') as f:
    all_documents = json.load(f)

docs_df = pd.DataFrame(all_documents)
print(f"  ✅ 原始數據已載入：{len(docs_df)} 筆")

# ============================================
# 路由策略 1: Factual Query
# ============================================

def handle_factual_query(query: str, k: int = 3) -> Dict:
    """
    處理事實查詢：找到特定球員 → 提取數據
    
    策略：
    1. Vector Search 找到球員
    2. 提取相關統計數據
    3. 格式化返回
    """
    
    print(f"\n  [Factual 路由]")
    print(f"  策略：Vector Search → 提取數據")
    
    # 偵測人名
    potential_names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query)
    
    # Vector Search
    query_embedding = model.encode(query).tolist()
    results = table.search(query_embedding).limit(k).to_list()
    
    if not results:
        return {
            'success': False,
            'message': '未找到相關球員',
            'results': []
        }
    
    # 提取主要球員（Top 1）
    top_player = results[0]
    
    print(f"  ✅ 找到球員：{top_player['player_name']}")
    
    # 格式化統計數據
    stats_summary = {}
    for key, value in top_player.items():
        if key.startswith('stat_'):
            stat_name = key.replace('stat_', '')
            stats_summary[stat_name] = value
    
    return {
        'success': True,
        'query_type': 'factual',
        'player': {
            'name': top_player['player_name'],
            'team': top_player['team'],
            'season': top_player['season'],
            'position': top_player['position'],
            'type': top_player['type']
        },
        'stats': stats_summary,
        'all_results': results[:k]
    }

# ============================================
# 路由策略 2: Ranking Query
# ============================================

def handle_ranking_query(query: str, top_n: int = 5) -> Dict:
    """
    處理排序查詢：根據某個統計項目排序
    
    策略：
    1. 識別統計項目（如 wRC+, ERA）
    2. 識別球員類型（打者 or 投手）
    3. 資料庫排序
    4. 返回 Top N
    """
    
    print(f"\n  [Ranking 路由]")
    print(f"  策略：資料庫排序 → Top {top_n}")
    
    # 識別統計項目
    query_lower = query.lower()
    
    # 打者統計項目
    batter_stats = {
        'wrc+': 'stat_wRC+',
        'wrc plus': 'stat_wRC+',
        'woba': 'stat_wOBA',
        'ops': 'stat_OPS',
        'home run': 'stat_HR',
        'hr': 'stat_HR',
        'avg': 'stat_AVG',
        'average': 'stat_AVG',
        'obp': 'stat_OBP',
        'slg': 'stat_SLG',
    }
    
    # 投手統計項目
    pitcher_stats = {
        'era': 'stat_ERA',
        'whip': 'stat_WHIP',
        'fip': 'stat_FIP',
        'k/9': 'stat_K_9',
        'strikeout': 'stat_K_9',
    }
    
    # 判斷統計項目和球員類型
    stat_col = None
    player_type = None
    ascending = True  # ERA, WHIP 越低越好
    
    # 檢查打者統計
    for keyword, col in batter_stats.items():
        if keyword in query_lower:
            stat_col = col
            player_type = 'batter'
            ascending = False  # wRC+, OPS 越高越好
            print(f"  偵測到打者統計：{keyword} → {col}")
            break
    
    # 檢查投手統計
    if not stat_col:
        for keyword, col in pitcher_stats.items():
            if keyword in query_lower:
                stat_col = col
                player_type = 'pitcher'
                # ERA, WHIP, FIP 越低越好
                ascending = True if keyword in ['era', 'whip', 'fip'] else False
                print(f"  偵測到投手統計：{keyword} → {col}")
                break
    
    # 如果沒有偵測到特定統計，使用通用策略
    if not stat_col:
        print(f"  ⚠️  未偵測到特定統計項目，使用 WAR 排序")
        stat_col = 'stat_WAR'
        ascending = False
        
        # 判斷是打者還是投手
        if 'pitcher' in query_lower or 'pitching' in query_lower:
            player_type = 'pitcher'
        else:
            player_type = 'batter'
    
    print(f"  球員類型：{player_type}")
    print(f"  排序欄位：{stat_col}")
    print(f"  排序方向：{'升序 (越低越好)' if ascending else '降序 (越高越好)'}")
    
    # 過濾球員類型
    if player_type:
        filtered_df = docs_df[docs_df['type'] == player_type].copy()
    else:
        filtered_df = docs_df.copy()
    
    # 年份過濾（動態）
    year_pattern = r'\b(202[0-9])\b'
    match = re.search(year_pattern, query)
    
    if match:
        target_year = int(match.group(1))
        filtered_df = filtered_df[filtered_df['season'] == target_year]
        print(f"  🎯 過濾到 {target_year} 賽季")
    else:
        # 如果沒指定年份，使用最新賽季
        max_season = filtered_df['season'].max()
        filtered_df = filtered_df[filtered_df['season'] == max_season]
        print(f"  使用最新賽季：{max_season}")
    
    print(f"  過濾後：{len(filtered_df)} 位球員")
    
    # 提取統計欄位
    filtered_df['sort_stat'] = filtered_df['stats'].apply(
        lambda x: x.get(stat_col.replace('stat_', ''), 0) if isinstance(x, dict) else 0
    )
    
    # 過濾掉 0 值（沒有數據的球員）
    filtered_df = filtered_df[filtered_df['sort_stat'] > 0]
    
    # 設定樣本數門檻（避免小樣本偏差）
    if player_type == 'batter':
        # 打者：至少 100 打席
        filtered_df['pa'] = filtered_df['stats'].apply(
            lambda x: x.get('PA', 0) if isinstance(x, dict) else 0
        )
        before_filter = len(filtered_df)
        filtered_df = filtered_df[filtered_df['pa'] >= 100]
        print(f"  打席門檻過濾 (PA >= 100)：{before_filter} → {len(filtered_df)} 位球員")
    
    elif player_type == 'pitcher':
        # 投手：至少 20 投球局數
        filtered_df['ip'] = filtered_df['stats'].apply(
            lambda x: x.get('IP', 0) if isinstance(x, dict) else 0
        )
        before_filter = len(filtered_df)
        filtered_df = filtered_df[filtered_df['ip'] >= 20]
        print(f"  投球局數門檻過濾 (IP >= 20)：{before_filter} → {len(filtered_df)} 位球員")
    
    # 排序
    sorted_df = filtered_df.sort_values('sort_stat', ascending=ascending)
    
    # 取 Top N
    top_players = sorted_df.head(top_n)
    
    print(f"  ✅ 找到 Top {len(top_players)} 位球員")
    
    # 格式化結果
    results = []
    for idx, row in top_players.iterrows():
        results.append({
            'rank': len(results) + 1,
            'name': row['player_name'],
            'team': row['team'],
            'season': row['season'],
            'stat_value': row['sort_stat'],
            'stat_name': stat_col.replace('stat_', ''),
            'type': row['type']
        })
    
    return {
        'success': True,
        'query_type': 'ranking',
        'stat_name': stat_col.replace('stat_', ''),
        'player_type': player_type,
        'top_n': top_n,
        'results': results
    }

# ============================================
# 路由策略 3: Analysis Query
# ============================================

def handle_analysis_query(query: str) -> Dict:
    """
    處理分析查詢：多維度檢索 → 需要 LLM 分析
    
    策略：
    1. Vector Search 找到相關球員
    2. 提取多個賽季/多個統計項目
    3. 標記為需要 LLM 分析
    """
    
    print(f"\n  [Analysis 路由]")
    print(f"  策略：多維檢索 → 待 LLM 分析")
    
    # Vector Search 找到相關球員
    query_embedding = model.encode(query).tolist()
    results = table.search(query_embedding).limit(5).to_list()
    
    if not results:
        return {
            'success': False,
            'message': '未找到相關球員',
            'results': []
        }
    
    # 提取主要球員
    top_player_name = results[0]['player_name']
    print(f"  ✅ 主要球員：{top_player_name}")
    
    # 收集該球員的所有賽季數據
    player_data = docs_df[docs_df['player_name'] == top_player_name].sort_values('season')
    
    print(f"  收集到 {len(player_data)} 個賽季的數據")
    
    # 提取關鍵統計
    stats_over_time = []
    for idx, row in player_data.iterrows():
        stats_over_time.append({
            'season': row['season'],
            'team': row['team'],
            'type': row['type'],
            'stats': row['stats']
        })
    
    return {
        'success': True,
        'query_type': 'analysis',
        'player_name': top_player_name,
        'stats_over_time': stats_over_time,
        'message': '數據已收集，需要 LLM 進行深度分析',
        'requires_llm': True
    }

# ============================================
# 主路由函數
# ============================================

def smart_route(query: str, query_type: str) -> Dict:
    """
    根據 query 類型路由到不同的處理函數
    """
    
    print(f"\n{'='*80}")
    print(f"查詢：'{query}'")
    print(f"類型：{query_type}")
    print(f"{'='*80}")
    
    if query_type == 'factual':
        return handle_factual_query(query)
    elif query_type == 'ranking':
        return handle_ranking_query(query)
    elif query_type == 'analysis':
        return handle_analysis_query(query)
    else:
        return {
            'success': False,
            'message': f'不支援的查詢類型：{query_type}'
        }

# ============================================
# 測試路由系統
# ============================================

print("\n" + "=" * 80)
print("測試路由系統")
print("=" * 80)

test_cases = [
    {
        'query': 'Aaron Judge 2024 wRC+',
        'type': 'factual'
    },
    {
        'query': 'Who has the highest wRC+ in 2024?',
        'type': 'ranking'
    },
    {
        'query': 'Top 5 pitchers by ERA',
        'type': 'ranking'
    },
    {
        'query': 'Why is Aaron Judge so good?',
        'type': 'analysis'
    },
]

results = []

for test in test_cases:
    result = smart_route(test['query'], test['type'])
    results.append({
        'query': test['query'],
        'type': test['type'],
        'result': result
    })
    
    # 顯示結果摘要
    if result['success']:
        if test['type'] == 'factual':
            print(f"\n  📊 結果：{result['player']['name']} ({result['player']['team']})")
            print(f"  關鍵統計：")
            for stat, value in list(result['stats'].items())[:5]:
                print(f"    {stat}: {value}")
        
        elif test['type'] == 'ranking':
            print(f"\n  🏆 Top {len(result['results'])}:")
            for r in result['results']:
                print(f"    {r['rank']}. {r['name']} ({r['team']}) - {r['stat_name']}: {r['stat_value']:.3f}")
        
        elif test['type'] == 'analysis':
            print(f"\n  🔍 分析對象：{result['player_name']}")
            print(f"  數據範圍：{len(result['stats_over_time'])} 個賽季")
    else:
        print(f"\n  ❌ {result['message']}")
    
    print()

# ============================================
# 儲存路由測試結果
# ============================================

output_file = os.path.join(DATA_DIR, "routing_test_results.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"💾 結果已儲存：{output_file}")

# ============================================
# 結論
# ============================================

print("\n" + "=" * 80)
print("路由測試完成")
print("=" * 80)

successful = sum(1 for r in results if r['result']['success'])
print(f"✅ 成功處理：{successful}/{len(results)}")

print("\n📊 路由策略效果：")
print(f"  Factual：Vector Search ✅")
print(f"  Ranking：資料庫排序 ✅")
print(f"  Analysis：多維檢索 ✅")

print("\n🎯 下一步：")
print("  執行 week2_mlb_assistant.py 整合完整系統")
print("  包含 LLM 生成自然語言回答")
print("=" * 80)
