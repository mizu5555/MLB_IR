"""
Week 3: 自動評估系統
評估指標：Query 分類準確率、Recall@k、數據準確率、Ranking 質量
"""

import json
import os
import sys
from typing import Dict, List

# 導入 MLB Assistant
sys.path.append('.')
from week2_mlb_assistant import mlb_assistant, classify_query, vector_search

print("=" * 80)
print("Week 3: 自動評估系統")
print("=" * 80)

# ============================================
# 載入測試集
# ============================================

def load_test_queries(file_path: str = "./mlb_data/week3_test_queries.json") -> Dict:
    """載入測試查詢"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ============================================
# 評估 1: Query 分類準確率
# ============================================

def evaluate_classification(test_queries: Dict) -> Dict:
    """評估 Query 分類準確率"""
    
    print("\n" + "=" * 80)
    print("[評估 1] Query 分類準確率")
    print("=" * 80)
    
    results = {
        'total': 0,
        'correct': 0,
        'by_type': {
            'factual': {'total': 0, 'correct': 0},
            'ranking': {'total': 0, 'correct': 0},
            'analysis': {'total': 0, 'correct': 0}
        },
        'errors': []
    }
    
    for query_type in ['factual', 'ranking', 'analysis']:
        print(f"\n測試 {query_type.upper()} 查詢...")
        
        for test_case in test_queries[query_type]:
            query = test_case['query']
            expected_type = test_case['expected_type']
            test_id = test_case['id']
            
            # 分類
            predicted_type = classify_query(query)
            
            # 統計
            results['total'] += 1
            results['by_type'][expected_type]['total'] += 1
            
            if predicted_type == expected_type:
                results['correct'] += 1
                results['by_type'][expected_type]['correct'] += 1
                print(f"  ✅ {test_id}: '{query[:40]}...' → {predicted_type}")
            else:
                results['by_type'][expected_type]['total'] += 1
                results['errors'].append({
                    'test_id': test_id,
                    'query': query,
                    'expected': expected_type,
                    'predicted': predicted_type
                })
                print(f"  ❌ {test_id}: '{query[:40]}...' → Expected: {expected_type}, Got: {predicted_type}")
    
    # 計算準確率
    results['accuracy'] = results['correct'] / results['total'] if results['total'] > 0 else 0
    
    for query_type in ['factual', 'ranking', 'analysis']:
        total = results['by_type'][query_type]['total']
        correct = results['by_type'][query_type]['correct']
        results['by_type'][query_type]['accuracy'] = correct / total if total > 0 else 0
    
    # 顯示結果
    print("\n" + "-" * 80)
    print("分類準確率總結：")
    print(f"  總準確率：{results['accuracy']:.1%} ({results['correct']}/{results['total']})")
    print(f"  Factual：{results['by_type']['factual']['accuracy']:.1%} ({results['by_type']['factual']['correct']}/{results['by_type']['factual']['total']})")
    print(f"  Ranking：{results['by_type']['ranking']['accuracy']:.1%} ({results['by_type']['ranking']['correct']}/{results['by_type']['ranking']['total']})")
    print(f"  Analysis：{results['by_type']['analysis']['accuracy']:.1%} ({results['by_type']['analysis']['correct']}/{results['by_type']['analysis']['total']})")
    
    if results['errors']:
        print(f"\n  ⚠️  錯誤分類：{len(results['errors'])} 筆")
        for error in results['errors'][:5]:
            print(f"    {error['test_id']}: '{error['query'][:40]}...'")
            print(f"      Expected: {error['expected']}, Got: {error['predicted']}")
    
    return results

# ============================================
# 評估 2: Factual 查詢準確性
# ============================================

def evaluate_factual_accuracy(test_queries: Dict) -> Dict:
    """評估 Factual 查詢的球員識別和數據準確性"""
    
    print("\n" + "=" * 80)
    print("[評估 2] Factual 查詢準確性")
    print("=" * 80)
    
    results = {
        'total': 0,
        'correct_player': 0,
        'correct_value': 0,
        'player_errors': [],
        'value_errors': []
    }
    
    value_test_count = 0
    
    for test_case in test_queries['factual']:
        query = test_case['query']
        expected_player = test_case.get('expected_player')
        expected_stat = test_case.get('expected_stat')
        expected_value = test_case.get('expected_value')
        test_id = test_case['id']
        
        # 執行查詢
        print(f"\n測試 {test_id}: '{query}'")
        try:
            result = mlb_assistant(query)
            
            results['total'] += 1
            
            # 檢查球員
            if result['data'].get('top_result'):
                player_name = result['data']['top_result']['player_name']
                
                if expected_player and expected_player.lower() in player_name.lower():
                    results['correct_player'] += 1
                    print(f"  ✅ 球員正確：{player_name}")
                else:
                    results['player_errors'].append({
                        'test_id': test_id,
                        'query': query,
                        'expected': expected_player,
                        'actual': player_name
                    })
                    print(f"  ❌ 球員錯誤：Expected {expected_player}, Got {player_name}")
                
                # 檢查數值（如果有期望值）
                if expected_stat and expected_value:
                    value_test_count += 1
                    stat_key = f"stat_{expected_stat}"
                    actual_value = result['data']['top_result'].get(stat_key)
                    
                    if actual_value and abs(actual_value - expected_value) < 1:
                        results['correct_value'] += 1
                        print(f"  ✅ 數值正確：{expected_stat} = {actual_value:.3f}")
                    else:
                        results['value_errors'].append({
                            'test_id': test_id,
                            'query': query,
                            'stat': expected_stat,
                            'expected': expected_value,
                            'actual': actual_value
                        })
                        print(f"  ❌ 數值錯誤：Expected {expected_value}, Got {actual_value}")
            
        except Exception as e:
            print(f"  ❌ 錯誤：{e}")
            results['player_errors'].append({
                'test_id': test_id,
                'query': query,
                'error': str(e)
            })
    
    # 計算準確率
    results['player_accuracy'] = results['correct_player'] / results['total'] if results['total'] > 0 else 0
    if value_test_count > 0:
        results['value_accuracy'] = results['correct_value'] / value_test_count
        results['value_test_count'] = value_test_count
    
    # 顯示結果
    print("\n" + "-" * 80)
    print("Factual 查詢準確性總結：")
    print(f"  球員識別準確率：{results['player_accuracy']:.1%} ({results['correct_player']}/{results['total']})")
    if value_test_count > 0:
        print(f"  數值準確率：{results['value_accuracy']:.1%} ({results['correct_value']}/{value_test_count})")
    
    return results

# ============================================
# 評估 3: Ranking 查詢質量
# ============================================

def evaluate_ranking_quality(test_queries: Dict) -> Dict:
    """評估 Ranking 查詢的排序質量"""
    
    print("\n" + "=" * 80)
    print("[評估 3] Ranking 查詢質量")
    print("=" * 80)
    
    results = {
        'total': 0,
        'correct_top_1': 0,
        'correct_stat': 0,
        'errors': []
    }
    
    top_1_test_count = 0
    
    for test_case in test_queries['ranking']:
        query = test_case['query']
        expected_top_1 = test_case.get('expected_top_1')
        expected_stat = test_case.get('expected_stat')
        test_id = test_case['id']
        
        # 執行查詢
        print(f"\n測試 {test_id}: '{query}'")
        try:
            result = mlb_assistant(query)
            
            results['total'] += 1
            
            # 檢查統計類型
            if result['data'].get('stat_name'):
                actual_stat = result['data']['stat_name']
                if expected_stat and expected_stat.lower() in actual_stat.lower():
                    results['correct_stat'] += 1
                    print(f"  ✅ 統計類型正確：{actual_stat}")
                else:
                    print(f"  ⚠️  統計類型：Expected {expected_stat}, Got {actual_stat}")
            
            # 檢查 Top 1
            if result['data'].get('results') and expected_top_1:
                top_1_test_count += 1
                top_player = result['data']['results'][0]['name']
                
                if expected_top_1.lower() in top_player.lower():
                    results['correct_top_1'] += 1
                    print(f"  ✅ Top 1 正確：{top_player}")
                else:
                    results['errors'].append({
                        'test_id': test_id,
                        'query': query,
                        'expected_top_1': expected_top_1,
                        'actual_top_1': top_player
                    })
                    print(f"  ❌ Top 1 錯誤：Expected {expected_top_1}, Got {top_player}")
        
        except Exception as e:
            print(f"  ❌ 錯誤：{e}")
            results['errors'].append({
                'test_id': test_id,
                'query': query,
                'error': str(e)
            })
    
    # 計算準確率
    results['stat_accuracy'] = results['correct_stat'] / results['total'] if results['total'] > 0 else 0
    if top_1_test_count > 0:
        results['top_1_accuracy'] = results['correct_top_1'] / top_1_test_count
        results['top_1_test_count'] = top_1_test_count
    
    # 顯示結果
    print("\n" + "-" * 80)
    print("Ranking 查詢質量總結：")
    print(f"  統計類型準確率：{results['stat_accuracy']:.1%} ({results['correct_stat']}/{results['total']})")
    if top_1_test_count > 0:
        print(f"  Top 1 準確率：{results['top_1_accuracy']:.1%} ({results['correct_top_1']}/{top_1_test_count})")
    
    return results

# ============================================
# 評估 4: Analysis 查詢
# ============================================

def evaluate_analysis_queries(test_queries: Dict) -> Dict:
    """評估 Analysis 查詢"""
    
    print("\n" + "=" * 80)
    print("[評估 4] Analysis 查詢")
    print("=" * 80)
    
    results = {
        'total': 0,
        'correct_player': 0,
        'has_multi_season': 0,
        'errors': []
    }
    
    for test_case in test_queries['analysis']:
        query = test_case['query']
        expected_player = test_case.get('expected_player')
        test_id = test_case['id']
        
        # 執行查詢
        print(f"\n測試 {test_id}: '{query}'")
        try:
            result = mlb_assistant(query)
            
            results['total'] += 1
            
            # 檢查球員
            if result['data'].get('player_name'):
                player_name = result['data']['player_name']
                
                if expected_player and expected_player.lower() in player_name.lower():
                    results['correct_player'] += 1
                    print(f"  ✅ 球員正確：{player_name}")
                else:
                    results['errors'].append({
                        'test_id': test_id,
                        'query': query,
                        'expected': expected_player,
                        'actual': player_name
                    })
                    print(f"  ❌ 球員錯誤：Expected {expected_player}, Got {player_name}")
                
                # 檢查是否收集多賽季數據
                stats_over_time = result['data'].get('stats_over_time', [])
                if len(stats_over_time) > 1:
                    results['has_multi_season'] += 1
                    print(f"  ✅ 多賽季數據：{len(stats_over_time)} 個賽季")
                else:
                    print(f"  ⚠️  只有 {len(stats_over_time)} 個賽季數據")
        
        except Exception as e:
            print(f"  ❌ 錯誤：{e}")
            results['errors'].append({
                'test_id': test_id,
                'query': query,
                'error': str(e)
            })
    
    # 計算準確率
    results['player_accuracy'] = results['correct_player'] / results['total'] if results['total'] > 0 else 0
    results['multi_season_rate'] = results['has_multi_season'] / results['total'] if results['total'] > 0 else 0
    
    # 顯示結果
    print("\n" + "-" * 80)
    print("Analysis 查詢總結：")
    print(f"  球員識別準確率：{results['player_accuracy']:.1%} ({results['correct_player']}/{results['total']})")
    print(f"  多賽季數據收集率：{results['multi_season_rate']:.1%} ({results['has_multi_season']}/{results['total']})")
    
    return results

# ============================================
# 主執行函數
# ============================================

def run_evaluation():
    """執行完整評估"""
    
    # 載入測試集
    print("\n[載入測試集]")
    test_queries = load_test_queries()
    print(f"  ✅ Factual: {len(test_queries['factual'])} 筆")
    print(f"  ✅ Ranking: {len(test_queries['ranking'])} 筆")
    print(f"  ✅ Analysis: {len(test_queries['analysis'])} 筆")
    print(f"  ✅ 總計: {len(test_queries['factual']) + len(test_queries['ranking']) + len(test_queries['analysis'])} 筆")
    
    # 評估 1：分類準確率
    classification_results = evaluate_classification(test_queries)
    
    # 評估 2：Factual 準確性
    factual_results = evaluate_factual_accuracy(test_queries)
    
    # 評估 3：Ranking 質量
    ranking_results = evaluate_ranking_quality(test_queries)
    
    # 評估 4：Analysis 查詢
    analysis_results = evaluate_analysis_queries(test_queries)
    
    # 儲存結果
    output = {
        'metadata': test_queries['metadata'],
        'classification': classification_results,
        'factual': factual_results,
        'ranking': ranking_results,
        'analysis': analysis_results
    }
    
    output_file = "./mlb_data/week3_evaluation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print("評估完成")
    print("=" * 80)
    print(f"\n💾 詳細結果已儲存：{output_file}")
    
    # 總結報告
    print("\n" + "=" * 80)
    print("📊 總結報告")
    print("=" * 80)
    print(f"\n✅ Query 分類準確率：{classification_results['accuracy']:.1%}")
    print(f"   - Factual: {classification_results['by_type']['factual']['accuracy']:.1%}")
    print(f"   - Ranking: {classification_results['by_type']['ranking']['accuracy']:.1%}")
    print(f"   - Analysis: {classification_results['by_type']['analysis']['accuracy']:.1%}")
    
    print(f"\n✅ Factual 查詢準確性：")
    print(f"   - 球員識別：{factual_results['player_accuracy']:.1%}")
    if 'value_accuracy' in factual_results:
        print(f"   - 數值準確率：{factual_results['value_accuracy']:.1%}")
    
    print(f"\n✅ Ranking 查詢質量：")
    print(f"   - 統計類型：{ranking_results['stat_accuracy']:.1%}")
    if 'top_1_accuracy' in ranking_results:
        print(f"   - Top 1 準確率：{ranking_results['top_1_accuracy']:.1%}")
    
    print(f"\n✅ Analysis 查詢：")
    print(f"   - 球員識別：{analysis_results['player_accuracy']:.1%}")
    print(f"   - 多賽季數據：{analysis_results['multi_season_rate']:.1%}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_evaluation()
