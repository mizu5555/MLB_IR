import sys
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --------------------------------------------------------
# 使用成功的引入方式
# --------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../..')
sys.path.insert(0, project_root)

try:
    # Retrieval 模組
    from src.retrieval.query_router import QueryRouter
    from src.retrieval.hybrid_search import HybridSearch
    from src.retrieval.lookup_engine import LookupEngine
    
    # Generation 模組
    from src.generation.prompt_templates import (
        format_fact_block,
        build_factual_prompt,
        build_comparison_prompt,
        build_ranking_prompt,
        STYLE_PRESETS
    )
    LLM_AVAILABLE = True
    print("✅ 成功載入 LLM generation 模組")
except ImportError as e:
    print(f"⚠️ Warning: LLM prompt templates not found - {e}")
    print("⚠️ LLM mode will be disabled")
    LLM_AVAILABLE = False

# --------------------------------------------------------
# Flask 初始化
# --------------------------------------------------------
app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
)
CORS(app)

# 全域共享物件
print("🔧 正在初始化檢索系統...")
router = QueryRouter()
searcher = HybridSearch()
lookup = LookupEngine()
print("✅ 檢索系統初始化完成")

PROJECT_ROOT = project_root
STATIC_DIR = os.path.join(current_dir, "static")
INDEX_HTML = "index.html"

# --------------------------------------------------------
# 檢查 Ollama 是否可用
# --------------------------------------------------------
OLLAMA_AVAILABLE = False
OLLAMA_MODEL = None

try:
    import ollama
    models = ollama.list()
    if hasattr(models, 'models') and models.models:
        OLLAMA_AVAILABLE = True
        OLLAMA_MODEL = models.models[0].model if hasattr(models.models[0], 'model') else 'llama3.2'
        if ':' in OLLAMA_MODEL:
            OLLAMA_MODEL = OLLAMA_MODEL.split(':')[0]
        print(f"✅ Ollama 可用，模型: {OLLAMA_MODEL}")
    else:
        print("⚠️ Ollama 未檢測到模型")
except Exception as e:
    print(f"⚠️ Ollama 不可用: {e}")
    print("⚠️ 僅支援純 RAG 模式")


# --------------------------------------------------------
# 工具函式：序列化檢索結果
# --------------------------------------------------------
def serialize_hit(rec: dict) -> dict:
    """統一整理單筆檢索結果"""
    if rec is None:
        return {}

    return {
        "id": rec.get("id") or rec.get("record_key"),
        "player_name": rec.get("player_name"),
        "season": rec.get("season"),
        "team": rec.get("team"),
        "type": rec.get("type"),
        "score": float(rec.get("score", 0.0)),
        "preview": (
            rec.get("raw_text")
            or rec.get("clean_text")
            or rec.get("embedding_text")
            or rec.get("keyword_text")
            or ""
        )[:400],
        "stats": rec.get("stats", {}),
    }


# --------------------------------------------------------
# 相容不同版本的 search 調用
# --------------------------------------------------------
def call_search_compatible(searcher, query, routed, topk):
    """
    相容不同版本的 HybridSearch.search() 方法
    
    嘗試順序：
    1. search(query, routed=routed, topk=topk) - 新版本
    2. search(query, routed, topk) - 位置參數版本
    3. search(query, routed) - 不支援 topk 的版本（使用預設值）
    """
    try:
        # 嘗試新版本（關鍵字參數）
        return searcher.search(query, routed=routed, topk=topk)
    except TypeError as e:
        if "topk" in str(e):
            try:
                # 嘗試位置參數版本
                return searcher.search(query, routed, topk)
            except TypeError:
                try:
                    # 嘗試不帶 topk 的版本
                    print(f"  ⚠️ HybridSearch.search() 不支援 topk 參數，使用預設值")
                    results = searcher.search(query, routed)
                    # 手動截取結果
                    if isinstance(results, list) and len(results) > topk:
                        return results[:topk]
                    return results
                except Exception as e2:
                    print(f"  ❌ Search 調用失敗: {e2}")
                    raise
        else:
            raise


