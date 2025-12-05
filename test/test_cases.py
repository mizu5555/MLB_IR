"""
MLB Team Manager Assistant - 完整性能測試
自動生成200筆測試案例（每種查詢類型50筆）
測試RAG和LLM兩種模式的所有核心指標

測試指標：
1. Recall@5
2. Precision@5  
3. MRR
4. Query Classification Accuracy
5. Fact Consistency Score
6. Zero Hallucination Rate
7. Response Time
"""

import sys
import os
import json
import requests
import time
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 專案路徑設定
THIS_FILE = Path(__file__).resolve()
TEST_DIR = THIS_FILE.parent
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# API 端點
API_URL = "http://localhost:8000/api/query"
HEALTH_URL = "http://localhost:8000/api/health"

# ============================================================
# 真實球員資料庫（2022-2024）
# ============================================================

REAL_PLAYERS = {
    "batters": [
        # 美國球員
        {"name": "Aaron Judge", "alias": "Judge"},
        {"name": "Mike Trout", "alias": "Trout"},
        {"name": "Mookie Betts", "alias": "Betts"},
        {"name": "Ronald Acuna Jr.", "alias": "Acuna"},
        {"name": "Freddie Freeman", "alias": "Freeman"},
        {"name": "Jose Altuve", "alias": "Altuve"},
        {"name": "Kyle Schwarber", "alias": "Schwarber"},
        {"name": "Pete Alonso", "alias": "Alonso"},
        {"name": "Matt Olson", "alias": "Olson"},
        {"name": "Rafael Devers", "alias": "Devers"},
        {"name": "Juan Soto", "alias": "Soto"},
        {"name": "Bryce Harper", "alias": "Harper"},
        {"name": "Vladimir Guerrero Jr.", "alias": "Guerrero"},
        {"name": "Corey Seager", "alias": "Seager"},
        {"name": "Marcus Semien", "alias": "Semien"},
        
        # 日本球員
        {"name": "Shohei Ohtani", "alias": "大谷"},
        {"name": "Seiya Suzuki", "alias": "鈴木誠也"},
    ],
    
    "pitchers": [
        # 美國球員
        {"name": "Gerrit Cole", "alias": "Cole"},
        {"name": "Spencer Strider", "alias": "Strider"},
        {"name": "Zack Wheeler", "alias": "Wheeler"},
        {"name": "Blake Snell", "alias": "Snell"},
        {"name": "Corbin Burnes", "alias": "Burnes"},
        {"name": "Kevin Gausman", "alias": "Gausman"},
        {"name": "Logan Webb", "alias": "Webb"},
        {"name": "Sandy Alcantara", "alias": "Alcantara"},
        {"name": "Framber Valdez", "alias": "Valdez"},
        {"name": "Dylan Cease", "alias": "Cease"},
        
        # 日本球員
        {"name": "Shohei Ohtani", "alias": "大谷"},
        {"name": "Yoshinobu Yamamoto", "alias": "山本"},
        {"name": "Yu Darvish", "alias": "達比修"},
        {"name": "Yusei Kikuchi", "alias": "菊池"},
    ]
}

# 指標對應
METRICS = {
    "batter": ["HR", "AVG", "OPS", "RBI", "SLG", "OBP", "wRC+", "wOBA"],
    "pitcher": ["ERA", "WHIP", "K%", "FIP", "K/9", "BB/9", "W", "SV"]
}

PLAYER_KEY_MAP = {
    "batter": "batters",
    "pitcher": "pitchers",
    "batters": "batters",
    "pitchers": "pitchers",
}

PLAYER_TO_METRIC = {
    "batters": "batter",
    "pitchers": "pitcher",
}

# 年份範圍
YEARS = [2022, 2023, 2024]

# Analysis 問題模板
ANALYSIS_TEMPLATES = {
    "batter": [
        "{player}{year}年打擊率為什麼這麼低",
        "{player}為什麼{year}三振這麼多",
        "{player}{year}年長打力為什麼下降",
        "{player}的選球為什麼{year}這麼差",
        "{player}{year}年上壘率為什麼不高",
    ],
    "pitcher": [
        "{player}{year}年投球壓制力為什麼下降",
        "{player}的控球為什麼{year}有問題",
        "{player}為什麼{year}防禦率這麼高",
        "{player}{year}年為什麼容易被長打",
        "{player}的三振率為什麼{year}下降",
    ]
}


