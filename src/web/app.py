import sys
import json
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --------------------------------------------------------
# 動態加入 src/retrieval 到 sys.path，沿用你目前的模組路徑
# --------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]  # project 根目錄
RETRIEVAL_DIR = ROOT / "src" / "retrieval"
sys.path.append(str(RETRIEVAL_DIR))

from query_router import QueryRouter          
from hybrid_search import HybridSearch        
from lookup_engine import LookupEngine        


# --------------------------------------------------------
# Flask 初始化
# --------------------------------------------------------
app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
)
CORS(app)

# 全域共享物件，避免每次請求重載模型 / 索引
router = QueryRouter()
searcher = HybridSearch()
lookup = LookupEngine()

PROJECT_ROOT = ROOT
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


# --------------------------------------------------------
# 工具函式：把 HybridSearch 回傳的 record 縮成前端好吃的格式
# --------------------------------------------------------
def _serialize_hit(rec: dict) -> dict:
    """
    統一整理單筆檢索結果，避免前端跟著後端內部結構一起變。
    """
    if rec is None:
        return {}

    return {
        "id": rec.get("record_key") or rec.get("id"),
        "player_name": rec.get("player_name"),
        "season": rec.get("season"),
        "team": rec.get("team"),
        "type": rec.get("type"),
        "score": float(rec.get("score", 0.0)),
        # 簡短預覽文字：raw_text / clean_text / embedding_text / keyword_text 其中一種
        "preview": (
            rec.get("raw_text")
            or rec.get("clean_text")
            or rec.get("embedding_text")
            or rec.get("keyword_text")
            or ""
        )[:400],
        # stats 保留給之後 LLM 使用（前端如果想直接看也可以）
        "stats": rec.get("stats", {}),
    }


# --------------------------------------------------------
# 根目錄：前端單頁
# --------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(STATIC_DIR, INDEX_HTML.name)


# --------------------------------------------------------
# Router debug：只看 QueryRouter 不打檢索
# --------------------------------------------------------
@app.route("/api/router", methods=["POST"])
def api_router():
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()

    if not query:
        return jsonify({"ok": False, "error": "query 不可為空"}), 400

    routed = router.route(query)
    return jsonify({"ok": True, "query": query, "routed": routed})


# --------------------------------------------------------
# 主 API：整合 Router + HybridSearch + LookupEngine
# --------------------------------------------------------
@app.route("/api/query", methods=["POST"])
def api_query():
    """
    Request JSON:
    {
        "query": "大谷 2023 投球",
        "topk": 10      # optional，預設 10
    }

    Response JSON:
    {
        "ok": true,
        "query": "...",
        "routed": {...},
        "mode": "factual" | "comparison" | "ranking" | "semantic",
        "structured": {...} 或 null,
        "hits": [ { ...縮好的檢索結果... } ]
    }
    """
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    topk = int(data.get("topk") or 10)

    if not query:
        return jsonify({"ok": False, "error": "query 不可為空"}), 400

    # 1) Query Router
    routed = router.route(query)
    qtype = routed.get("query_type")
    metric = routed.get("metric")
    top_n = routed.get("top_n") or topk

    # 2) 先處理「結構化數值問題」：COMPARISON / RANKING
    structured = None

    # --- Comparison: 有誰 HR 比大谷高？ ---
    if qtype == "comparison" and metric:
        comp_list = lookup.comparison(routed, records=None)
        structured = {
            "kind": "comparison",
            "metric": metric,
            "baseline_player": routed.get("players", [None])[0],
            "season": routed.get("seasons", [None])[0],
            "results": comp_list,
        }
        hits = []  # 這類問題主要靠 structured，不一定需要檢索 hits

    # --- Ranking: 2024 全壘打前 10 名 ---
    elif qtype == "ranking" and metric:
        ranking_list = lookup.ranking(routed)
        structured = {
            "kind": "ranking",
            "metric": metric,
            "season": routed.get("seasons", [None])[0],
            "top_n": top_n,
            "results": ranking_list,
        }
        hits = []

    else:
        # 3) 其他情況：走 Hybrid Search
        normalized = routed.get("normalized_query") or query
        raw_hits = searcher.search(
            normalized,
            routed=routed,
            topk=top_n,
        )
        hits = [_serialize_hit(h) for h in raw_hits]

        # 若是 Factual + 有 metric → 幫你把數值也算出來
        if qtype == "factual" and metric and hits:
            fact = lookup.factual(raw_hits[0], metric)
            structured = {"kind": "factual", **fact}

        # 其他像 general analysis / semantic 查詢，就只回 hits
        if structured is None and qtype not in ("comparison", "ranking", "factual"):
            structured = {"kind": "semantic", "note": "僅回傳檢索結果，未做數值運算。"}

    return jsonify(
        {
            "ok": True,
            "query": query,
            "routed": routed,
            "mode": qtype,
            "structured": structured,
            "hits": hits,
        }
    )


# --------------------------------------------------------
# 健康檢查
# --------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"ok": True, "status": "ready"})


if __name__ == "__main__":
    # 預設跑在 8000，可照你習慣改
    app.run(host="0.0.0.0", port=8000, debug=True)
