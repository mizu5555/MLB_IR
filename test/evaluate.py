"""
MLB Team Manager Assistant
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 設定專案根目錄
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class PerformanceEvaluator:

    def __init__(self):
        print("\n" + "=" * 80)
        print("MLB Team Manager Assistant - 性能評估")
        print("=" * 80)

        from src.retrieval.hybrid_search import HybridSearch
        from src.retrieval.query_router import QueryRouter

        self.searcher = HybridSearch()
        self.router = QueryRouter()

        # --------------------------------------------------------
        # Test Set (Factual / Ranking / Comparison)
        # --------------------------------------------------------
        self.test_queries = [

            # ---------- Factual ----------
            {
                "query": "大谷在2023年打擊表現",
                "type": "factual",
                "expected_player_name": "Shohei Ohtani",
                "expected_season": 2023,
            },

            # ---------- Ranking ----------
            {
                "query": "2024全壘打數前5名",
                "type": "ranking",
                "expected_player_name": None,
                "expected_season": None,
            },

            # ---------- Comparison ----------
            {
                "query": "比較 Judge 跟 Ohtani 2022年的全壘打數",
                "type": "comparison",
                "expected_player_name": "Shohei Ohtani",
                "expected_season": 2022,
            },
        ]

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(self.test_queries),
            "classification_accuracy": 0,
            "recall_at_5": 0,
            "recall_at_10": 0,
            "precision_at_5": 0,
            "precision_at_10": 0,
            "mrr": 0,
            "details": []
        }

    # ======================================================================
    def evaluate(self):
        print("\n" + "=" * 80)
        print("開始評估")
        print("=" * 80)

        correct_class = 0
        recall5 = 0
        recall10 = 0
        precision5_total = 0
        precision10_total = 0
        rr = []

        for i, case in enumerate(self.test_queries, 1):
            print(f"\n[{i}/{len(self.test_queries)}] 查詢: {case['query']}")
            print("-" * 80)

            # 1) Routing
            pred = self.router.route(case["query"])
            type_ok = pred["query_type"] == case["type"]

            if type_ok:
                correct_class += 1
                print(f"✅ 類型分類正確: {pred['query_type']}")
            else:
                print(f"❌ 類型分類錯誤: 得到 {pred['query_type']}，預期 {case['type']}")

            # 2) Hybrid Search
            results = self.searcher.search(
                pred["normalized_query"],
                routed=pred,
                k=10,
                alpha=0.4,
                filter_players=pred.get("players"),
                filter_seasons=pred.get("seasons"),
                boost_type=pred.get("type_boost"),
            )

            # 3) 找 expected player 的排名（Recall / MRR 用）
            expected_name = case["expected_player_name"]
            expected_season = case["expected_season"]

            found_at = None
            if expected_name:
                for rank, r in enumerate(results, 1):
                    if r["player_name"] == expected_name and r["season"] == expected_season:
                        found_at = rank
                        break
            else:
                # Ranking 類型：只要找到任何結果都視為成功
                found_at = 1 if results else None

            # recall
            if found_at:
                print(f"✅ 找到預期結果，排名: {found_at}")
                if found_at <= 5: recall5 += 1
                if found_at <= 10: recall10 += 1
                rr.append(1 / found_at)
            else:
                print("❌ 未找到預期結果")
                rr.append(0)

            # 4) Precision@5 / Precision@10
            precision5 = 0
            precision10 = 0

            if expected_name:
                # check top-5
                top5 = results[:5]
                rel5 = sum(
                    1 for r in top5
                    if r["player_name"] == expected_name and r["season"] == expected_season
                )
                precision5 = rel5 / 5

                # check top-10
                top10 = results[:10]
                rel10 = sum(
                    1 for r in top10
                    if r["player_name"] == expected_name and r["season"] == expected_season
                )
                precision10 = rel10 / 10

            precision5_total += precision5
            precision10_total += precision10

            # 顯示 Top 3
            print("\nTop 3 搜尋結果:")
            for j, r in enumerate(results[:3], 1):
                print(f"  {j}. {r['player_id']} {r['player_name']} ({r['season']})  score={r['score']:.4f}")

            # 紀錄
            self.results["details"].append({
                "query": case["query"],
                "expected_type": case["type"],
                "predicted_type": pred["query_type"],
                "found_at": found_at,
                "precision_at_5": precision5,
                "precision_at_10": precision10,
                "top_results": [r["player_id"] for r in results[:3]],
            })

        # --------------------------------------------------------
        # Final Metrics
        # --------------------------------------------------------
        total = len(self.test_queries)
        self.results["classification_accuracy"] = correct_class / total
        self.results["recall_at_5"] = recall5 / total
        self.results["recall_at_10"] = recall10 / total
        self.results["precision_at_5"] = precision5_total / total
        self.results["precision_at_10"] = precision10_total / total
        self.results["mrr"] = sum(rr) / total

        self.print_summary()
        self.save_report()

    # ======================================================================
    def print_summary(self):
        print("\n" + "=" * 80)
        print("評估結果摘要")
        print("=" * 80)

        print(f"分類準確率: {self.results['classification_accuracy']:.1%}")
        print(f"Recall@5:   {self.results['recall_at_5']:.1%}")
        print(f"Recall@10:  {self.results['recall_at_10']:.1%}")
        print(f"Precision@5:  {self.results['precision_at_5']:.1%}")
        print(f"Precision@10: {self.results['precision_at_10']:.1%}")
        print(f"MRR:        {self.results['mrr']:.4f}")

    # ======================================================================
    def save_report(self):
        reports_dir = CURRENT_DIR / "reports"
        reports_dir.mkdir(exist_ok=True)

        out = reports_dir / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n📄 評估報告已保存: {out}")


# ======================================================================
def main():
    evaluator = PerformanceEvaluator()
    evaluator.evaluate()


if __name__ == "__main__":
    main()
