"""
Phase 6.1 測試：關鍵字擴展和權重優化
重點測試之前失敗的查詢
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase6_hybrid_search import HybridSearch


def test_keyword_detection():
    """測試關鍵字檢測是否正確"""
    
    print("=" * 80)
    print("Phase 6.1: 關鍵字檢測測試")
    print("=" * 80)
    
    test_cases = [
        ("best sprint speed fastest runner", "batter"),  # 應該檢測為 batter
        ("high exit velocity power hitter", "batter"),
        ("pitcher with high strikeout rate", "pitcher"),
        ("fastest baserunner", "batter"),  # 新增
        ("stolen bases leader", "batter"),  # 新增
        ("best curveball", "pitcher"),  # 新增
        ("Aaron Judge home runs 2022", "batter"),
    ]
    
    print("\n檢測球員類型:")
    print("-" * 80)
    
    for query, expected_type in test_cases:
        query_lower = query.lower()
        
        # 使用擴展的關鍵字列表
        batter_keywords = [
            'hitter', 'batter', 'batting', 'hitting',
            'home runs', 'rbi', 'hits', 'doubles', 'triples', 'average',
            'exit velocity', 'barrel rate', 'hard hit', 'launch angle',
            'sprint speed', 'runner', 'baserunner', 'stolen bases', 'steal',
            'on base', 'slugging', 'ops', 'woba', 'wrc',
            'outfield', 'infield', 'first base', 'second base', 'shortstop', 'third base',
            'catcher', 'dh', 'designated hitter'
        ]
        
        pitcher_keywords = [
            'pitcher', 'pitching',
            'era', 'whip', 'strikeout', 'walk', 'saves', 'wins', 'losses',
            'fip', 'xfip', 'k%', 'bb%', 'hr/9', 'k/9', 'bb/9',
            'fastball', 'slider', 'curveball', 'changeup', 'cutter', 'sinker', 'splitter',
            'velocity', 'spin rate', 'movement',
            'starter', 'reliever', 'closer', 'setup'
        ]
        
        detected_type = None
        matched_keywords = []
        
        if any(kw in query_lower for kw in batter_keywords):
            detected_type = 'batter'
            matched_keywords = [kw for kw in batter_keywords if kw in query_lower]
        elif any(kw in query_lower for kw in pitcher_keywords):
            detected_type = 'pitcher'
            matched_keywords = [kw for kw in pitcher_keywords if kw in query_lower]
        
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} \"{query}\"")
        print(f"   期望: {expected_type}, 檢測: {detected_type}")
        if matched_keywords:
            print(f"   匹配關鍵字: {', '.join(matched_keywords)}")
        print()
    
    print("=" * 80)


def test_critical_queries():
    """測試之前失敗的關鍵查詢"""
    
    print("\n" + "=" * 80)
    print("Phase 6.1: 關鍵查詢測試")
    print("=" * 80)
    
    searcher = HybridSearch()
    
    critical_queries = [
        {
            'query': 'best sprint speed fastest runner',
            'expected_type': 'batter',
            'description': '之前返回投手，現在應該返回打者'
        },
        {
            'query': 'high exit velocity power hitter',
            'expected_type': 'batter',
            'description': '應該全部是打者'
        },
        {
            'query': 'stolen bases leader',
            'expected_type': 'batter',
            'description': '新測試：應該檢測為打者'
        },
        {
            'query': 'Aaron Judge home runs 2022',
            'expected_type': 'batter',
            'description': '應該 Top 1 = Aaron Judge_2022'
        }
    ]
    
    for test in critical_queries:
        query = test['query']
        expected_type = test['expected_type']
        description = test['description']
        
        print(f"\n查詢: '{query}'")
        print(f"描述: {description}")
        print("-" * 80)
        
        results = searcher.auto_search(query, k=5)
        
        # 檢查球員類型
        correct_type_count = 0
        for i, result in enumerate(results, 1):
            text = result['full_text']
            actual_type = 'batter' if 'Type: batter' in text else ('pitcher' if 'Type: pitcher' in text else 'unknown')
            
            is_correct = actual_type == expected_type
            status = "✅" if is_correct else "❌"
            
            if is_correct:
                correct_type_count += 1
            
            print(f"  {status} {i}. {result['player_id']:30s} (類型: {actual_type})")
        
        type_accuracy = correct_type_count / len(results)
        print(f"\n  類型正確率: {type_accuracy:.2f} ({correct_type_count}/{len(results)})")
        
        if type_accuracy == 1.0:
            print("  🎉 完美！所有結果類型正確！")
        elif type_accuracy >= 0.8:
            print("  ✅ 良好！大部分結果類型正確")
        else:
            print("  ⚠️ 需要改進")
    
    print("\n" + "=" * 80)


def test_weight_optimization():
    """測試權重優化效果"""
    
    print("\n" + "=" * 80)
    print("Phase 6.1: 權重優化測試")
    print("=" * 80)
    
    searcher = HybridSearch()
    
    test_queries = [
        {
            'query': 'Aaron Judge home runs 2022',
            'expected_alpha': 0.2,
            'description': '精確查詢（名字+年份）→ 80% BM25'
        },
        {
            'query': 'Juan Soto batting average',
            'expected_alpha': 0.35,
            'description': '球員查詢（只有名字）→ 65% BM25'
        },
        {
            'query': 'high exit velocity',
            'expected_alpha': 0.7,
            'description': '語意查詢 → 70% Vector'
        },
        {
            'query': 'top performing player',
            'expected_alpha': 0.7,
            'description': '語意查詢（包含 top）→ 70% Vector'
        }
    ]
    
    print("\n權重檢測:")
    print("-" * 80)
    
    for test in test_queries:
        query = test['query']
        expected_alpha = test['expected_alpha']
        description = test['description']
        
        print(f"\n查詢: \"{query}\"")
        print(f"描述: {description}")
        print(f"期望 alpha: {expected_alpha}")
        
        # 執行查詢（會打印實際 alpha）
        results = searcher.auto_search(query, k=3)
        
        # 顯示 Top 3
        print("  Top 3:")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result['player_id']}")
    
    print("\n" + "=" * 80)


def main():
    """執行所有測試"""
    
    print("\n" + "=" * 80)
    print("Phase 6.1 完整測試")
    print("改進項目:")
    print("  1. 擴展 batter_keywords（+sprint speed, runner, stolen bases 等）")
    print("  2. 擴展 pitcher_keywords（+球種、角色等）")
    print("  3. 精確查詢權重優化（α: 0.3 → 0.2）")
    print("  4. 球員查詢權重優化（α: 0.4 → 0.35）")
    print("=" * 80)
    
    # 測試 1: 關鍵字檢測
    test_keyword_detection()
    
    # 測試 2: 關鍵查詢
    test_critical_queries()
    
    # 測試 3: 權重優化
    test_weight_optimization()
    
    print("\n" + "=" * 80)
    print("✅ Phase 6.1 測試完成！")
    print("=" * 80)
    print("\n下一步:")
    print("  如果 Type Accuracy 顯著改善 → 繼續 Phase 6.2（增強文字描述）")
    print("  如果仍有問題 → 進一步調整關鍵字或權重")
    print("=" * 80)


if __name__ == "__main__":
    main()
