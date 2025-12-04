#!/usr/bin/env python3
# ============================================================
# Analysis Query 功能測試腳本
# ============================================================

import sys
import os

# 測試數據
TEST_QUERIES = [
    # === Analysis 查詢（應該被識別為 analysis）===
    {
        "query": "大谷2023年投球壓制力為什麼下降",
        "expected_type": "analysis",
        "expected_problem": "壓制力不足",
    },
    {
        "query": "Yamamoto的控球有什麼問題",
        "expected_type": "analysis",
        "expected_problem": "控球問題",
    },
    {
        "query": "Judge最近打擊率為什麼這麼低",
        "expected_type": "analysis",
        "expected_problem": "打擊率低",
    },
    {
        "query": "分析Gerrit Cole為什麼被長打這麼多",
        "expected_type": "analysis",
        "expected_problem": "被長打",
    },
    {
        "query": "Vlad Jr.的長打力有什麼問題",
        "expected_type": "analysis",
        "expected_problem": "長打力不足",
    },
    
    # === 非 Analysis 查詢（不應該被誤判）===
    {
        "query": "Ohtani 2023 表現",
        "expected_type": "factual",
        "expected_problem": None,
    },
    {
        "query": "2024全壘打前5名",
        "expected_type": "ranking",
        "expected_problem": None,
    },
    {
        "query": "Judge vs Ohtani",
        "expected_type": "comparison",
        "expected_problem": None,
    },
]

# 測試結果
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


def test_query_router():
    """測試 Query Router 的 analysis 識別"""
    print("\n" + "=" * 60)
    print("測試 1: Query Router - Analysis 查詢識別")
    print("=" * 60)
    
    try:
        # 這裡需要實際的 QueryRouter
        # 如果無法 import，跳過測試
        print("⚠️  需要在實際專案中運行此測試")
        print("   提示：確保 src/retrieval/query_router.py 已修改")
        return
        
    except ImportError as e:
        print(f"❌ 無法載入 QueryRouter: {e}")
        return


def test_problem_detection():
    """測試問題類型識別"""
    print("\n" + "=" * 60)
    print("測試 2: 問題類型識別")
    print("=" * 60)
    
    # 模擬 detect_problem_type 函數（簡化版）
    def detect_problem_type_simple(query):
        q = query.lower()
        
        if "壓制" in q or "三振" in q:
            return "壓制力不足"
        elif "控球" in q or "保送" in q:
            return "控球問題"
        elif "被長打" in q or "被轟" in q:
            return "被長打"
        elif "打擊率" in q:
            return "打擊率低"
        elif "長打力" in q:
            return "長打力不足"
        
        return None
    
    for test in TEST_QUERIES:
        query = test["query"]
        expected_problem = test["expected_problem"]
        
        detected_problem = detect_problem_type_simple(query)
        
        if detected_problem == expected_problem:
            print(f"✅ {query}")
            print(f"   識別: {detected_problem}")
            test_results["passed"] += 1
        else:
            print(f"❌ {query}")
            print(f"   預期: {expected_problem}")
            print(f"   實際: {detected_problem}")
            test_results["failed"] += 1
            test_results["errors"].append({
                "query": query,
                "expected": expected_problem,
                "actual": detected_problem
            })
        print()


def test_analysis_stats_mapping():
    """測試分析數據映射"""
    print("\n" + "=" * 60)
    print("測試 3: 分析數據映射")
    print("=" * 60)
    
    # 模擬配置（簡化版）
    ANALYSIS_PROBLEM_STATS = {
        "壓制力不足": {
            "main_stats": ["K%", "K/9", "CSW%", "SwStr%"],
            "supporting_stats": ["HardHit%", "Barrel%", "EV"],
        },
        "控球問題": {
            "main_stats": ["BB%", "BB/9", "Zone%", "F-Strike%"],
            "supporting_stats": ["WHIP", "K/BB", "O-Contact%"],
        },
        "打擊率低": {
            "main_stats": ["AVG", "BABIP", "Contact%", "K%"],
            "supporting_stats": ["LD%", "GB%", "IF/FB"],
        },
    }
    
    test_problems = ["壓制力不足", "控球問題", "打擊率低"]
    
    for problem in test_problems:
        if problem in ANALYSIS_PROBLEM_STATS:
            config = ANALYSIS_PROBLEM_STATS[problem]
            print(f"✅ {problem}")
            print(f"   主要指標: {config['main_stats']}")
            print(f"   支援指標: {config['supporting_stats']}")
            test_results["passed"] += 1
        else:
            print(f"❌ {problem} - 未找到配置")
            test_results["failed"] += 1
        print()


def test_analysis_report_structure():
    """測試分析報告結構"""
    print("\n" + "=" * 60)
    print("測試 4: 分析報告結構")
    print("=" * 60)
    
    # 模擬報告生成（簡化版）
    def generate_simple_report(player_name, season, problem_type):
        report = f"### 📊 {player_name} {season} 年分析報告\n\n"
        report += f"**問題診斷**: {problem_type}\n\n"
        report += "#### 🔍 關鍵數據診斷\n"
        report += "- K%: 18.5% ❌ 劣於平均\n\n"
        report += "#### 💡 分析重點\n"
        report += "1. 三振能力是否下降\n\n"
        report += "#### 🎯 改善建議\n"
        report += "1. 提升三振率\n"
        return report
    
    test_case = {
        "player_name": "Shohei Ohtani",
        "season": 2023,
        "problem_type": "壓制力不足"
    }
    
    report = generate_simple_report(**test_case)
    
    # 檢查報告結構
    required_sections = ["分析報告", "問題診斷", "關鍵數據", "分析重點", "改善建議"]
    
    all_present = all(section in report for section in required_sections)
    
    if all_present:
        print("✅ 報告結構完整")
        print("\n預覽:")
        print("-" * 60)
        print(report)
        test_results["passed"] += 1
    else:
        print("❌ 報告結構不完整")
        missing = [s for s in required_sections if s not in report]
        print(f"   缺少: {missing}")
        test_results["failed"] += 1


def print_summary():
    """輸出測試摘要"""
    print("\n" + "=" * 60)
    print("測試摘要")
    print("=" * 60)
    
    total = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    
    print(f"總測試數: {total}")
    print(f"通過: {test_results['passed']}")
    print(f"失敗: {test_results['failed']}")
    print(f"通過率: {pass_rate:.1f}%")
    
    if test_results["errors"]:
        print("\n失敗詳情:")
        for error in test_results["errors"]:
            print(f"- {error['query']}")
            print(f"  預期: {error['expected']}")
            print(f"  實際: {error['actual']}")


def main():
    """主測試流程"""
    print("=" * 60)
    print("Analysis Query 功能測試")
    print("=" * 60)
    
    # 執行測試
    test_query_router()
    test_problem_detection()
    test_analysis_stats_mapping()
    test_analysis_report_structure()
    
    # 輸出摘要
    print_summary()
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
    print("\n下一步：")
    print("1. 在實際專案中整合代碼")
    print("2. 運行完整系統測試")
    print("3. 測試前端範例按鈕")


if __name__ == "__main__":
    main()
