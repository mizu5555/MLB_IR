import sys
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../..')
sys.path.insert(0, project_root)

try:
    from src.retrieval.query_router import QueryRouter
    from src.retrieval.hybrid_search import HybridSearch
    from src.retrieval.lookup_engine import LookupEngine
    from src.generation.prompt_templates import (
        format_fact_block,
        build_factual_prompt,
        build_comparison_prompt,
        build_ranking_prompt,
    )
    LLM_AVAILABLE = True
    print("✅ 成功載入模組")
except ImportError as e:
    print(f"⚠️ 模組載入失敗: {e}")
    LLM_AVAILABLE = False

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

print("🔧 初始化檢索系統...")
router = QueryRouter()
searcher = HybridSearch()
lookup = LookupEngine()
print("✅ 檢索系統初始化完成")

STATIC_DIR = os.path.join(current_dir, "static")

# Ollama
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
        print(f"✅ Ollama 可用: {OLLAMA_MODEL}")
except:
    print("⚠️ Ollama 不可用")

def serialize_hit(rec: dict, idx: int) -> dict:
    """序列化檢索結果 - 完整 stats debug"""
    if rec is None:
        return {}
    
    stats = rec.get("stats", {})
    
    result = {
        "id": rec.get("record_key") or rec.get("id"),
        "record_key": rec.get("record_key") or rec.get("id"),
        "player_name": rec.get("player_name"),
        "player_id": rec.get("player_id"),
        "season": rec.get("season"),
        "team": rec.get("team"),
        "type": rec.get("type"),
        "score": float(rec.get("score", 0.0)),
        "preview": (rec.get("raw_text") or rec.get("clean_text") or rec.get("embedding_text") or "")[:400],
        "stats": stats,
    }
    
    # ⭐ 完整 stats debug
    stats_keys = list(stats.keys())
    print(f"   序列化 {idx+1}: {result['player_name']} {result['season']} {result['type']} "
          f"score={result['score']:.4f}")
    print(f"      → stats 包含 {len(stats_keys)} 個欄位: {stats_keys[:10]}{'...' if len(stats_keys) > 10 else ''}")
    
    return result

def generate_llm_response(query, routed, hits, history=None):
    if not OLLAMA_AVAILABLE:
        return "⚠️ LLM 需要 Ollama"
    try:
        import ollama
        fact_block = format_fact_block(hits) if hits else "No data"
        qtype = routed.get("query_type", "factual")
        if qtype == "ranking":
            prompt = build_ranking_prompt(query, fact_block)
        elif qtype == "comparison":
            prompt = build_comparison_prompt(query, fact_block)
        else:
            prompt = build_factual_prompt(query, fact_block)
        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        return response['message']['content']
    except Exception as e:
        return f"⚠️ LLM 錯誤：{str(e)}"

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "ok": True,
        "status": "ready",
        "llm_available": OLLAMA_AVAILABLE,
        "llm_model": OLLAMA_MODEL if OLLAMA_AVAILABLE else None
    })