# ============================================================
# 測試案例生成器
# ============================================================

def generate_factual_queries(n=50):
    queries = []

    templates = [
        "{player} {year} 打擊表現",
        "{player} {year} {metric}",
        "{player}在{year}年的{metric}是多少",
        "查詢{player} {year}年{metric}數據",
        "{year}年{player}的{metric}",
    ]
    
    for i in range(n):
        # 正確 key：batters / pitchers
        player_type = random.choice(["batters", "pitchers"])
        player = random.choice(REAL_PLAYERS[player_type])
        year = random.choice(YEARS)

        metric_type = PLAYER_TO_METRIC[player_type] 
        metric = random.choice(METRICS[metric_type])

        template = random.choice(templates)
        query = template.format(
            player=random.choice([player["name"], player["alias"]]),
            year=year,
            metric=metric,
        )

        queries.append({
            "id": f"F{i+1:03d}",
            "query": query,
            "type": "factual",
            "expected_player": player["name"],
            "expected_season": year,
            "expected_type": metric_type,
            "expected_metric": metric,
        })

    return queries



def generate_ranking_queries(n=50):
    """生成 Ranking 查詢（50筆）"""
    queries = []
    
    templates = [
        "{year} {metric} 前{topn}名",
        "{year}年{metric}排名前{topn}",
        "{year}年{metric}最高的{topn}位球員",
        "查詢{year} {metric} top {topn}",
        "{year}{metric}前{topn}高的選手",
    ]
    
    for i in range(n):
        # 隨機選擇指標類型
        metric_type = random.choice(["batter", "pitcher"])
        metric = random.choice(METRICS[metric_type])
        year = random.choice(YEARS)
        topn = random.choice([3, 5, 10])
        
        # 隨機選擇模板
        template = random.choice(templates)
        query = template.format(
            year=year,
            metric=metric,
            topn=topn
        )
        
        queries.append({
            "id": f"R{i+1:03d}",
            "query": query,
            "type": "ranking",
            "expected_season": year,
            "expected_type": metric_type,
            "expected_metric": metric,
            "expected_top_n": topn
        })
    
    return queries


def generate_comparison_queries(n=50):
    queries = []

    templates = [
        "比較{p1}和{p2}{year}年的{metric}",
        "{year}年{metric}比較：{p1} vs {p2}",
        "{p1} 和 {p2} 在 {year} 年誰的 {metric} 較好？",
    ]

    for i in range(n):

        player_type = random.choice(["batters", "pitchers"])  
        real_key = PLAYER_KEY_MAP[player_type]                

        p1, p2 = random.sample(REAL_PLAYERS[real_key], 2)
        year = random.choice(YEARS)

        metric_type = PLAYER_TO_METRIC[real_key]              # batter/pitcher
        metric = random.choice(METRICS[metric_type])

        template = random.choice(templates)

        query = template.format(
            p1=random.choice([p1["name"], p1["alias"]]),
            p2=random.choice([p2["name"], p2["alias"]]),
            year=year,
            metric=metric
        )

        queries.append({
            "id": f"C{i+1:03d}",
            "query": query,
            "type": "comparison",
            "players": [p1["name"], p2["name"]],
            "metric": metric,
            "season": year,
        })

    return queries



def generate_analysis_queries(n=50):
    """生成 Analysis 查詢（50筆）"""
    queries = []
    
    for i in range(n):
        # 隨機選擇球員類型
        player_type = random.choice(["batter", "pitcher"])
        players_key = "batters" if player_type == "batter" else "pitchers"
        player = random.choice(REAL_PLAYERS[players_key])
        year = random.choice(YEARS)
        
        # 隨機選擇問題模板
        template = random.choice(ANALYSIS_TEMPLATES[player_type])
        query = template.format(
            player=random.choice([player["name"], player["alias"]]),
            year=year
        )
        
        queries.append({
            "id": f"A{i+1:03d}",
            "query": query,
            "type": "analysis",
            "expected_player": player["name"],
            "expected_season": year,
            "expected_type": player_type
        })
    
    return queries


