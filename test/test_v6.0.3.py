"""
MLB RAG v6.0.3 Bug Fix 測試腳本

測試 4 個新修正的 Bug：
1. Ranking 沒有排序
2. 無法識別「高/低/快」等比較詞
3. 中文綴詞導致球員識別失敗
4. 網頁不支援 Markdown 語法（手動測試）

執行方式：
    python src/retrieval/test_v6.0.3.py
"""

import sys
import importlib.util
from pathlib import Path

# 測試結果統計
total_pass = 0
total_fail = 0


def load_module_from_file(module_name, file_path):
    """
    從指定路徑載入模組
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_bug_1():
    """
    測試 Bug 1：Ranking 沒有排序
    
    測試 lookup_engine_v2.py 的修正：
    - rank() 函數正確排序
    - 越高越好（HR）→ 降序
    - 越低越好（ERA）→ 升序
    """
    global total_pass, total_fail
    
    print("=" * 60)
    print("測試 Bug 1：Ranking 排序")
    print("=" * 60)
    
    # 載入新檔案
    project_root = Path(__file__).resolve().parents[1]
    lookup_path = project_root / "src/retrieval" / "lookup_engine.py"
    
    print(f"\n📁 載入新檔案: {lookup_path}")
    
    if not lookup_path.exists():
        print(f"❌ 檔案不存在: {lookup_path}")
        return
    
    # 載入模組
    lookup_module = load_module_from_file("lookup_engine", lookup_path)
    LookupEngine = lookup_module.LookupEngine
    
    lookup = LookupEngine()
    
    pass_count = 0
    fail_count = 0
    
    # 測試 1：全壘打排名（越高越好）
    print("\n測試 1: 2024 全壘打前 5 名（應該從高到低）")
    results = lookup.rank(season=2024, metric="HR", top_n=5)
    
    if not results:
        print("  ❌ FAIL: 沒有結果")
        fail_count += 1
    else:
        print(f"  前 5 名：")
        prev_val = float('inf')
        sorted_correctly = True
        
        for i, (rec, val) in enumerate(results, 1):
            print(f"    {i}. {rec['player_name']} - {val}")
            if val > prev_val:
                sorted_correctly = False
            prev_val = val
        
        if sorted_correctly:
            print(f"  結果: ✅ PASS（降序排列）")
            pass_count += 1
        else:
            print(f"  結果: ❌ FAIL（排序錯誤）")
            fail_count += 1
    
    # 測試 2：防禦率排名（越低越好）
    print("\n測試 2: 2023 防禦率前 3 名（應該從低到高）")
    results = lookup.rank(season=2023, metric="ERA", top_n=3)
    
    if not results:
        print("  ❌ FAIL: 沒有結果")
        fail_count += 1
    else:
        print(f"  前 3 名：")
        prev_val = 0
        sorted_correctly = True
        
        for i, (rec, val) in enumerate(results, 1):
            print(f"    {i}. {rec['player_name']} - {val}")
            if val < prev_val:
                sorted_correctly = False
            prev_val = val
        
        if sorted_correctly:
            print(f"  結果: ✅ PASS（升序排列）")
            pass_count += 1
        else:
            print(f"  結果: ❌ FAIL（排序錯誤）")
            fail_count += 1
    
    print(f"\nBug 1 測試結果: {pass_count} 個通過, {fail_count} 個失敗")
    total_pass += pass_count
    total_fail += fail_count


def test_bug_2():
    """
    測試 Bug 2：無法識別「高/低/快」等比較詞
    
    測試 query_router.py 的修正：
    - extract_top_n() 識別「前 N 高/低/快」
    - detect_query_type() 正確判斷為 ranking
    """
    global total_pass, total_fail
    
    print("\n" + "=" * 60)
    print("測試 Bug 2：識別「前 N 高/低」")
    print("=" * 60)
    
    # 載入新檔案
    project_root = Path(__file__).resolve().parents[1]
    router_path = project_root / "src/retrieval" / "query_router.py"
    
    print(f"\n📁 載入新檔案: {router_path}")
    
    if not router_path.exists():
        print(f"❌ 檔案不存在: {router_path}")
        return
    
    # 載入模組
    router_module = load_module_from_file("query_router", router_path)
    QueryRouter = router_module.QueryRouter
    
    router = QueryRouter()
    
    test_cases = [
        {
            "query": "2023 防禦率前 3 低",
            "expected_qtype": "ranking",
            "expected_top_n": 3,
        },
        {
            "query": "2023 全壘打前 3 高",
            "expected_qtype": "ranking",
            "expected_top_n": 3,
        },
        {
            "query": "2024 球速前 5 快",
            "expected_qtype": "ranking",
            "expected_top_n": 5,
        },
    ]
    
    pass_count = 0
    fail_count = 0
    
    for tc in test_cases:
        query = tc["query"]
        routed = router.route(query)
        
        qtype_pass = routed["query_type"] == tc["expected_qtype"]
        top_n_pass = routed["top_n"] == tc["expected_top_n"]
        
        print(f"\n查詢: {query}")
        print(f"  預期 Query Type: {tc['expected_qtype']}")
        print(f"  實際 Query Type: {routed['query_type']} {'✅' if qtype_pass else '❌'}")
        print(f"  預期 Top N: {tc['expected_top_n']}")
        print(f"  實際 Top N: {routed['top_n']} {'✅' if top_n_pass else '❌'}")
        
        if qtype_pass and top_n_pass:
            print(f"  結果: ✅ PASS")
            pass_count += 1
        else:
            print(f"  結果: ❌ FAIL")
            fail_count += 1
    
    print(f"\nBug 2 測試結果: {pass_count} 個通過, {fail_count} 個失敗")
    total_pass += pass_count
    total_fail += fail_count


def test_bug_3():
    """
    測試 Bug 3：中文綴詞導致球員識別失敗
    
    測試 query_router.py 的修正：
    - extract_players() 支援中文綴詞
    - 移除單詞邊界限制
    """
    global total_pass, total_fail
    
    print("\n" + "=" * 60)
    print("測試 Bug 3：中文綴詞識別")
    print("=" * 60)
    
    # 載入新檔案
    project_root = Path(__file__).resolve().parents[1]
    router_path = project_root / "src/retrieval" / "query_router.py"
    
    print(f"\n📁 載入新檔案: {router_path}")
    
    if not router_path.exists():
        print(f"❌ 檔案不存在: {router_path}")
        return
    
    # 載入模組
    router_module = load_module_from_file("query_router_bug3", router_path)
    QueryRouter = router_module.QueryRouter
    
    router = QueryRouter()
    
    test_cases = [
        {
            "query": "Ohtani 2023 全壘打",
            "expected_players": ["Shohei Ohtani"],
        },
        {
            "query": "Ohtani在2023的全壘打",
            "expected_players": ["Shohei Ohtani"],
        },
        {
            "query": "Judge跟Ohtani的比較",
            "expected_players": ["Aaron Judge", "Shohei Ohtani"],
        },
    ]
    
    pass_count = 0
    fail_count = 0
    
    for tc in test_cases:
        query = tc["query"]
        routed = router.route(query)
        
        # 檢查球員列表是否包含預期的球員
        players_pass = all(p in routed["players"] for p in tc["expected_players"])
        
        print(f"\n查詢: {query}")
        print(f"  預期 Players: {tc['expected_players']}")
        print(f"  實際 Players: {routed['players']} {'✅' if players_pass else '❌'}")
        
        if players_pass:
            print(f"  結果: ✅ PASS")
            pass_count += 1
        else:
            print(f"  結果: ❌ FAIL")
            fail_count += 1
    
    print(f"\nBug 3 測試結果: {pass_count} 個通過, {fail_count} 個失敗")
    total_pass += pass_count
    total_fail += fail_count


def test_regression():
    """
    回歸測試：確保 v6.0.2 的修正仍然有效
    
    測試：
    1. Intent 識別（中文關鍵字）
    2. 投手 AVG → BAA（需要 answer_templates_v3.py）
    3. 大谷多賽季比較（需要 answer_templates_v3.py）
    """
    global total_pass, total_fail
    
    print("\n" + "=" * 60)
    print("回歸測試：v6.0.2 修正仍然有效")
    print("=" * 60)
    
    # 載入新檔案
    project_root = Path(__file__).resolve().parents[1]
    router_path = project_root / "src/retrieval" / "query_router.py"
    
    print(f"\n📁 載入新檔案: {router_path}")
    
    if not router_path.exists():
        print(f"❌ 檔案不存在: {router_path}")
        return
    
    # 載入模組
    router_module = load_module_from_file("query_router_regression", router_path)
    QueryRouter = router_module.QueryRouter
    
    router = QueryRouter()
    
    test_cases = [
        {
            "query": "大谷 2024 防禦率",
            "expected_intent": "pitching",
            "expected_metric": "ERA",
        },
        {
            "query": "山本 2024 防禦率",
            "expected_intent": "pitching",
            "expected_metric": "ERA",
        },
    ]
    
    pass_count = 0
    fail_count = 0
    
    for tc in test_cases:
        query = tc["query"]
        routed = router.route(query)
        
        intent_pass = routed["intent"] == tc["expected_intent"]
        metric_pass = routed["metric"] == tc["expected_metric"]
        
        print(f"\n查詢: {query}")
        print(f"  預期 Intent: {tc['expected_intent']}")
        print(f"  實際 Intent: {routed['intent']} {'✅' if intent_pass else '❌'}")
        print(f"  預期 Metric: {tc['expected_metric']}")
        print(f"  實際 Metric: {routed['metric']} {'✅' if metric_pass else '❌'}")
        
        if intent_pass and metric_pass:
            print(f"  結果: ✅ PASS")
            pass_count += 1
        else:
            print(f"  結果: ❌ FAIL")
            fail_count += 1
    
    print(f"\n回歸測試結果: {pass_count} 個通過, {fail_count} 個失敗")
    total_pass += pass_count
    total_fail += fail_count


if __name__ == "__main__":
    print("=" * 60)
    print("MLB RAG v6.0.3 Bug Fix 測試")
    print("⭐ 測試新檔案（src/retrieval/）")
    print("=" * 60)
    
    try:
        # 測試 3 個自動化 Bug
        test_bug_1()  # Ranking 排序
        test_bug_2()  # 識別「前 N 高/低」
        test_bug_3()  # 中文綴詞
        
        # 回歸測試
        test_regression()
        
        # Bug 4 手動測試提示
        print("\n" + "=" * 60)
        print("⚠️ Bug 4（Markdown 渲染）需要手動測試")
        print("=" * 60)
        print("部署後，在網頁上測試以下查詢：")
        print("  1. 2024 全壘打前 5 名")
        print("  2. 確認 **粗體** 顯示為粗體")
        print("  3. 確認 ### 標題 顯示為標題")
        
        # 最終結果
        print("\n" + "=" * 60)
        print("最終測試結果（自動化測試）")
        print("=" * 60)
        print(f"✅ 通過: {total_pass} 個")
        print(f"❌ 失敗: {total_fail} 個")
        
        if total_fail == 0:
            print("\n🎉 所有測試通過！v6.0.3 修正成功！")
            print("\n下一步：執行部署指令")
            print("=" * 60)
            print("copy src/retrieval\\query_router.py src\\retrieval\\query_router.py")
            print("copy src/retrieval\\lookup_engine_v2.py src\\retrieval\\lookup_engine.py")
            print("copy src/retrieval\\index_v2.html src\\web\\static\\index.html")
            print("=" * 60)
        else:
            print(f"\n⚠️ 有 {total_fail} 個測試失敗，請檢查修正。")
    
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
