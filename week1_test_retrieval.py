"""
Week 1: 檢索系統完整測試
驗證 Hybrid Search 是否解決了人名檢索問題

測試重點：
1. 人名精確匹配（Aaron Judge 不會變成 Albert Suarez）
2. 語意理解（「最強打者」能找到高 wRC+ 的球員）
3. 混合查詢（「Aaron Judge wRC+」能正確檢索）
4. Recall@k 和 MRR 計算
"""

import json
import os
from typing import List, Dict, Tuple
import re

print("=" * 80)
print("Hybrid Search 檢索測試")
print("=" * 80)

# ============================================
# 載入系統
# ============================================
print("\n[Step 1] 載入 Hybrid Search 系統...")

try:
    import lancedb
    from sentence_transformers import SentenceTransformer
    import pandas as pd
except ImportError as e:
    print(f"❌ 缺少依賴：{e}")
    print("請先執行 week1_build_hybrid_search.py")
    exit(1)

# 載入配置
DATA_DIR = "./mlb_data"
config_file = os.path.join(DATA_DIR, "search_config.json")

if not os.path.exists(config_file):
    print(f"❌ 找不到配置檔：{config_file}")
    print("請先執行 week1_build_hybrid_search.py")
    exit(1)

with open(config_file, 'r') as f:
    config = json.load(f)

print(f"✅ 配置已載入")
print(f"   資料庫：{config['db_path']}")
print(f"   模型：{config['embedding_model']}")

# 連接資料庫
db = lancedb.connect(config['db_path'])
table = db.open_table(config['table_name'])
print(f"✅ 資料庫已連接：{len(table)} 筆記錄")

# 載入模型
model = SentenceTransformer(config['embedding_model'])
print(f"✅ Embedding 模型已載入")

# ============================================
# 定義檢索函數
# ============================================

def vector_only_search(query: str, k: int = 5) -> List[Dict]:
    """純 Vector Search（舊版方法）"""
    query_embedding = model.encode(query).tolist()
    results = table.search(query_embedding).limit(k).to_list()
    return results

def fts_only_search(query: str, k: int = 5) -> List[Dict]:
    """純 FTS（關鍵字匹配）"""
    try:
        results = table.search(query, query_type="fts").limit(k).to_list()
        return results
    except Exception as e:
        print(f"  FTS 錯誤：{e}")
        return []

def hybrid_search(query: str, k: int = 5) -> List[Dict]:
    """Hybrid Search（新版方法）"""
    
    # 檢測人名
    potential_names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query)
    has_person_name = len(potential_names) > 0
    
    if has_person_name:
        # 有人名：FTS 優先
        try:
            fts_query = potential_names[0]
            fts_results = table.search(fts_query, query_type="fts").limit(k * 2).to_list()
            
            if len(fts_results) >= k:
                return fts_results[:k]
            
            # 不足則補充 Vector
            query_embedding = model.encode(query).tolist()
            vector_results = table.search(query_embedding).limit(k * 2).to_list()
            
            seen_ids = {r['doc_id'] for r in fts_results}
            combined = fts_results + [r for r in vector_results if r['doc_id'] not in seen_ids]
            
            return combined[:k]
        except:
            # FTS 失敗，降級到 Vector
            pass
    
    # 無人名：純 Vector
    query_embedding = model.encode(query).tolist()
    results = table.search(query_embedding).limit(k).to_list()
    return results

# ============================================
# 測試案例
# ============================================

test_cases = [
    {
        'id': 1,
        'query': 'Aaron Judge',
        'expected_player': 'Aaron Judge',
        'description': '純人名查詢',
        'category': 'person_name'
    },
    {
        'id': 2,
        'query': 'Aaron Judge 2024 wRC+',
        'expected_player': 'Aaron Judge',
        'description': '人名 + 統計項目',
        'category': 'person_name_with_stat'
    },
    {
        'id': 3,
        'query': 'Aaron Judge home runs',
        'expected_player': 'Aaron Judge',
        'description': '人名 + 統計描述',
        'category': 'person_name_with_stat'
    },
    {
        'id': 4,
        'query': 'Shohei Ohtani',
        'expected_player': 'Shohei Ohtani',
        'description': '純人名查詢（另一球員）',
        'category': 'person_name'
    },
    {
        'id': 5,
        'query': 'Shohei Ohtani batting stats',
        'expected_player': 'Shohei Ohtani',
        'description': '人名 + 統計描述',
        'category': 'person_name_with_stat'
    },
    {
        'id': 6,
        'query': 'highest wRC+ batter 2024',
        'expected_player': None,  # 不確定，看實際數據
        'description': '語意查詢（無人名）',
        'category': 'semantic'
    },
    {
        'id': 7,
        'query': 'best pitcher ERA',
        'expected_player': None,
        'description': '語意查詢（投手）',
        'category': 'semantic'
    },
    {
        'id': 8,
        'query': 'Juan Soto 2024',
        'expected_player': 'Juan Soto',
        'description': '人名 + 年份',
        'category': 'person_name'
    },
    {
        'id': 9,
        'query': 'Freddie Freeman',
        'expected_player': 'Freddie Freeman',
        'description': '純人名查詢',
        'category': 'person_name'
    },
    {
        'id': 10,
        'query': 'Clayton Kershaw pitching stats',
        'expected_player': 'Clayton Kershaw',
        'description': '人名 + 統計描述（投手）',
        'category': 'person_name_with_stat'
    },
]