# --------------------------------------------------------
# LLM 生成函式（使用本地 Ollama）
# --------------------------------------------------------
def generate_llm_response(query, routed, hits, history=None):
    """
    使用本地 Ollama 生成回答
    """
    if not OLLAMA_AVAILABLE:
        return "⚠️ LLM 模式需要 Ollama 運行。請確認 Ollama 服務已啟動。"
    
    try:
        import ollama
        
        # 準備 fact block
        fact_block = format_fact_block(hits) if hits else "No data found."
        
        # 根據查詢類型選擇 prompt
        qtype = routed.get("query_type", "factual")
        
        if qtype == "ranking":
            prompt = build_ranking_prompt(query, fact_block)
        elif qtype == "comparison":
            prompt = build_comparison_prompt(query, fact_block)
        else:
            prompt = build_factual_prompt(query, fact_block)
        
        # 構建訊息
        messages = []
        
        # 加入歷史對話
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 加入當前查詢
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # 呼叫 Ollama API
        print(f"🤖 使用 Ollama 模型: {OLLAMA_MODEL}")
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )
        
        return response['message']['content']
        
    except Exception as e:
        print(f"❌ LLM generation error: {e}")
        return f"⚠️ LLM 生成時發生錯誤：{str(e)}"


# --------------------------------------------------------
# 根目錄：前端單頁
# --------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(STATIC_DIR, INDEX_HTML)


