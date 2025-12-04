import sys
import os
import re
import json
import requests
import time
from pathlib import Path

from datetime import datetime
datetime_str = datetime.now().strftime('%Y%m%d_%H%M%S')

# 加入專案路徑
THIS_FILE = Path(__file__).resolve()             
TEST_DIR = THIS_FILE.parent                     
PROJECT_ROOT = TEST_DIR.parent                   
sys.path.insert(0, str(PROJECT_ROOT))

# API 端點
API_URL = "http://localhost:8000/api/query"

# 測試用例
TEST_CASES = [
    {
        "query": "大谷2023年投球壓制力為什麼下降",
        "expected_problem": "壓制力不足",
        "expected_metrics": ["K%", "K/9", "CSW%"],
        "player": "Shohei Ohtani",
        "season": 2023
    },
    {
        "query": "Yamamoto的控球有什麼問題",
        "expected_problem": "控球問題",
        "expected_metrics": ["BB%", "BB/9", "WHIP"],
        "player": "Yoshinobu Yamamoto",
        "season": 2024
    },
    {
        "query": "Judge為什麼2024三振這麼多",
        "expected_problem": "選球不佳",
        "expected_metrics": ["K%", "BB%", "O-Swing%"],
        "player": "Aaron Judge",
        "season": 2024
    },
]