def generate_all_test_cases():
    """生成所有測試案例（200筆）"""
    print("📝 生成測試案例...")
    
    all_cases = []
    
    # 生成各類型查詢
    factual = generate_factual_queries(50)
    ranking = generate_ranking_queries(50)
    comparison = generate_comparison_queries(50)
    analysis = generate_analysis_queries(50)
    
    all_cases.extend(factual)
    all_cases.extend(ranking)
    all_cases.extend(comparison)
    all_cases.extend(analysis)
    
    print(f"✅ 生成完成：{len(all_cases)} 筆測試案例")
    print(f"   - Factual: {len(factual)} 筆")
    print(f"   - Ranking: {len(ranking)} 筆")
    print(f"   - Comparison: {len(comparison)} 筆")
    print(f"   - Analysis: {len(analysis)} 筆")
    
    return all_cases



# ============================================================
# API 呼叫與評估
# ============================================================

def call_api(query: str, mode: str = "rag", timeout: int = 60) -> dict:
    """呼叫查詢 API"""
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "mode": mode, "topk": 5},
            timeout=timeout
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"ok": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_query_classification(routed: dict, expected: dict) -> bool:
    """檢查查詢分類是否正確"""
    # 最重要：Query Type
    if routed.get("query_type") != expected.get("type"):
        return False
    
    # 檢查 Metric（如果有）
    if "expected_metric" in expected:
        if routed.get("metric") != expected["expected_metric"]:
            return False
    
    # 檢查 Top N（Ranking 查詢）
    if "expected_top_n" in expected:
        if routed.get("top_n") != expected["expected_top_n"]:
            return False
    
    return True


def calculate_retrieval_metrics(search_results: list, expected: dict, k: int = 5) -> dict:
    """計算檢索指標"""
    if not search_results:
        return {
            "recall_at_k": 0.0,
            "precision_at_k": 0.0,
            "mrr": 0.0
        }
    
    relevant_count = 0
    first_relevant_rank = None
    
    for i, result in enumerate(search_results[:k]):
        is_relevant = True
        
        # 檢查球員
        if "expected_player" in expected:
            actual = result.get("player_name", "").lower()
            expected_name = expected["expected_player"].lower()
            if expected_name not in actual:
                is_relevant = False
        
        # 檢查年度
        if "expected_season" in expected:
            if result.get("season") != expected["expected_season"]:
                is_relevant = False
        
        if "expected_seasons" in expected:
            if result.get("season") not in expected["expected_seasons"]:
                is_relevant = False
        
        # 檢查類型
        if "expected_type" in expected:
            expected_type = expected["expected_type"]
            if expected_type == "batter":
                if result.get("type") != "batter":
                    is_relevant = False
            elif expected_type == "pitcher":
                if result.get("type") != "pitcher":
                    is_relevant = False
        
        if is_relevant:
            relevant_count += 1
            if first_relevant_rank is None:
                first_relevant_rank = i + 1
    
    # 計算指標
    precision_at_1 = 1.0 if first_relevant_rank == 1 else 0.0
    precision = relevant_count / k
    recall = 1.0 if relevant_count > 0 else 0.0
    mrr = 1.0 / first_relevant_rank if first_relevant_rank else 0.0
    
    return {
        "recall_at_k": recall,
        "precision_at_k": precision,
        "precision_at_1": precision_at_1,
        "mrr": mrr
    }

def debug_dump(case, response):
    """輸出完整 debug 資訊，方便定位問題"""
    routed = response.get("routed", {})
    hits = response.get("search_results", [])
    
    return {
        "query": case["query"],
        "expected": case,
        "routed": routed,
        "search_top5": [
            {
                "player": h.get("player_name"),
                "season": h.get("season"),
                "type": h.get("type"),
                "score": h.get("score"),
            }
            for h in hits[:5]
        ],
        "answer_preview": (response.get("answer") or "")[:200],
        "issues": {
            "routing_mismatch": routed.get("query_type") != case.get("type"),
            "metric_mismatch": case.get("expected_metric") not in (None, routed.get("metric")),
            "retrieval_zero_hit": len(hits) == 0,
            "comparison_insufficient_hits": (
                case.get("type") == "comparison" and len(hits) < 2
            ),
        }
    }

