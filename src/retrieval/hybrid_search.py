import json
import pickle
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from pathlib import Path
from query_router import QueryRouter


class HybridSearch:

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        ROOT = Path(__file__).resolve().parents[2]
        data_dir = ROOT / "data" / "mlb_data_adv"

        print("🔧 Initializing HybridSearch...")

        # ---------------------- Load embedding model ---------------------
        print(f"🔁 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # ---------------------- Load FAISS components -------------------
        print("🔁 Loading FAISS vector index...")
        self.vector_index = faiss.read_index(str(data_dir / "vector_index.faiss"))

        self.embeddings = np.load(data_dir / "vector_embeddings.npy")
        with open(data_dir / "vector_ids.json", "r") as f:
            self.vector_ids = json.load(f)

        # ---------------------- Load BM25 corpus ------------------------
        print("🔁 Loading BM25 index...")
        with open(data_dir / "bm25_corpus.pkl", "rb") as f:
            self.bm25_corpus = pickle.load(f)

        with open(data_dir / "bm25_ids.pkl", "rb") as f:
            self.bm25_ids = pickle.load(f)

        # Build BM25
        self.bm25 = BM25Okapi(self.bm25_corpus)

        # ---------------------- Load training data ----------------------
        print("🔁 Loading training_data.json...")
        with open(data_dir / "training_data.json", "r", encoding="utf-8") as f:
            self.records = {rec["id"]: rec for rec in json.load(f)}

        print(f"✅ HybridSearch ready: {len(self.records)} records.\n")

        # Query Router
        self.router = QueryRouter()

    # ------------------------------------------------------------
    # 取得 record_by_id
    # ------------------------------------------------------------
    def get_record(self, record_id: str):
        return self.records[record_id]

    # ------------------------------------------------------------
    # Vector search
    # ------------------------------------------------------------
    def vector_search(self, query_vec, topk=100):
        scores, indices = self.vector_index.search(query_vec, topk)
        scores = scores[0]
        indices = indices[0]

        results = []
        for score, idx in zip(scores, indices):
            if idx == -1:
                continue
            record_id = self.vector_ids[idx]  # <- 正確 mapping
            results.append((record_id, float(score)))

        return results

    # ------------------------------------------------------------
    # BM25 search
    # ------------------------------------------------------------
    def bm25_search(self, query, topk=100):
        tokens = query.split()
        scores = self.bm25.get_scores(tokens)

        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, sc in indexed_scores[:topk]:
            record_id = self.bm25_ids[idx]
            results.append((record_id, float(sc)))
        return results

    # ------------------------------------------------------------
    # Hybrid search scoring
    # ------------------------------------------------------------
    def compute_hybrid_score(self, vec_score, bm25_score, qtype, intent):
        # α 值對應 query_type
        alpha_map = {
            "factual": 0.2,
            "ranking": 0.5,
            "comparison": 0.3,
            "analysis": 0.4,
        }
        alpha = alpha_map.get(qtype, 0.3)

        return alpha * vec_score + (1 - alpha) * bm25_score

    # ------------------------------------------------------------
    # Ranking mode：依 metric 排序
    # ------------------------------------------------------------
    def metric_ranking(self, metric, season=None, top_n=10):
        metric = metric.upper()

        candidates = []
        for rec_id, rec in self.records.items():
            if season and rec["season"] != season:
                continue

            stats = rec["stats"]
            if metric not in stats:
                continue

            val = stats[metric]
            if isinstance(val, str):
                continue
            if isinstance(val, (int, float)):
                candidates.append((rec_id, val))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_n]

    # ------------------------------------------------------------
    # Comparison mode：
    # e.g. "誰 2023 年全壘打比大谷高？"
    # ------------------------------------------------------------
    def comparison_search(self, metric, target_player, season=None, top_n=20):
        metric = metric.upper()

        # 先找到大谷（或比較對象）的數值
        target_value = None
        for rec_id, rec in self.records.items():
            if rec["player_name"] == target_player:
                if season and rec["season"] != season:
                    continue
                if metric in rec["stats"]:
                    if isinstance(rec["stats"][metric], (int, float)):
                        target_value = rec["stats"][metric]
                        break

        if target_value is None:
            return []

        # 找比他高的
        candidates = []
        for rec_id, rec in self.records.items():
            if season and rec["season"] != season:
                continue
            if rec["player_name"] == target_player:
                continue

            val = rec["stats"].get(metric)
            if isinstance(val, (int, float)) and val > target_value:
                candidates.append((rec_id, val))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_n]

    # ------------------------------------------------------------
    # Main search function
    # ------------------------------------------------------------
    def search(self, query: str, routed: dict, topk=5):

        # ---------------------- Ranking mode ---------------------
        if routed["query_type"] == "ranking" and routed["metric"]:
            results = self.metric_ranking(
                metric=routed["metric"],
                season=routed["seasons"][0] if routed["seasons"] else None,
                top_n=routed["top_n"] or topk
            )
            return [(rec_id, val, "") for rec_id, val in results]

        # ---------------------- Comparison mode ------------------
        if routed["query_type"] == "comparison" and routed["metric"] and routed["players"]:
            results = self.comparison_search(
                metric=routed["metric"],
                target_player=routed["players"][0],
                season=routed["seasons"][0] if routed["seasons"] else None,
                top_n=routed["top_n"] or topk
            )
            return [(rec_id, val, "") for rec_id, val in results]

        # ---------------------- Hybrid factual search ------------
        query_vec = self.model.encode([query])
        vec_res = self.vector_search(query_vec, topk=200)
        bm25_res = self.bm25_search(query, topk=200)

        # dict for merging scores
        scores = {}

        for rec_id, vscore in vec_res:
            if rec_id not in scores:
                scores[rec_id] = {"vec": 0, "bm25": 0}
            scores[rec_id]["vec"] = vscore

        for rec_id, bscore in bm25_res:
            if rec_id not in scores:
                scores[rec_id] = {"vec": 0, "bm25": 0}
            scores[rec_id]["bm25"] = bscore

        # Apply boosting
        intent = routed["intent"]
        qtype = routed["query_type"]
        boost_map = routed["type_boost"]

        merged = []
        for rec_id, sc in scores.items():
            rec = self.records[rec_id]
            rec_type = rec["type"]

            hy_score = self.compute_hybrid_score(sc["vec"], sc["bm25"], qtype, intent)

            # boosting
            hy_score += boost_map.get(rec_type, 0.0)

            merged.append((rec_id, hy_score))

        merged.sort(key=lambda x: x[1], reverse=True)
        merged = merged[:topk]

        return [(rec_id, score, self.records[rec_id]["embedding_text"][:200] + "...") for rec_id, score in merged]


# ------------------------------------------------------------
# CLI 測試
# ------------------------------------------------------------
if __name__ == "__main__":
    hs = HybridSearch()

    while True:
        q = input("輸入查詢（或 Enter 離開）：")
        if not q.strip():
            break

        routed = hs.router.route(q)
        print("\n--- Routed Result ---")
        print(json.dumps(routed, indent=2, ensure_ascii=False))

        results = hs.search(routed["normalized_query"], routed=routed, topk=5)

        print("\n🔍 Hybrid Search 結果：")
        for rec_id, score, preview in results:
            rec = hs.get_record(rec_id)
            print(f"{rec['player_name']} {rec['season']} {rec['type']}  score={score:.4f}")
            print("   ", preview)
        print()
