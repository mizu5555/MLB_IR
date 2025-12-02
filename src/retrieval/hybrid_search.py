import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import jieba
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "mlb_data_adv"


class HybridSearch:
    """
    混合檢索：
      - 向量語義搜尋 (SentenceTransformer embeddings)
      - BM25 關鍵字搜尋

    最後再根據 query_router 給的參數做 re-rank。

    ⚠ 注意：
    這個版本 **不再依賴 FAISS / bm25_index.pkl / bm25_ids**，
    直接在記憶體中用 numpy + BM25Okapi 重新建索引，
    以避免 id / index 不一致造成的錯誤。
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        print("🔧 Initializing HybridSearch...")

        # --------------------------------------------------
        # 1. 載入訓練資料
        # --------------------------------------------------
        training_path = DATA_DIR / "training_data.json"
        if not training_path.exists():
            raise FileNotFoundError(f"training_data.json not found at {training_path}")

        print("🔁 Loading training_data.json...")
        with open(training_path, "r", encoding="utf-8") as f:
            self.records: List[Dict[str, Any]] = json.load(f)

        self.n_docs = len(self.records)
        if self.n_docs == 0:
            raise ValueError("training_data.json is empty, cannot build index.")

        # --------------------------------------------------
        # 2. 載入向量（只用 numpy，不依賴 FAISS id）
        # --------------------------------------------------
        emb_path = DATA_DIR / "vector_embeddings.npy"
        if not emb_path.exists():
            raise FileNotFoundError(f"vector_embeddings.npy not found at {emb_path}")

        print("🔁 Loading vector embeddings (numpy)...")
        embs = np.load(emb_path)
        if embs.shape[0] != self.n_docs:
            print(
                f"⚠️ embeddings rows ({embs.shape[0]}) != records ({self.n_docs}), "
                f"will truncate to min length."
            )
            n = min(embs.shape[0], self.n_docs)
            embs = embs[:n]
            self.records = self.records[:n]
            self.n_docs = n

        # L2 normalize for cosine similarity
        embs = embs.astype("float32")
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.embeddings = embs / norms
        self.dim = self.embeddings.shape[1]

        # --------------------------------------------------
        # 3. 初始化 embedding 模型（查詢用）
        # --------------------------------------------------
        print(f"🔁 Initializing SentenceTransformer model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # --------------------------------------------------
        # 4. 建立 BM25 索引（用 keyword_text）
        #    → 保證順序和 self.records 完全一致
        # --------------------------------------------------
        print("🔁 Building BM25 index (from keyword_text)...")
        corpus_tokens: List[List[str]] = []
        for rec in self.records:
            text = rec.get("keyword_text") or rec.get("clean_text") or ""
            corpus_tokens.append(self._tokenize(text))
        self.bm25 = BM25Okapi(corpus_tokens)
        self.corpus_tokens = corpus_tokens

        print(f"✅ HybridSearch ready: {self.n_docs} records, dim={self.dim}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_scores(scores: np.ndarray) -> np.ndarray:
        if scores.size == 0:
            return scores
        s_min = float(scores.min())
        s_max = float(scores.max())
        if math.isclose(s_max, s_min):
            return np.zeros_like(scores, dtype="float32")
        return (scores - s_min) / (s_max - s_min)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        中英混合斷詞：
          - 中文用 jieba
          - 英文 / 數字用空白切
        """
        text = text.strip()
        if not text:
            return []

        tokens: List[str] = []
        has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in text)
        if has_cjk:
            tokens.extend([t for t in jieba.cut(text) if t.strip()])

        # 補上空白分詞（英文、數字、縮寫）
        for part in text.split():
            part = part.strip()
            if part:
                tokens.append(part)
        return tokens

    def _encode_query(self, query: str) -> np.ndarray:
        vec = self.model.encode(query, convert_to_numpy=True)
        vec = vec.astype("float32")
        norm = np.linalg.norm(vec)
        if norm == 0.0:
            return vec
        return vec / norm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        routed: Optional[Dict[str, Any]] = None,
        k: int = 10,
        alpha: float = 0.4,
        filter_players: Optional[List[str]] = None,
        filter_seasons: Optional[List[int]] = None,
        boost_type: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        回傳 top-k 搜尋結果。

        參數：
        - query: 查詢字串（會送去 embedding + BM25）
        - routed: query_router 的資訊（可選，用於 debug）
        - k: 最大回傳筆數
        - alpha: 向量分數的權重（0~1），其餘給 BM25
        - filter_players: 若指定，僅保留這些球員
        - filter_seasons: 若指定，僅保留這些年度
        - boost_type: {'batter': +0.5, 'pitcher': -0.3} 類型加權
        """
        if not query.strip():
            return []

        # 1) 向量相似度（cosine，範圍不一定是 0~1，後面會 normalize）
        q_vec = self._encode_query(query)
        vec_scores = self.embeddings @ q_vec  # (n_docs,)

        # 2) BM25
        bm25_tokens = self._tokenize(query)
        bm25_scores = np.array(self.bm25.get_scores(bm25_tokens), dtype="float32")

        # 3) Normalize
        vec_norm = self._normalize_scores(vec_scores)
        bm25_norm = self._normalize_scores(bm25_scores)

        # 4) Hybrid score
        alpha = max(0.0, min(1.0, float(alpha)))
        hybrid = alpha * vec_norm + (1.0 - alpha) * bm25_norm

        # 5) 類型加權（pitcher / batter）
        if boost_type:
            for i, rec in enumerate(self.records):
                t = (rec.get("type") or "").lower()
                boost = boost_type.get(t, 0.0)
                if boost:
                    hybrid[i] += float(boost)

        # 6) 條件過濾（玩家 / 年度）
        candidate_indices = list(range(self.n_docs))

        if filter_players:
            names = {p.lower() for p in filter_players}
            candidate_indices = [
                i
                for i in candidate_indices
                if (self.records[i].get("player_name") or "").lower() in names
            ]

        if filter_seasons:
            seas = set(filter_seasons)
            candidate_indices = [
                i for i in candidate_indices if self.records[i].get("season") in seas
            ]

        if not candidate_indices:
            return []

        # 7) 排序取 top-k
        candidate_indices.sort(key=lambda i: float(hybrid[i]), reverse=True)
        top_indices = candidate_indices[:k]

        results: List[Dict[str, Any]] = []
        for idx in top_indices:
            rec = self.records[idx]
            results.append(
                {
                    # 給 LookupEngine 用
                    "record_key": rec.get("record_key") or rec.get("id") or str(idx),
                    "score": float(hybrid[idx]),
                    "player_name": rec.get("player_name"),
                    "player_id": rec.get("player_id"),
                    "season": rec.get("season"),
                    "team": rec.get("team"),
                    "type": rec.get("type"),
                    "preview": (rec.get("clean_text") or rec.get("raw_text") or "")[:400],
                }
            )

        return results


# ----------------------------------------------------------------------
# CLI 測試（直接執行 hybrid_search.py）
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 為了讓在 src/retrieval 目錄直接執行也能 import query_router
    try:
        from query_router import QueryRouter  # type: ignore
    except ImportError:
        try:
            from src.retrieval.query_router import QueryRouter  # type: ignore
        except ImportError:
            QueryRouter = None  # type: ignore

    hs = HybridSearch()
    router = QueryRouter() if QueryRouter is not None else None

    print()
    print("輸入查詢（或 Enter 離開）：")
    while True:
        try:
            q = input("> ").strip()
        except EOFError:
            break

        if not q:
            break

        routed = router.route(q) if router is not None else None
        if routed is not None:
            print("\n--- Routed Result ---")
            print(json.dumps(routed, ensure_ascii=False, indent=2))

        hits = hs.search(
            routed["normalized_query"] if routed else q,
            routed=routed,
            k=10,
            alpha=0.4,
            filter_players=(routed or {}).get("players"),
            filter_seasons=(routed or {}).get("seasons"),
            boost_type=(routed or {}).get("type_boost"),
        )

        print("\n🔍 Hybrid Search 結果：")
        for h in hits:
            title = f"{h.get('player_name')} {h.get('season')} {h.get('type')}"
            print(f"{title:40s}  score={h['score']:.4f}")
        print("-" * 70)