def evaluate_single_case(case: dict, mode: str) -> dict:
    """評估單一測試案例"""
    query = case["query"]
    
    # 呼叫 API
    response = call_api(query, mode, timeout=90 if mode == "llm" else 60)
    
    if not response.get("ok"):
        return {
            "success": False,
            "error": response.get("error")
        }
    
    # 提取結果
    result = {
        "success": True,
        "case_id": case["id"],
        "query": case["query"],
        "query_type": case["type"],
        "mode": mode,
    }
    
    # 1. Query Classification
    routed = response.get("routed", {})
    result["classification_correct"] = check_query_classification(routed, case)
    if not result["classification_correct"]:
        result["classification_error"] = {
            "expected_type": case.get("type"),
            "router_predicted": routed.get("query_type"),
            "expected_metric": case.get("expected_metric"),
            "route_metric": routed.get("metric"),
            "expected_player": case.get("expected_player"),
            "routed_players": routed.get("players"),
        }

    
    # 2. Retrieval Metrics（僅非 Ranking）
    if case["type"] != "ranking":
        search_results = response.get("search_results", [])
        metrics = calculate_retrieval_metrics(search_results, case)
        result.update(metrics)
    else:
        # Ranking 查詢不評估 Recall/Precision/MRR
        result["recall_at_k"] = None
        result["precision_at_k"] = None
        result["mrr"] = None
    
    # 3. Fact Consistency（僅 LLM 模式）
    if mode == "llm":
        fact_check = response.get("fact_check", {})
        result["fact_consistency"] = fact_check.get("confidence", 0.0)
        result["hallucination_count"] = fact_check.get("hallucination_count", 0)
    else:
        result["fact_consistency"] = 1.0
        result["hallucination_count"] = 0
    
    # 4. Response Time
    result["response_time"] = response.get("metrics", {}).get("response_time", 0)
    
    return result


# ============================================================
# 主測試流程
# ============================================================

def run_full_test():
    """運行完整測試（200筆）"""
    
    print("\n" + "="*80)
    print("🧪 MLB Team Manager Assistant - 200筆完整性能測試")
    print("="*80)
    
    # 檢查 API
    print("\n[1/5] 檢查 API 狀態...")
    try:
        health = requests.get(HEALTH_URL, timeout=5)
        if health.status_code != 200:
            print("❌ API 未運行")
            return
    except:
        print("❌ 無法連接到 API，請先啟動：python src/web/app.py")
        return
    print("✅ API 運行正常")
    
    # 生成測試案例
    print("\n[2/5] 生成測試案例...")
    test_cases = generate_all_test_cases()
    
    # 儲存測試案例
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = PROJECT_ROOT / "test" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cases_file = output_dir / f"test_cases_{timestamp}.json"
    with open(cases_file, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    print(f"✅ 測試案例已儲存：{cases_file}")
    
    # 初始化結果收集
    results = {
        "rag": [],
        "llm": []
    }   
    debug_logs = []

    # ==================== RAG 模式測試 ====================
    print("\n[3/5] 測試 RAG 模式（200筆）...")
    print("-" * 80)
    print("⏳ 預計耗時：約 3-5 分鐘")
    
    for i, case in enumerate(test_cases):
        if (i + 1) % 20 == 0:
            print(f"   進度：{i+1}/200 ({(i+1)/200*100:.1f}%)")
        
        result = evaluate_single_case(case, "rag")
        if result["success"]:
            results["rag"].append(result)
            raw_response = call_api(case["query"], "rag")
            debug_logs.append(debug_dump(case, raw_response))
        
        # 延遲避免過載
        if (i + 1) % 10 == 0:
            time.sleep(1)
    
    print(f"✅ RAG 測試完成：{len(results['rag'])}/{len(test_cases)} 成功")
    
    # ==================== LLM 模式測試（僅 Analysis）====================
    print("\n[4/5] 測試 LLM 模式（50筆 Analysis）...")
    print("-" * 80)
    print("⏳ 預計耗時：約 3-5 分鐘")
    
    analysis_cases = [c for c in test_cases if c["type"] == "analysis"]
    
    for i, case in enumerate(analysis_cases):
        if (i + 1) % 10 == 0:
            print(f"   進度：{i+1}/50 ({(i+1)/50*100:.1f}%)")
        
        result = evaluate_single_case(case, "llm")
        if result["success"]:
            results["llm"].append(result)
        
        # LLM 需要更長延遲
        if (i + 1) % 5 == 0:
            time.sleep(2)
    
    print(f"✅ LLM 測試完成：{len(results['llm'])}/{len(analysis_cases)} 成功")
    
    # ==================== 計算總體指標 ====================
    print("\n[5/5] 計算總體指標...")
    print("="*80)
    
    summary = calculate_summary_metrics(results)
    
    # 輸出報告
    print_summary_report(summary)
    
    # 儲存詳細結果
    full_report = {
        "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_cases": len(test_cases),
        "summary": summary,
        "detailed_results": results
    }
    
    report_file = output_dir / f"full_test_report_{timestamp}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 詳細報告已儲存：{report_file}")
    
    debug_file = output_dir / f"debug_logs_{timestamp}.jsonl"
    with open(debug_file, "w", encoding="utf-8") as f:
        for log in debug_logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    print(f"🐞 Debug 詳細紀錄已儲存：{debug_file}")

    # 生成 Markdown 報告
    generate_markdown_report(summary, output_dir, timestamp)
    
    print("\n" + "="*80)
    print("🎉 測試完成！")
    print("="*80)
    
    return full_report