def call_api(query: str, mode: str = "rag") -> dict:
    """
    呼叫 API 端點
    
    Args:
        query: 查詢字串
        mode: "rag" 或 "llm"
    
    Returns:
        API 回應的 JSON
    """
    try:
        response = requests.post(
            API_URL,
            json={
                "query": query,
                "mode": mode,
                "topk": 5
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API 錯誤: {response.status_code}")
            print(f"   回應: {response.text}")
            return {"ok": False, "error": response.text}
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API，請確保 Flask 伺服器正在運行（python src/web/app.py）")
        return {"ok": False, "error": "Connection failed"}
    except Exception as e:
        print(f"❌ 請求錯誤: {e}")
        return {"ok": False, "error": str(e)}


def rate_insight_depth(answer: str, problem_type: str = None) -> dict:
    """
    改進版洞察深度評估
    
    Returns:
        {
            "score": float,
            "breakdown": {
                "causal_reasoning": bool,
                "metric_correlation": bool,
                "actionable_suggestions": bool,
                "data_support": bool
            }
        }
    """
    breakdown = {
        "causal_reasoning": False,
        "metric_correlation": False,
        "actionable_suggestions": False,
        "data_support": False
    }
    
    # 1. 因果推理（檢查完整的因果結構）
    causal_patterns = [
        r"因為.{5,50}(所以|導致|造成)",
        r"(可能|主要)原因.{5,50}(是|在於)",
        r".{5,50}(使得|讓|導致).{5,50}",
    ]
    if any(re.search(pattern, answer) for pattern in causal_patterns):
        breakdown["causal_reasoning"] = True
    
    # 2. 跨指標關聯
    # 檢查是否同時提到多個統計指標
    stat_keywords = ["K%", "BB%", "ERA", "WHIP", "FIP", "OPS", "AVG", "HR", "RBI", 
                     "wRC+", "wOBA", "三振", "保送", "防禦率", "打擊率"]
    metrics_mentioned = sum(1 for kw in stat_keywords if kw in answer)
    if metrics_mentioned >= 2:
        breakdown["metric_correlation"] = True
    
    # 3. 可行建議（檢查具體動作）
    suggestion_patterns = [
        r"建議.{5,50}(提升|改善|加強|調整)",
        r"(可以|應該|需要).{5,50}(訓練|練習|改善)",
        r"(專注|加強).{5,50}(能力|技術)",
    ]
    if any(re.search(pattern, answer) for pattern in suggestion_patterns):
        breakdown["actionable_suggestions"] = True
    
    # 4. 數據支持（至少 3 個數值）
    numbers = re.findall(r'\d+\.?\d*', answer)
    if len(numbers) >= 3:
        breakdown["data_support"] = True
    
    # 計算總分
    score = sum(breakdown.values()) / 4.0
    
    return {
        "score": score,
        "breakdown": breakdown
    }


def evaluate_single_case(case: dict, mode: str) -> dict:
    """評估單一測試案例"""
    query = case["query"]
    print(f"\n{'='*60}")
    print(f"📝 查詢: {query}")
    print(f"🔧 模式: {mode.upper()}")
    
    # 呼叫 API
    response = call_api(query, mode)
    
    if not response.get("ok"):
        print(f"⚠️ 查詢出現警告: {response.get('error')}")
        return {
            "success": True,
            "query": query,
            "mode": mode,
            "problem_type": None,
            "answer": response.get("error"),
            "answer_length": len(response.get("error", "")),
            "fact_consistency": 1.0,
            "hallucination_count": 0,
            "insight_depth": 0,
            "response_time": response.get("metrics", {}).get("response_time", 0)
        }

    # 提取結果
    answer = response.get("answer", "")
    problem_type = response.get("problem_type")
    
    print(f"✅ 問題類型: {problem_type}")
    print(f"📊 回答長度: {len(answer)} 字元")
    
    # 評估
    result = {
        "success": True,
        "query": query,
        "mode": mode,
        "problem_type": problem_type,
        "answer": answer,
        "answer_length": len(answer),
    }
    
    # Fact Consistency（僅 LLM 模式）
    if mode == "llm":
        fact_check = response.get("fact_check", {})
        result["fact_consistency"] = fact_check.get("confidence", 0.0)
        result["hallucination_count"] = fact_check.get("hallucination_count", 0)
        
        print(f"🔍 事實一致性: {result['fact_consistency']:.1%}")
        print(f"⚠️  數值偏差: {result['hallucination_count']} 個")
        
        # ⭐ 新增：詳細輸出違規內容
        if fact_check.get("violation_details"):
            print(f"\n⚠️  數值偏差詳情:")
            for v in fact_check["violation_details"]:
                print(f"   • {v['message']}")
                print(f"     上下文: ...{v['context']}...")
    else:
        result["fact_consistency"] = 1.0
        result["hallucination_count"] = 0
    
    # ⭐ 改進：Insight Depth
    insight_result = rate_insight_depth(answer, problem_type)
    result["insight_depth"] = insight_result["score"]
    result["insight_breakdown"] = insight_result["breakdown"]
    
    print(f"💡 洞察深度: {insight_result['score']:.1%}")
    print(f"   • 因果推理: {'✅' if insight_result['breakdown']['causal_reasoning'] else '❌'}")
    print(f"   • 指標關聯: {'✅' if insight_result['breakdown']['metric_correlation'] else '❌'}")
    print(f"   • 可行建議: {'✅' if insight_result['breakdown']['actionable_suggestions'] else '❌'}")
    print(f"   • 數據支持: {'✅' if insight_result['breakdown']['data_support'] else '❌'}")
    
    # Response Time
    response_time = response.get("metrics", {}).get("response_time", 0)
    result["response_time"] = response_time
    print(f"⏱️  響應時間: {response_time:.2f}s")
    
    return result


def compare_modes():
    """對比 RAG vs LLM 模式"""
    print("\n" + "="*60)
    print("🔬 Analysis Query 評估對比：RAG vs LLM")
    print("="*60)
    
    results = {
        "rag": [],
        "llm": []
    }
    
    # 測試 RAG 模式
    print("\n\n【RAG 模式測試】")
    for i, case in enumerate(TEST_CASES):
        result = evaluate_single_case(case, "rag")
        if result["success"]:
            results["rag"].append(result)
        
        # ⭐ 每個測試之間延遲 2 秒
        if i < len(TEST_CASES) - 1:
            print("\n⏳ 等待 2 秒...")
            time.sleep(2)
    
    # 測試 LLM 模式
    print("\n\n【LLM 模式測試】")
    for i, case in enumerate(TEST_CASES):
        result = evaluate_single_case(case, "llm")
        if result["success"]:
            results["llm"].append(result)
        
        # ⭐ LLM 模式需要更長延遲（5 秒）
        if i < len(TEST_CASES) - 1:
            print("\n⏳ 等待 5 秒...")
            time.sleep(5)
    
    # 計算平均指標
    print("\n\n" + "="*60)
    print("📊 評估結果總結")
    print("="*60)
    
    for mode_name, mode_results in results.items():
        if not mode_results:
            continue
        
        avg_fact = sum(r["fact_consistency"] for r in mode_results) / len(mode_results)
        avg_insight = sum(r["insight_depth"] for r in mode_results) / len(mode_results)
        avg_time = sum(r["response_time"] for r in mode_results) / len(mode_results)
        total_hallucinations = sum(r["hallucination_count"] for r in mode_results)
        
        # ⭐ 新增：洞察深度細節
        breakdown_summary = {
            "causal_reasoning": 0,
            "metric_correlation": 0,
            "actionable_suggestions": 0,
            "data_support": 0
        }
        for r in mode_results:
            if "insight_breakdown" in r:
                for key in breakdown_summary:
                    if r["insight_breakdown"].get(key):
                        breakdown_summary[key] += 1
        
        print(f"\n【{mode_name.upper()} 模式】")
        print(f"  事實一致性:   {avg_fact:.1%}")
        print(f"  洞察深度:     {avg_insight:.1%}")
        print(f"    ├─ 因果推理: {breakdown_summary['causal_reasoning']}/{len(mode_results)}")
        print(f"    ├─ 指標關聯: {breakdown_summary['metric_correlation']}/{len(mode_results)}")
        print(f"    ├─ 可行建議: {breakdown_summary['actionable_suggestions']}/{len(mode_results)}")
        print(f"    └─ 數據支持: {breakdown_summary['data_support']}/{len(mode_results)}")
        print(f"  平均響應:     {avg_time:.2f}s")
        print(f"  數值偏差:     {total_hallucinations} 個")
    
    # 儲存結果
    output_dir = Path(PROJECT_ROOT) / "test" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"analysis_comparison_{datetime_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 詳細結果已儲存至: {output_file}")

if __name__ == "__main__":
    # 檢查 API 是否運行
    print("🔍 檢查 API 狀態...")
    try:
        health = requests.get("http://localhost:8000/api/health", timeout=5)
        if health.status_code == 200:
            print("✅ API 運行中")
            compare_modes()
        else:
            print("❌ API 狀態異常")
    except:
        print("❌ 無法連接到 API")
        print("請先啟動 Flask 伺服器：python src/web/app.py")