# ============================================
# 評估函數
# ============================================

def evaluate_result(query: str, results: List[Dict], expected_player: str, k: int = 5) -> Dict:
    """
    評估檢索結果
    
    返回：
    - found: 是否在 Top-k 中找到期望的球員
    - rank: 排名（1-based，未找到則為 -1）
    - top_player: Top-1 球員名稱
    """
    if not results:
        return {
            'found': False,
            'rank': -1,
            'top_player': None,
            'reciprocal_rank': 0.0
        }
    
    top_player = results[0]['player_name']
    
    # 如果沒有指定期望球員，無法評估準確性
    if expected_player is None:
        return {
            'found': None,  # 無法判斷
            'rank': None,
            'top_player': top_player,
            'reciprocal_rank': None
        }
    
    # 尋找期望球員的排名
    for i, result in enumerate(results):
        if expected_player.lower() in result['player_name'].lower():
            rank = i + 1
            return {
                'found': True,
                'rank': rank,
                'top_player': top_player,
                'reciprocal_rank': 1.0 / rank  # MRR 計算
            }
    
    return {
        'found': False,
        'rank': -1,
        'top_player': top_player,
        'reciprocal_rank': 0.0
    }

# ============================================
# 執行測試
# ============================================

print("\n" + "=" * 80)
print("開始測試")
print("=" * 80)

k = 5  # Top-5 檢索

results_summary = {
    'vector_only': [],
    'fts_only': [],
    'hybrid': []
}

for test_case in test_cases:
    print(f"\n[測試 {test_case['id']}] {test_case['description']}")
    print(f"Query: '{test_case['query']}'")
    if test_case['expected_player']:
        print(f"期望球員: {test_case['expected_player']}")
    print()
    
    # 1. Vector Only
    print(f"  [1] Vector Only Search:")
    vector_results = vector_only_search(test_case['query'], k=k)
    vector_eval = evaluate_result(test_case['query'], vector_results, test_case['expected_player'], k=k)
    
    if vector_results:
        print(f"      Top-3: {', '.join([r['player_name'] for r in vector_results[:3]])}")
        if test_case['expected_player']:
            if vector_eval['found']:
                print(f"      ✅ 找到 {test_case['expected_player']} (排名 #{vector_eval['rank']})")
            else:
                print(f"      ❌ 未找到 {test_case['expected_player']}")
    
    results_summary['vector_only'].append({
        'test_id': test_case['id'],
        'query': test_case['query'],
        **vector_eval
    })
    
    # 2. FTS Only
    print(f"  [2] FTS Only Search:")
    fts_results = fts_only_search(test_case['query'], k=k)
    fts_eval = evaluate_result(test_case['query'], fts_results, test_case['expected_player'], k=k)
    
    if fts_results:
        print(f"      Top-3: {', '.join([r['player_name'] for r in fts_results[:3]])}")
        if test_case['expected_player']:
            if fts_eval['found']:
                print(f"      ✅ 找到 {test_case['expected_player']} (排名 #{fts_eval['rank']})")
            else:
                print(f"      ❌ 未找到 {test_case['expected_player']}")
    else:
        print(f"      (無結果)")
    
    results_summary['fts_only'].append({
        'test_id': test_case['id'],
        'query': test_case['query'],
        **fts_eval
    })
    
    # 3. Hybrid Search
    print(f"  [3] Hybrid Search:")
    hybrid_results = hybrid_search(test_case['query'], k=k)
    hybrid_eval = evaluate_result(test_case['query'], hybrid_results, test_case['expected_player'], k=k)
    
    if hybrid_results:
        print(f"      Top-3: {', '.join([r['player_name'] for r in hybrid_results[:3]])}")
        if test_case['expected_player']:
            if hybrid_eval['found']:
                print(f"      ✅ 找到 {test_case['expected_player']} (排名 #{hybrid_eval['rank']})")
            else:
                print(f"      ❌ 未找到 {test_case['expected_player']}")
    
    results_summary['hybrid'].append({
        'test_id': test_case['id'],
        'query': test_case['query'],
        **hybrid_eval
    })