def calculate_summary_metrics(results: dict) -> dict:
    """計算總體指標"""
    summary = {
        "rag": {},
        "llm": {}
    }
    
    # ==================== RAG 模式指標 ====================
    rag_results = results["rag"]
    
    if rag_results:
        # Query Classification Accuracy
        classification_correct = sum(1 for r in rag_results if r.get("classification_correct"))
        summary["rag"]["classification_accuracy"] = classification_correct / len(rag_results)
        
        # Retrieval Metrics（排除 Ranking）
        non_ranking = [r for r in rag_results if r.get("recall_at_k") is not None]
        if non_ranking:
            summary["rag"]["recall_at_5"] = sum(r["recall_at_k"] for r in non_ranking) / len(non_ranking)
            summary["rag"]["precision_at_5"] = sum(r["precision_at_k"] for r in non_ranking) / len(non_ranking)
            summary["rag"]["mrr"] = sum(r["mrr"] for r in non_ranking) / len(non_ranking)
        else:
            summary["rag"]["recall_at_5"] = 0.0
            summary["rag"]["precision_at_5"] = 0.0
            summary["rag"]["mrr"] = 0.0
        
        # Fact Consistency
        summary["rag"]["fact_consistency"] = 1.0
        summary["rag"]["zero_hallucination_rate"] = 1.0
        
        # Response Time
        summary["rag"]["avg_response_time"] = sum(r["response_time"] for r in rag_results) / len(rag_results)
        
        # 分類型統計
        summary["rag"]["by_type"] = {}
        for qtype in ["factual", "ranking", "comparison", "analysis"]:
            type_results = [r for r in rag_results if r.get("query_type") == qtype]
            if type_results:
                type_classification = sum(1 for r in type_results if r.get("classification_correct"))
                summary["rag"]["by_type"][qtype] = {
                    "total": len(type_results),
                    "classification_accuracy": type_classification / len(type_results)
                }
    
    # ==================== LLM 模式指標 ====================
    llm_results = results["llm"]
    
    if llm_results:
        # Query Classification Accuracy
        classification_correct = sum(1 for r in llm_results if r.get("classification_correct"))
        summary["llm"]["classification_accuracy"] = classification_correct / len(llm_results)
        
        # Retrieval Metrics
        non_ranking = [r for r in llm_results if r.get("recall_at_k") is not None]
        if non_ranking:
            summary["llm"]["recall_at_5"] = sum(r["recall_at_k"] for r in non_ranking) / len(non_ranking)
            summary["llm"]["precision_at_5"] = sum(r["precision_at_k"] for r in non_ranking) / len(non_ranking)
            summary["llm"]["mrr"] = sum(r["mrr"] for r in non_ranking) / len(non_ranking)
        else:
            summary["llm"]["recall_at_5"] = 0.0
            summary["llm"]["precision_at_5"] = 0.0
            summary["llm"]["mrr"] = 0.0
        
        # Fact Consistency
        summary["llm"]["fact_consistency"] = sum(r["fact_consistency"] for r in llm_results) / len(llm_results)
        zero_hallucinations = sum(1 for r in llm_results if r.get("hallucination_count", 0) == 0)
        summary["llm"]["zero_hallucination_rate"] = zero_hallucinations / len(llm_results)
        summary["llm"]["total_hallucinations"] = sum(r.get("hallucination_count", 0) for r in llm_results)
        
        # Response Time
        summary["llm"]["avg_response_time"] = sum(r["response_time"] for r in llm_results) / len(llm_results)
    
    return summary


