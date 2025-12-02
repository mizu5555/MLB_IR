import sys
import os
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path

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
    # ⭐ 導入統計選擇配置
    from stat_selection_config import (
        select_stats_for_comparison, 
        get_stat_description,
        is_lower_better
    )
    
    LLM_AVAILABLE = True
    print("✅ 成功載入模組")
except ImportError as e:
    print(f"⚠️ 模組載入失敗: {e}")
    LLM_AVAILABLE = False
    # 如果配置文件載入失敗，使用預設函數
    def select_stats_for_comparison(routed, common_type):
        if common_type == "pitcher":
            return ["ERA", "WHIP", "K%", "FIP"]
        else:
            return ["AVG", "HR", "OPS", "wRC+"]
    
    def get_stat_description(stat_key):
        return stat_key
    
    def is_lower_better(stat_key):
        return stat_key in ["ERA", "WHIP", "FIP", "K%", "BB%"]

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

print("🔧 初始化檢索系統...")
router = QueryRouter()
searcher = HybridSearch()
lookup = LookupEngine()
print("✅ 檢索系統初始化完成")

STATIC_DIR = os.path.join(current_dir, "static")
METRICS_FILE = Path(project_root) / "results" / "metrics_log.jsonl"

# 全局變量：存儲評估指標
query_metrics = []

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

def calculate_metrics(results, routed, k=5):
    """
    計算檢索評估指標
    
    相關性判斷標準：
    - 如果查詢指定了 players，則結果必須包含這些 players
    - 如果查詢指定了 seasons，則結果必須包含這些 seasons
    """
    if not results:
        return {
            "recall@k": 0.0,
            "precision@k": 0.0,
            "mrr": 0.0,
            "relevant_count": 0,
            "total_retrieved": 0,
            "k": k  # ⭐ 修正：加入 k 鍵
        }
    
    filter_players = routed.get("players", [])
    filter_seasons = routed.get("seasons", [])
    
    # 判斷每個結果是否相關
    relevant_results = []
    for i, r in enumerate(results[:k]):
        is_relevant = True
        
        # 檢查球員匹配
        if filter_players:
            player_name = r.get("player_name", "").lower()
            if not any(p.lower() in player_name for p in filter_players):
                is_relevant = False
        
        # 檢查年度匹配
        if filter_seasons:
            season = r.get("season")
            if season not in filter_seasons:
                is_relevant = False
        
        if is_relevant:
            relevant_results.append((i + 1, r))  # (rank, result)
    
    # 計算指標
    relevant_count = len(relevant_results)
    total_retrieved = min(len(results), k)
    
    # Precision@k: 前 k 個中相關的比例
    precision_at_k = relevant_count / total_retrieved if total_retrieved > 0 else 0.0
    
    # Recall@k: 這裡假設相關文檔總數 = 我們找到的相關文檔
    # （實際應用中需要 ground truth）
    recall_at_k = 1.0 if relevant_count > 0 else 0.0
    
    # MRR: 第一個相關結果的排名倒數
    mrr = 0.0
    if relevant_results:
        first_rank = relevant_results[0][0]
        mrr = 1.0 / first_rank
    
    return {
        "recall@k": recall_at_k,
        "precision@k": precision_at_k,
        "mrr": mrr,
        "relevant_count": relevant_count,
        "total_retrieved": total_retrieved,
        "k": k
    }

def serialize_hit(rec: dict, idx: int) -> dict:
    """序列化檢索結果"""
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
    
    stats_keys = list(stats.keys())
    print(f"   序列化 {idx+1}: {result['player_name']} {result['season']} {result['type']} "
          f"score={result['score']:.4f}")
    print(f"      → stats 包含 {len(stats_keys)} 個欄位: {stats_keys[:10]}{'...' if len(stats_keys) > 10 else ''}")
    
    return result