@app.route("/api/query", methods=["POST"])
def api_query():
    try:
        data = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        mode = data.get("mode", "rag")
        topk = int(data.get("topk", 5))
        history = data.get("history", [])

        if not query:
            return jsonify({"ok": False, "error": "query 不可為空"}), 400

        # 1) Query Router
        routed = router.route(query)
        qtype = routed.get("query_type")
        metric = routed.get("metric")
        top_n = routed.get("top_n") or topk

        print(f"\n{'='*60}")
        print(f"📊 Query: {query}")
        print(f"   Type: {qtype}, Metric: {metric}, Mode: {mode}, TopK: {top_n}")

        # 2) Hybrid Search - ⭐ 正確傳遞參數
        normalized = routed.get("normalized_query") or query
        
        try:
            raw_hits = searcher.search(
                normalized,
                routed=routed,
                k=top_n,
                filter_players=routed.get("players"),      # ⭐ 明確傳遞
                filter_seasons=routed.get("seasons"),      # ⭐ 明確傳遞
                boost_type=routed.get("type_boost")        # ⭐ 關鍵！
            )
            print(f"\n🔍 HybridSearch 返回 {len(raw_hits)} 筆結果:")
            for i, h in enumerate(raw_hits[:5]):
                print(f"   {i+1}. {h.get('player_name')} {h.get('season')} {h.get('type')} "
                      f"score={h.get('score', 0):.4f}")
        except Exception as e:
            print(f"❌ Search 錯誤: {e}")
            import traceback
            traceback.print_exc()
            raw_hits = []

        # 3) 序列化
        print(f"\n🔄 開始序列化 {len(raw_hits)} 筆結果:")
        hits = []
        for i, h in enumerate(raw_hits):
            if isinstance(h, dict):
                serialized = serialize_hit(h, i)
                hits.append(serialized)

        print(f"\n✅ 序列化完成: {len(hits)} 筆")
        print(f"   前3名: {[(h['player_name'], h['type'], h['score']) for h in hits[:3]]}")

        # 4) 生成回答
        answer = ""
        structured = None
        
        if mode == "llm" and OLLAMA_AVAILABLE:
            answer = generate_llm_response(query, routed, raw_hits, history)
        else:
            # RAG 模式
            if hits:
                if len(hits) == 1:
                    h = hits[0]
                    answer = f"找到 {h['player_name']} 在 {h['season']} 年的數據（{h['team']}）。\n\n"
                    stats = h.get('stats', {})
                    if stats:
                        if h.get('type') == 'pitcher':
                            answer += "投球表現：\n"
                            for key in ['ERA', 'WHIP', 'K%', 'FIP']:
                                if key in stats:
                                    answer += f"- {key}: {stats[key]}\n"
                        else:
                            answer += "打擊表現：\n"
                            for key in ['AVG', 'HR', 'OPS', 'wRC+']:
                                if key in stats:
                                    answer += f"- {key}: {stats[key]}\n"
                
                elif len(hits) <= 3:
                    answer = f"找到 {len(hits)} 筆相關數據：\n\n"
                    for i, h in enumerate(hits, 1):
                        answer += f"{i}. {h['player_name']} ({h['season']} {h['team']}) - {h['type']}\n"
                        stats = h.get('stats', {})
                        if stats:
                            key_stats = []
                            if h.get('type') == 'pitcher':
                                for k in ['ERA', 'WHIP', 'K%']:
                                    if k in stats:
                                        key_stats.append(f"{k}: {stats[k]}")
                            else:
                                for k in ['AVG', 'HR', 'OPS']:
                                    if k in stats:
                                        key_stats.append(f"{k}: {stats[k]}")
                            if key_stats:
                                answer += f"   {' | '.join(key_stats)}\n"
                
                else:
                    answer = f"找到 {len(hits)} 筆相關數據。前 {min(3, len(hits))} 名最相關的結果：\n\n"
                    for i, h in enumerate(hits[:3], 1):
                        answer += f"{i}. {h['player_name']} ({h['season']} {h['team']}) - {h['type']}"
                        stats = h.get('stats', {})
                        if stats:
                            if h.get('type') == 'pitcher' and 'ERA' in stats:
                                answer += f" | ERA: {stats['ERA']}"
                            elif 'HR' in stats:
                                answer += f" | HR: {stats['HR']}"
                        answer += "\n"
                    answer += f"\n（共 {len(hits)} 筆結果，請展開「檢索來源」查看完整資料）"
            else:
                answer = "沒有找到相關數據"

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

        print(f"\n✅ 返回 {len(hits)} 筆結果給前端")
        print(f"{'='*60}\n")

        return jsonify(response)

    except Exception as e:
        import traceback
        print(f"❌ API 錯誤: {e}")
        print(traceback.format_exc())
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MLB Team Manager Assistant")
    print("="*60)
    print(f"🤖 Ollama: {OLLAMA_AVAILABLE}")
    if OLLAMA_AVAILABLE:
        print(f"🤖 Model: {OLLAMA_MODEL}")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=8000, debug=True)