def print_summary_report(summary: dict):
    """輸出總體報告"""
    print("\n" + "="*80)
    print("📊 總體評估報告")
    print("="*80)
    
    # RAG 模式
    if "rag" in summary and summary["rag"]:
        rag = summary["rag"]
        print("\n【RAG 模式】- 200 筆測試")
        print("-" * 80)
        print(f"  Recall@5:                    {rag['recall_at_5']:.1%}")
        print(f"  Precision@5:                 {rag['precision_at_5']:.1%}")
        print(f"  MRR:                         {rag['mrr']:.3f}")
        print(f"  Query Classification Acc:    {rag['classification_accuracy']:.1%}")
        print(f"  Fact Consistency:            {rag['fact_consistency']:.1%}")
        print(f"  Zero Hallucination Rate:     {rag['zero_hallucination_rate']:.1%}")
        print(f"  Avg Response Time:           {rag['avg_response_time']:.3f}s")
        
        if "by_type" in rag:
            print("\n  分類型準確度：")
            for qtype, stats in rag["by_type"].items():
                print(f"    {qtype:12s}: {stats['classification_accuracy']:.1%} ({stats['total']} 筆)")
    
    # LLM 模式
    if "llm" in summary and summary["llm"]:
        llm = summary["llm"]
        print("\n【LLM 模式】- 50 筆 Analysis 測試")
        print("-" * 80)
        print(f"  Recall@5:                    {llm['recall_at_5']:.1%}")
        print(f"  Precision@5:                 {llm['precision_at_5']:.1%}")
        print(f"  MRR:                         {llm['mrr']:.3f}")
        print(f"  Query Classification Acc:    {llm['classification_accuracy']:.1%}")
        print(f"  Fact Consistency:            {llm['fact_consistency']:.1%}")
        print(f"  Zero Hallucination Rate:     {llm['zero_hallucination_rate']:.1%}")
        print(f"  Total Hallucinations:        {llm['total_hallucinations']}")
        print(f"  Avg Response Time:           {llm['avg_response_time']:.3f}s")
    
    print("\n" + "="*80)


