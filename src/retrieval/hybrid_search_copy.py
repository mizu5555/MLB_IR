import json
import pickle
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from pathlib import Path

try:
    from .query_router import QueryRouter
except ImportError:
    from query_router import QueryRouter

class HybridSearch:

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        # 定義資料路徑
        self.root = Path(__file__).resolve().parents[2]
        self.data_dir = self.root / "data" / "mlb_data_adv"

        print("🔧 Initializing HybridSearch (v2.0 with FAISS)...")

        # ---------------------- 1. Load Embedding Model ---------------------
        print(f"🔁 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # ---------------------- 2. Load FAISS Index -------------------------
        # 如果沒有 FAISS 檔案，會報錯提醒使用者
        faiss_path = self.data_dir / "vector_index.faiss"
        if not faiss_path.exists():
            raise FileNotFoundError(f"❌ 找不到 FAISS 索引: {faiss_path}\n請先執行 step2_build_vector_index.py")
        
        print("🔁 Loading FAISS vector index...")
        self.vector_index = faiss.read_index(str(faiss_path))

        # 載入 ID 對照表
        with open(self.data_dir / "vector_ids.json", "r", encoding="utf-8") as f:
            self.vector_ids = json.load(f)

        # ---------------------- 3. Load BM25 Index --------------------------
        bm25_path = self.data_dir / "bm25_corpus.pkl"
        if not bm25_path.exists():
            raise FileNotFoundError(f"❌ 找不到 BM25 索引: {bm25_path}\n請先執行 step3_build_bm25_index.py")

        print("🔁 Loading BM25 index...")
        with open(bm25_path, "rb") as f:
            self.bm25_corpus = pickle.load(f)

        with open(self.data_dir / "bm25_ids.pkl", "rb") as f:
            self.bm25_ids = pickle.load(f)

        self.bm25 = BM25Okapi(self.bm25_corpus)

        # ---------------------- 4. Load Raw Records -------------------------
        print("🔁 Loading training_data.json...")
        with open(self.data_dir / "training_data.json", "r", encoding="utf-8") as f:
            self.records = {rec["id"]: rec for rec in json.load(f)}

        print(f"✅ HybridSearch ready: {len(self.records)} records.\n")

        # Router
        self.router = QueryRouter()

    # ------------------------------------------------------------
    # 核心：取得單筆資料
    # ------------------------------------------------------------
    def get_record(self, record_id: str):
        return self.records.get(record_id, {})

    # ------------------------------------------------------------
    # Vector Search (FAISS)
    # ------------------------------------------------------------
    def vector_search(self, query_vec, topk=100):
        # FAISS search
        # query_vec 必須是 2D array (1, dim)
        if len(query_vec.shape) == 1:
            query_vec = query_vec.reshape(1, -1)
            
        scores, indices = self.vector_index.search(query_vec, topk)
        
        # indices[0] 是第一筆查詢的結果
        found_indices = indices[0]
        found_scores = scores[0]

        results = []
        for score, idx in zip(found_scores, found_indices):
            if idx == -1: continue # FAISS 填充值
            if idx < len(self.vector_ids):
                rec_id = self.vector_ids[idx]
                results.append((rec_id, float(score)))
        return results

    # ------------------------------------------------------------
    # BM25 Search
    # ------------------------------------------------------------
    def bm25_search(self, query, topk=100):
        tokens = query.split() # 簡單分詞
        scores = self.bm25.get_scores(tokens)
        
        # 排序取 TopK
        # np.argsort 在大數據下可能慢，但幾千筆還好
        # 這裡用原生 sort
        indexed_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in indexed_scores[:topk]:
            rec_id = self.bm25_ids[idx]
            results.append((rec_id, float(score)))
        return results

    # ------------------------------------------------------------
    # 混合分數計算
    # ------------------------------------------------------------
    def compute_hybrid_score(self, vec_score, bm25_score, qtype, intent):
        # 根據查詢類型調整權重
        alpha = 0.5
        if qtype == "factual": alpha = 0.3      # 事實類多信 BM25 (關鍵字)
        elif qtype == "semantic": alpha = 0.7   # 語意類多信 Vector
        elif qtype == "analysis": alpha = 0.6
        
        # 簡單加權
        return alpha * vec_score + (1 - alpha) * bm25_score

    # ------------------------------------------------------------
    # 特殊模式：Ranking (數值排序)
    # ------------------------------------------------------------
    def metric_ranking(self, metric, season=None, top_n=10):
        metric = metric.upper()
        candidates = []
        
        for rid, rec in self.records.items():
            if season and str(rec.get("season")) != str(season):
                continue
            
            stats = rec.get("stats", {})
            val = stats.get(metric)
            
            # 確保數值有效
            if isinstance(val, (int, float)):
                candidates.append((rid, val))
                
        # 排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_n]

    # ------------------------------------------------------------
    # 特殊模式：Comparison (數值比較)
    # ------------------------------------------------------------
    def comparison_search(self, metric, target_player, season=None, top_n=20):
        metric = metric.upper()
        
        # 1. 找基準球員數值
        target_val = None
        for rid, rec in self.records.items():
            if target_player.lower() in rec["player_name"].lower():
                if season and str(rec["season"]) != str(season): continue
                if metric in rec.get("stats", {}):
                    target_val = rec["stats"][metric]
                    break
        
        if target_val is None:
            return [] # 找不到基準

        # 2. 找比他高的
        candidates = []
        for rid, rec in self.records.items():
            if season and str(rec.get("season")) != str(season): continue
            if rec["player_name"] == target_player: continue
            
            val = rec.get("stats", {}).get(metric)
            if isinstance(val, (int, float)) and val > target_val:
                candidates.append((rid, val))
                
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_n]

    # ------------------------------------------------------------
    # 主搜尋入口 (支援 topk 參數)
    # ------------------------------------------------------------
    def search(self, query: str, routed: dict, topk=5):
        qtype = routed.get("query_type")
        
        # 1. Ranking Mode
        if qtype == "ranking" and routed.get("metric"):
            ranks = self.metric_ranking(
                metric=routed["metric"],
                season=routed.get("seasons", [None])[0],
                top_n=routed.get("top_n", topk)
            )
            # 格式化回傳 (id, score, preview)
            return [(r[0], r[1], "") for r in ranks]

        # 2. Comparison Mode
        if qtype == "comparison" and routed.get("metric") and routed.get("players"):
            comps = self.comparison_search(
                metric=routed["metric"],
                target_player=routed["players"][0],
                season=routed.get("seasons", [None])[0],
                top_n=topk
            )
            return [(c[0], c[1], "") for c in comps]

        # 3. Hybrid Search (Default)
        # Vector
        q_vec = self.model.encode([query])
        vec_hits = self.vector_search(q_vec, topk=topk*2) # 多取一點做重排序
        
        # BM25
        bm25_hits = self.bm25_search(query, topk=topk*2)
        
        # Merge Scores
        scores = {}
        for rid, s in vec_hits:
            scores[rid] = scores.get(rid, {"v":0, "b":0})
            scores[rid]["v"] = s
            
        for rid, s in bm25_hits:
            scores[rid] = scores.get(rid, {"v":0, "b":0})
            scores[rid]["b"] = s
            
        # Final Scoring
        final_results = []
        for rid, s_dict in scores.items():
            final_score = self.compute_hybrid_score(
                s_dict["v"], s_dict["b"], qtype, routed.get("intent")
            )
            final_results.append((rid, final_score))
            
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        # 回傳前 N 筆
        results = []
        for rid, score in final_results[:topk]:
            rec = self.records[rid]
            # 預覽文字優先順序
            preview = rec.get("raw_text") or rec.get("embedding_text") or ""
            results.append((rid, score, preview))
            
        return results

if __name__ == "__main__":
    hs = HybridSearch()
    print("Test run complete.")