# ============================================
# 計算整體指標
# ============================================

print("\n" + "=" * 80)
print("評估結果")
print("=" * 80)

def calculate_metrics(results: List[Dict], method_name: str):
    """計算 Recall@k 和 MRR"""
    
    # 只計算有 expected_player 的測試案例
    valid_results = [r for r in results if r['found'] is not None]
    
    if not valid_results:
        print(f"\n{method_name}: 無法評估（沒有有效測試案例）")
        return
    
    # Recall@k：Top-k 中找到的比例
    found_count = sum(1 for r in valid_results if r['found'])
    recall_at_k = found_count / len(valid_results)
    
    # MRR (Mean Reciprocal Rank)
    rr_sum = sum(r['reciprocal_rank'] for r in valid_results)
    mrr = rr_sum / len(valid_results)
    
    print(f"\n【{method_name}】")
    print(f"  Recall@{k}: {recall_at_k:.2%} ({found_count}/{len(valid_results)})")
    print(f"  MRR: {mrr:.3f}")
    
    # 顯示失敗案例
    failed = [r for r in valid_results if not r['found']]
    if failed:
        print(f"  失敗案例：")
        for r in failed:
            print(f"    - 測試 {r['test_id']}: '{r['query']}' → Top-1: {r['top_player']}")
    
    return {
        'method': method_name,
        'recall_at_k': recall_at_k,
        'mrr': mrr,
        'found_count': found_count,
        'total_count': len(valid_results),
        'failed_cases': failed
    }

metrics = {}
metrics['vector_only'] = calculate_metrics(results_summary['vector_only'], "Vector Only")
metrics['fts_only'] = calculate_metrics(results_summary['fts_only'], "FTS Only")
metrics['hybrid'] = calculate_metrics(results_summary['hybrid'], "Hybrid Search")

# ============================================
# 對比分析
# ============================================

print("\n" + "=" * 80)
print("對比分析")
print("=" * 80)

print("\n✨ Hybrid Search vs Vector Only:")
if metrics['hybrid'] and metrics['vector_only']:
    recall_improvement = (metrics['hybrid']['recall_at_k'] - metrics['vector_only']['recall_at_k']) * 100
    mrr_improvement = (metrics['hybrid']['mrr'] - metrics['vector_only']['mrr']) * 100
    
    print(f"  Recall@{k} 提升: {recall_improvement:+.1f}%")
    print(f"  MRR 提升: {mrr_improvement:+.1f}%")
    
    if recall_improvement > 0:
        print(f"  ✅ Hybrid Search 在準確率上優於 Vector Only")
    elif recall_improvement == 0:
        print(f"  ➡️  Hybrid Search 與 Vector Only 準確率相同")
    else:
        print(f"  ⚠️  Hybrid Search 準確率低於 Vector Only（不應該發生）")

# ============================================
# 儲存測試報告
# ============================================

report = {
    'test_date': pd.Timestamp.now().isoformat(),
    'k': k,
    'total_test_cases': len(test_cases),
    'metrics': {
        'vector_only': metrics['vector_only'] if 'vector_only' in metrics and metrics['vector_only'] else None,
        'fts_only': metrics['fts_only'] if 'fts_only' in metrics and metrics['fts_only'] else None,
        'hybrid': metrics['hybrid'] if 'hybrid' in metrics and metrics['hybrid'] else None,
    },
    'detailed_results': results_summary,
}

report_file = os.path.join(DATA_DIR, "retrieval_test_report.json")
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n💾 測試報告已儲存：{report_file}")

# ============================================
# 結論
# ============================================

print("\n" + "=" * 80)
print("結論")
print("=" * 80)

if metrics['hybrid'] and metrics['hybrid']['recall_at_k'] >= 0.8:
    print("✅ Hybrid Search 系統運作良好！")
    print(f"   Recall@{k} 達到 {metrics['hybrid']['recall_at_k']:.0%}")
    print("   人名檢索問題已解決。")
elif metrics['hybrid']:
    print("⚠️  Hybrid Search 需要調整")
    print(f"   目前 Recall@{k}: {metrics['hybrid']['recall_at_k']:.0%}")
    print("   建議檢查：")
    print("   1. FTS index 是否正確建立")
    print("   2. 人名偵測邏輯是否準確")
    print("   3. 測試資料是否包含期望球員")
else:
    print("❌ Hybrid Search 評估失敗")

print("\n🎯 Week 1 完成！下一步：")
print("   - Week 2: 建立 LLM Agent 和 Query 分類器")
print("   - Week 3: 評估系統和建立 Demo")
print("=" * 80)