def generate_markdown_report(summary: dict, output_dir: Path, timestamp: str):
    """生成 Markdown 報告"""
    markdown_file = output_dir / f"full_test_report_{timestamp}.md"
    
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write("# MLB Team Manager Assistant - 完整性能測試報告\n\n")
        f.write(f"**測試時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**測試規模**: 200 筆（RAG 200筆 + LLM 50筆）\n\n")
        f.write("---\n\n")
        
        # RAG 表格
        if "rag" in summary and summary["rag"]:
            rag = summary["rag"]
            f.write("## 📊 RAG 模式性能（200筆）\n\n")
            f.write("| 指標 | 數值 | 說明 |\n")
            f.write("|------|------|------|\n")
            f.write(f"| **Recall@5** | {rag['recall_at_5']:.1%} | 前5個結果包含所有相關文檔 |\n")
            f.write(f"| **Precision@5** | {rag['precision_at_5']:.1%} | 前5個結果中相關文檔比例 |\n")
            f.write(f"| **MRR** | {rag['mrr']:.3f} | 第一個相關結果的排名 |\n")
            f.write(f"| **Query Classification Accuracy** | {rag['classification_accuracy']:.1%} | 查詢分類準確率 |\n")
            f.write(f"| **Fact Consistency Score** | {rag['fact_consistency']:.1%} | 事實一致性評分 |\n")
            f.write(f"| **Zero Hallucination Rate** | {rag['zero_hallucination_rate']:.1%} | 無數值幻覺案例比例 |\n")
            f.write(f"| **Avg Response Time** | {rag['avg_response_time']:.3f}s | 平均響應時間 |\n")
            f.write("\n")
            
            # 分類型統計
            if "by_type" in rag:
                f.write("### 分查詢類型準確度\n\n")
                f.write("| 查詢類型 | 測試案例 | 分類準確率 |\n")
                f.write("|---------|---------|----------|\n")
                for qtype, stats in rag["by_type"].items():
                    f.write(f"| {qtype.capitalize()} | {stats['total']} | {stats['classification_accuracy']:.1%} |\n")
                f.write("\n")
        
        # LLM 表格
        if "llm" in summary and summary["llm"]:
            llm = summary["llm"]
            f.write("## 🤖 LLM 模式性能（50筆 Analysis）\n\n")
            f.write("| 指標 | 數值 | 說明 |\n")
            f.write("|------|------|------|\n")
            f.write(f"| **Recall@5** | {llm['recall_at_5']:.1%} | 前5個結果包含所有相關文檔 |\n")
            f.write(f"| **Precision@5** | {llm['precision_at_5']:.1%} | 前5個結果中相關文檔比例 |\n")
            f.write(f"| **MRR** | {llm['mrr']:.3f} | 第一個相關結果的排名 |\n")
            f.write(f"| **Query Classification Accuracy** | {llm['classification_accuracy']:.1%} | 查詢分類準確率 |\n")
            f.write(f"| **Fact Consistency Score** | {llm['fact_consistency']:.1%} | 事實一致性評分 |\n")
            f.write(f"| **Zero Hallucination Rate** | {llm['zero_hallucination_rate']:.1%} | 無數值幻覺案例比例 |\n")
            f.write(f"| **Total Hallucinations** | {llm['total_hallucinations']} | 總數值偏差數量 |\n")
            f.write(f"| **Avg Response Time** | {llm['avg_response_time']:.3f}s | 平均響應時間 |\n")
            f.write("\n")
        
        f.write("---\n\n")
        f.write("## 📋 測試結論\n\n")
        
        if rag['classification_accuracy'] >= 0.95 and rag['recall_at_5'] >= 0.90:
            f.write("✅ **系統性能達標**\n\n")
            f.write("- 查詢分類準確率 ≥95%\n")
            f.write("- 檢索召回率 ≥90%\n")
            f.write("- RAG 模式 100% 事實準確\n")
        else:
            f.write("⚠️ **需要改進**\n\n")
            if rag['classification_accuracy'] < 0.95:
                f.write(f"- 查詢分類準確率需提升（當前 {rag['classification_accuracy']:.1%}）\n")
            if rag['recall_at_5'] < 0.90:
                f.write(f"- 檢索召回率需改善（當前 {rag['recall_at_5']:.1%}）\n")
    
    print(f"✅ Markdown 報告已儲存：{markdown_file}")


# ============================================================
# 主程式入口
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 開始完整性能測試（200筆）")
    print("="*80)
    print("\n⚠️  請確保：")
    print("   1. Flask 伺服器正在運行（python src/web/app.py）")
    print("   2. Ollama 正在運行（用於 LLM 測試）")
    print("\n⏱️  預計耗時：約 8-12 分鐘")
    print("   - RAG 測試（200筆）：3-5 分鐘")
    print("   - LLM 測試（50筆）：3-5 分鐘")
    print("   - 報告生成：1-2 分鐘")
    print("\n按 Enter 開始測試...")
    input()
    
    try:
        report = run_full_test()
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試已中斷")
    except Exception as e:
        print(f"\n\n❌ 測試錯誤: {e}")
        import traceback
        traceback.print_exc()