# --------------------------------------------------------
# Router debug API
# --------------------------------------------------------
@app.route("/api/router", methods=["POST"])
def api_router():
    try:
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()

        if not query:
            return jsonify({"ok": False, "error": "query 不可為空"}), 400

        routed = router.route(query)
        return jsonify({"ok": True, "query": query, "routed": routed})
    
    except Exception as e:
        print(f"❌ Router error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# --------------------------------------------------------
# 主查詢 API
# --------------------------------------------------------
@app.route("/api/query", methods=["POST"])
def api_query():
    """
    主要查詢 API
    
    Request:
        {
            "query": "大谷 2023 投球",
            "mode": "rag" | "llm",
            "topk": 10,
            "history": [...]
        }
    
    Response:
        {
            "ok": true,
            "query": "...",
            "routed": {...},
            "classification": {...},
            "search_results": [...],
            "hits": [...],
            "answer": "..."
        }
    """
    try:
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        mode = data.get("mode", "rag")
        topk = int(data.get("topk", 10))
        history = data.get("history", [])

        if not query:
            return jsonify({"ok": False, "error": "query 不可為空"}), 400

        # 1) Query Router
        routed = router.route(query)
        qtype = routed.get("query_type")
        metric = routed.get("metric")
        top_n = routed.get("top_n") or topk

        print(f"\n📊 Query: {query}")
        print(f"   Type: {qtype}, Metric: {metric}, Mode: {mode}")

        # 2) 執行檢索（使用相容性包裝）
        normalized = routed.get("normalized_query") or query
        
        try:
            raw_hits = call_search_compatible(searcher, normalized, routed, top_n)
        except Exception as search_error:
            print(f"❌ Search error: {search_error}")
            import traceback
            traceback.print_exc()
            raw_hits = []

        # 轉換為前端格式
        hits = []
        for h in raw_hits:
            if isinstance(h, dict):
                hits.append(serialize_hit(h))
            elif isinstance(h, tuple) and len(h) >= 2:
                # (record_id, score, preview) 格式
                try:
                    rec = searcher.get_record(h[0]) if hasattr(searcher, 'get_record') else {}
                    if rec:
                        rec['score'] = h[1]
                        hits.append(serialize_hit(rec))
                except Exception as e:
                    print(f"  ⚠️ 無法序列化結果 {h[0]}: {e}")

        # 3) 處理結構化查詢
        structured = None
        
        if qtype == "ranking" and metric:
            try:
                season = routed["seasons"][0] if routed.get("seasons") else 2024
                ranking_results = lookup.rank(
                    season=season,
                    metric=metric,
                    top_n=top_n
                )
                structured = {
                    "kind": "ranking",
                    "metric": metric,
                    "season": season,
                    "results": [
                        {
                            "player": r[0]["player_name"],
                            "value": r[1],
                            "season": r[0]["season"],
                            "team": r[0]["team"]
                        }
                        for r in ranking_results
                    ]
                }
            except Exception as e:
                print(f"⚠️ Ranking error: {e}")

        elif qtype == "comparison" and metric and routed.get("players"):
            try:
                season = routed["seasons"][0] if routed.get("seasons") else 2024
                base_record = lookup.find_player_record(
                    routed["players"][0],
                    season
                )
                if base_record:
                    comp_results = lookup.find_relative_players(
                        base_record=base_record,
                        metric=metric,
                        season=season
                    )
                    structured = {
                        "kind": "comparison",
                        "metric": metric,
                        "baseline": routed["players"][0],
                        "season": season,
                        "results": [
                            {
                                "player": r[0]["player_name"],
                                "value": r[1],
                                "season": r[0]["season"],
                                "team": r[0]["team"]
                            }
                            for r in comp_results[:top_n]
                        ]
                    }
            except Exception as e:
                print(f"⚠️ Comparison error: {e}")

        # 4) 生成回答
        answer = ""
        
        if mode == "llm" and OLLAMA_AVAILABLE:
            # LLM 模式：使用本地 Ollama
            answer = generate_llm_response(query, routed, raw_hits, history)
        else:
            # RAG 模式：改進回答
            if structured:
                if structured["kind"] == "ranking":
                    answer = f"根據 {structured['metric']} 排名前 {len(structured['results'])} 名：\n"
                    for i, r in enumerate(structured['results'], 1):
                        answer += f"{i}. {r['player']} ({r['team']}) - {r['value']}\n"
                
                elif structured["kind"] == "comparison":
                    answer = f"在 {structured['metric']} 方面比 {structured['baseline']} 更好的球員有 {len(structured['results'])} 位。"
            
            elif hits:
                if len(hits) == 1:
                    # 單一結果：顯示詳細資訊
                    h = hits[0]
                    answer = f"找到 {h['player_name']} 在 {h['season']} 年的數據（{h['team']}）。\n\n"
                    
                    # 顯示關鍵統計
                    stats = h.get('stats', {})
                    if stats:
                        if h.get('type') == 'pitcher':
                            # 投手關鍵數據
                            answer += f"投球表現：\n"
                            if 'ERA' in stats:
                                answer += f"- 防禦率 (ERA): {stats['ERA']}\n"
                            if 'WHIP' in stats:
                                answer += f"- WHIP: {stats['WHIP']}\n"
                            if 'K%' in stats:
                                answer += f"- 三振率 (K%): {stats['K%']}\n"
                            if 'FIP' in stats:
                                answer += f"- FIP: {stats['FIP']}\n"
                        else:
                            # 打者關鍵數據
                            answer += f"打擊表現：\n"
                            if 'AVG' in stats:
                                answer += f"- 打擊率 (AVG): {stats['AVG']}\n"
                            if 'HR' in stats:
                                answer += f"- 全壘打 (HR): {stats['HR']}\n"
                            if 'OPS' in stats:
                                answer += f"- OPS: {stats['OPS']}\n"
                            if 'wRC+' in stats:
                                answer += f"- wRC+: {stats['wRC+']}\n"
                elif len(hits) <= 3:
                    # 少量結果：顯示所有球員名稱
                    answer = f"找到 {len(hits)} 筆相關數據：\n\n"
                    for i, h in enumerate(hits, 1):
                        answer += f"{i}. {h['player_name']} ({h['season']} {h['team']}) - {h['type']}\n"
                else:
                    # 多筆結果：顯示前 3 名
                    answer = f"找到 {len(hits)} 筆相關數據。前 3 名最相關的結果：\n\n"
                    for i, h in enumerate(hits[:3], 1):
                        answer += f"{i}. {h['player_name']} ({h['season']} {h['team']}) - {h['type']}"
                        
                        # 顯示一個關鍵指標
                        stats = h.get('stats', {})
                        if stats:
                            if h.get('type') == 'pitcher' and 'ERA' in stats:
                                answer += f" | ERA: {stats['ERA']}"
                            elif 'HR' in stats:
                                answer += f" | HR: {stats['HR']}"
                            elif 'OPS' in stats:
                                answer += f" | OPS: {stats['OPS']}"
                        answer += "\n"
                    
                    answer += f"\n（共 {len(hits)} 筆結果，請展開「檢索來源」查看完整資料）"
            else:
                answer = "沒有找到相關數據，請嘗試不同的查詢。"

        # 5) 回傳結果
        response = {
            "ok": True,
            "query": query,
            "routed": routed,
            "classification": routed,
            "mode": qtype,
            "search_results": hits,
            "hits": hits,
            "structured": structured,
            "answer": answer,
        }

        return jsonify(response)

    except Exception as e:
        import traceback
        print(f"❌ API Error: {e}")
        print(traceback.format_exc())
        return jsonify({"ok": False, "error": str(e)}), 500


# --------------------------------------------------------
# 健康檢查
# --------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "ok": True,
        "status": "ready",
        "llm_available": OLLAMA_AVAILABLE,
        "llm_model": OLLAMA_MODEL if OLLAMA_AVAILABLE else None
    })


# --------------------------------------------------------
# 錯誤處理
# --------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"ok": False, "error": "Not Found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"ok": False, "error": "Internal Server Error"}), 500


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MLB Team Manager Assistant API Server")
    print("="*60)
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"🌐 Static Files: {STATIC_DIR}")
    print(f"🤖 Ollama Available: {OLLAMA_AVAILABLE}")
    if OLLAMA_AVAILABLE:
        print(f"🤖 Ollama Model: {OLLAMA_MODEL}")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=8000, debug=True)