def generate_rag_answer(query, hits, routed):
    """
    生成 RAG 回答（改進版 - 選項 A：直接比較式）
    """
    if not hits:
        return "沒有找到相關數據。"
    
    qtype = routed.get("query_type", "factual")
    players = routed.get("players", [])
    metric = routed.get("metric")
    
    # 比較查詢（2+ 球員）
    if len(players) >= 2 and len(hits) >= 2:
        # 按球員分組
        player_data = {}
        for h in hits:
            pname = h.get("player_name")
            if pname not in player_data:
                player_data[pname] = []
            player_data[pname].append(h)
        
        # 只保留查詢中的球員
        player_data = {p: data for p, data in player_data.items() if any(p.lower() in query_p.lower() or query_p.lower() in p.lower() for query_p in players)}
        
        if len(player_data) >= 2:
            # 生成比較式回答
            # ⭐ 修正：先檢查 hits 是否為空，再訪問 hits[0]
            if not hits:
                return "沒有找到相關數據。"
            
            season = routed.get("seasons", [None])[0] if routed.get("seasons") else hits[0].get("season", "")
            answer = f"{season} 年數據比較：\n\n"
            
            # 找出相同類型的數據（都是打者或都是投手）
            common_type = hits[0].get("type")
            comparisons = []
            
            for pname, data_list in player_data.items():
                # 找到匹配類型的數據
                matching = [d for d in data_list if d.get("type") == common_type]
                if matching:
                    d = matching[0]
                    stats = d.get("stats", {})
                    comparisons.append({
                        "name": pname,
                        "team": d.get("team"),
                        "type": d.get("type"),
                        "stats": stats
                    })
            
            if len(comparisons) >= 2:
                # ⭐ 使用智能統計選擇
                print(f"\n   🎯 智能選擇統計數據:")
                print(f"      查詢: {query}")
                print(f"      Metric: {routed.get('metric')}")
                print(f"      類型: {common_type}")
                
                key_stats = select_stats_for_comparison(routed, common_type)
                print(f"      選擇: {key_stats}")
                
                # 生成比較文字
                p1, p2 = comparisons[0], comparisons[1]
                
                for stat in key_stats:
                    val1 = p1["stats"].get(stat)
                    val2 = p2["stats"].get(stat)
                    
                    if val1 is not None and val2 is not None:
                        try:
                            val1 = float(val1)
                            val2 = float(val2)
                            
                            # ⭐ 使用配置函數判斷高低
                            lower_is_better = is_lower_better(stat)
                            
                            if lower_is_better:
                                if val1 < val2:
                                    answer += f"{stat}：{p1['name']} {val1} < {p2['name']} {val2}（{p1['name']} 較佳）\n"
                                elif val1 > val2:
                                    answer += f"{stat}：{p1['name']} {val1} > {p2['name']} {val2}（{p2['name']} 較佳）\n"
                                else:
                                    answer += f"{stat}：{p1['name']} {val1} = {p2['name']} {val2}\n"
                            else:
                                if val1 > val2:
                                    answer += f"{stat}：{p1['name']} {val1} > {p2['name']} {val2}（{p1['name']} 較佳）\n"
                                elif val1 < val2:
                                    answer += f"{stat}：{p1['name']} {val1} < {p2['name']} {val2}（{p2['name']} 較佳）\n"
                                else:
                                    answer += f"{stat}：{p1['name']} {val1} = {p2['name']} {val2}\n"
                        except:
                            pass
                
                answer += f"\n詳細數據可以參考下方「原始數據來源」。"
                return answer
    
    # 單一查詢
    if len(hits) == 1:
        h = hits[0]
        answer = f"找到 {h['player_name']} 在 {h['season']} 年的數據（{h['team']}）。\n\n"
        stats = h.get('stats', {})
        
        if stats:
            # ⭐ 使用智能統計選擇
            player_type = h.get('type', 'batter')
            print(f"\n   🎯 智能選擇統計數據 (單一查詢):")
            print(f"      查詢: {query}")
            print(f"      Metric: {routed.get('metric')}")
            print(f"      類型: {player_type}")
            
            key_stats = select_stats_for_comparison(routed, player_type)
            print(f"      選擇: {key_stats}")
            
            if player_type == 'pitcher':
                answer += "投球表現：\n"
            else:
                answer += "打擊表現：\n"
            
            for key in key_stats:
                if key in stats:
                    answer += f"- {key}: {stats[key]}\n"
        
        answer += "\n詳細數據可以參考下方「原始數據來源」。"
        return answer
    
    # 多筆結果（列表式）
    elif len(hits) <= 3:
        answer = f"找到 {len(hits)} 筆相關數據：\n\n"
        
        for i, h in enumerate(hits, 1):
            answer += f"{i}. {h['player_name']} ({h['season']} {h['team']}) - {h['type']}\n"
            stats = h.get('stats', {})
            
            if stats:
                # ⭐ 使用智能統計選擇（只在第一筆時打印日誌）
                player_type = h.get('type', 'batter')
                if i == 1:
                    print(f"\n   🎯 智能選擇統計數據 (多筆結果):")
                    print(f"      查詢: {query}")
                    print(f"      Metric: {routed.get('metric')}")
                    print(f"      類型: {player_type}")
                    key_stats = select_stats_for_comparison(routed, player_type)
                    print(f"      選擇: {key_stats}")
                else:
                    # 後續使用相同類型的統計選擇
                    key_stats = select_stats_for_comparison(routed, player_type)
                
                key_stats_values = []
                for k in key_stats[:3]:  # 顯示前3個
                    if k in stats:
                        key_stats_values.append(f"{k}: {stats[k]}")
                
                if key_stats_values:
                    answer += f"   {' | '.join(key_stats_values)}\n"
        
        answer += "\n詳細數據可以參考下方「原始數據來源」。"
        return answer
    
    else:
        answer = f"找到 {len(hits)} 筆相關數據。前 {min(3, len(hits))} 名最相關的結果：\n\n"
        
        for i, h in enumerate(hits[:3], 1):
            answer += f"{i}. {h['player_name']} ({h['season']} {h['team']}) - {h['type']}"
            stats = h.get('stats', {})
            
            if stats:
                # ⭐ 使用智能統計選擇（只在第一筆時打印日誌）
                player_type = h.get('type', 'batter')
                if i == 1:
                    print(f"\n   🎯 智能選擇統計數據 (多筆結果):")
                    print(f"      查詢: {query}")
                    print(f"      Metric: {routed.get('metric')}")
                    print(f"      類型: {player_type}")
                    key_stats = select_stats_for_comparison(routed, player_type)
                    print(f"      選擇: {key_stats}")
                else:
                    key_stats = select_stats_for_comparison(routed, player_type)
                
                # 顯示第一個統計
                if key_stats and key_stats[0] in stats:
                    answer += f" | {key_stats[0]}: {stats[key_stats[0]]}"
            
            answer += "\n"
        
        answer += f"\n（共 {len(hits)} 筆結果）\n詳細數據可以參考下方「原始數據來源」。"
        return answer

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

        start_time = time.time()

        # 1) Query Router
        routed = router.route(query)
        qtype = routed.get("query_type")
        metric = routed.get("metric")
        top_n = routed.get("top_n") or topk

        print(f"\n{'='*60}")
        print(f"📊 Query: {query}")
        print(f"   Type: {qtype}, Metric: {metric}, Mode: {mode}, TopK: {top_n}")

        # 2) Hybrid Search
        normalized = routed.get("normalized_query") or query
        
        try:
            raw_hits = searcher.search(
                normalized,
                routed=routed,
                k=top_n,
                filter_players=routed.get("players"),
                filter_seasons=routed.get("seasons"),
                boost_type=routed.get("type_boost")
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

        # 3) 計算評估指標
        metrics = calculate_metrics(raw_hits, routed, k=top_n)
        
        print(f"\n📊 檢索評估指標:")
        print(f"   Recall@{metrics['k']}: {metrics['recall@k']:.1%}")
        print(f"   Precision@{metrics['k']}: {metrics['precision@k']:.1%}")
        print(f"   MRR: {metrics['mrr']:.3f}")
        print(f"   相關文檔: {metrics['relevant_count']}/{metrics['total_retrieved']}")

        # 4) 序列化
        print(f"\n🔄 開始序列化 {len(raw_hits)} 筆結果:")
        hits = []
        for i, h in enumerate(raw_hits):
            if isinstance(h, dict):
                serialized = serialize_hit(h, i)
                hits.append(serialized)

        print(f"\n✅ 序列化完成: {len(hits)} 筆")

        # 5) 生成回答
        answer = ""
        structured = None
        
        if mode == "llm" and OLLAMA_AVAILABLE:
            answer = generate_llm_response(query, routed, raw_hits, history)
        else:
            # RAG 模式 - 使用改進的回答生成
            answer = generate_rag_answer(query, hits, routed)

        elapsed_time = time.time() - start_time

        # 6) 記錄指標
        query_log = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "mode": mode,
            "query_type": qtype,
            "metrics": metrics,
            "response_time": elapsed_time,
            "results_count": len(hits)
        }
        query_metrics.append(query_log)
        
        # 寫入檔案
        try:
            METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(METRICS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(query_log, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ 寫入 metrics 檔案失敗: {e}")

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
            "metrics": metrics,  # ⭐ 回傳給前端
        }

        print(f"\n✅ 返回 {len(hits)} 筆結果給前端")
        print(f"⏱️  響應時間: {elapsed_time:.2f}s")
        print(f"{'='*60}\n")

        return jsonify(response)

    except Exception as e:
        import traceback
        print(f"❌ API 錯誤: {e}")
        print(traceback.format_exc())
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/metrics", methods=["GET"])
def api_metrics():
    """
    獨立 API：返回累積的評估指標
    """
    if not query_metrics:
        return jsonify({
            "ok": True,
            "message": "尚無查詢記錄",
            "total_queries": 0
        })
    
    # 計算平均指標
    total = len(query_metrics)
    avg_recall = sum(m["metrics"]["recall@k"] for m in query_metrics) / total
    avg_precision = sum(m["metrics"]["precision@k"] for m in query_metrics) / total
    avg_mrr = sum(m["metrics"]["mrr"] for m in query_metrics) / total
    avg_response_time = sum(m["response_time"] for m in query_metrics) / total
    
    return jsonify({
        "ok": True,
        "total_queries": total,
        "average_metrics": {
            "recall@k": round(avg_recall, 4),
            "precision@k": round(avg_precision, 4),
            "mrr": round(avg_mrr, 4),
            "avg_response_time": round(avg_response_time, 3)
        },
        "recent_queries": query_metrics[-10:],  # 最近 10 筆
        "metrics_file": str(METRICS_FILE)
    })

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 MLB Team Manager Assistant")
    print("="*60)
    print(f"🤖 Ollama: {OLLAMA_AVAILABLE}")
    if OLLAMA_AVAILABLE:
        print(f"🤖 Model: {OLLAMA_MODEL}")
    print(f"📊 Metrics 記錄: {METRICS_FILE}")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=8000, debug=True)