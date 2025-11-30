"""
MLB Team Manager Assistant - 快速測試 (適用於 tests/ 目錄)
快速驗證系統是否可以正常運行
"""

import sys
import os

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def quick_test():
    """快速測試"""
    
    print("\n" + "=" * 80)
    print("MLB Team Manager Assistant - 快速測試")
    print("=" * 80)
    
    # 測試 1: 導入模組
    print("\n[1/4] 測試模組導入...")
    try:
        from src.retrieval.hybrid_search import HybridSearch
        from src.retrieval.query_router import QueryRouter
        print("✅ 模組導入成功")
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        return False
    
    # 測試 2: 初始化系統
    print("\n[2/4] 測試系統初始化...")
    try:
        searcher = HybridSearch()
        router = QueryRouter()
        print("✅ 系統初始化成功")
    except Exception as e:
        print(f"❌ 系統初始化失敗: {e}")
        return False
    
    # 測試 3: 查詢分類
    print("\n[3/4] 測試查詢分類...")
    try:
        test_query = "Aaron Judge 2022年的 wOBA 是多少？"
        result = router.classify_query(test_query)
        print(f"✅ 查詢分類成功")
        print(f"   查詢: {test_query}")
        print(f"   類型: {result['query_type']}")
        print(f"   語言: {result['language']}")
        print(f"   信心: {result['confidence']:.2f}")
    except Exception as e:
        print(f"❌ 查詢分類失敗: {e}")
        return False
    
    # 測試 4: 檢索功能
    print("\n[4/4] 測試檢索功能...")
    try:
        test_query = "Aaron Judge 2022"
        results = searcher.auto_search(test_query, k=3)
        print(f"✅ 檢索成功")
        print(f"   查詢: {test_query}")
        print(f"   結果數: {len(results)}")
        print(f"\n   Top 3 結果:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['player_id']:30s} (分數: {result['score']:.4f})")
    except Exception as e:
        print(f"❌ 檢索失敗: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 所有測試通過！系統運行正常。")
    print("=" * 80)
    print("\n下一步:")
    print("  1. 運行完整測試: python tests/test_system.py")
    print("  2. 運行評估測試: python tests/evaluate_system.py")
    print("  3. 數據診斷: python tests/diagnose_data.py")
    print("  4. 啟動網頁應用: python src/web/app.py")
    print()
    
    return True


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
