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
    from src.web.stat_selection_config import (
        select_stats_for_comparison, 
        get_stat_description,
        is_lower_better,
        detect_problem_type, 
        get_analysis_stats,
    )

    LLM_AVAILABLE = True

except ImportError as e:
    print(f"⚠️ 模組載入失敗: {e}")
    LLM_AVAILABLE = False
    # 如果配置文件載入失敗，使用預設函數
    def select_stats_for_comparison(routed, common_type):
        if common_type == "pitcher":
            return ["ERA", "WHIP", "K%", "FIP"]
        else:
            return ["AVG", "HR", "OPS", "wRC+"]

try:
    from answer_templates import (
        format_factual_answer,
        format_ranking_answer,
        format_comparison_answer,
        #extract_comparison_data,
        #extract_ranking_data
    )
    TEMPLATES_AVAILABLE = True

except ImportError as e:
    print(f"⚠️ answer_templates 載入失敗: {e}")
    TEMPLATES_AVAILABLE = False
    
    def get_stat_description(stat_key):
        return stat_key
    
    def is_lower_better(stat_key):
        return stat_key in ["ERA", "WHIP", "FIP", "K%", "BB%"]

from src.generation.llm_analysis_engine import AnalysisLLMEngine, get_league_averages
from src.evaluation.fact_checker import FactChecker

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

print("🔧 初始化檢索系統...")
router = QueryRouter()
searcher = HybridSearch()
lookup = LookupEngine()

"""print("🔄 Syncing stats from HybridSearch to LookupEngine...")
hybrid_map = {rec["record_key"]: rec["stats"] for rec in searcher.records}

cnt = 0
for rec in lookup.data:
    key = rec.get("record_key")
    if key in hybrid_map:
        rec["stats"] = hybrid_map[key]
        cnt += 1
print(f"✅ Stats Sync 完成，共更新 {cnt} 筆資料")"""

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

def choose_role_for_metric(metric, intent, hits):
    """根據 metric 和 intent 選擇二刀流角色"""
    metric = metric.upper()

    pitcher_only = {"ERA", "WHIP", "FIP", "XFIP", "SIERA", "K/9", "BB/9", "H/9", "HR/9", "IP", "TBF"}
    batter_only = {"AVG", "OBP", "SLG", "OPS", "OPS+", "ISO", "BABIP", "WOBA", "WRC", "WRC+"}
    overlap = {"SO", "K", "K%", "BB", "BB%", "CS", "SB", "HARDHIT%", "BARREL%"}

    # 1. Only-pitcher metrics
    if metric in pitcher_only:
        return [h for h in hits if h["type"] == "pitcher"]

    # 2. Only-batter metrics
    if metric in batter_only:
        return [h for h in hits if h["type"] == "batter"]

    # 3. Overlap metrics → intent first
    if metric in overlap and intent:
        if intent == "pitching":
            pit = [h for h in hits if h["type"] == "pitcher"]
            if pit: return pit

        if intent == "batting":
            bat = [h for h in hits if h["type"] == "batter"]
            if bat: return bat

    bat_hits = [h for h in hits if h["type"] == "batter"]
    pit_hits = [h for h in hits if h["type"] == "pitcher"]

    # Case A：全部都是打者
    if bat_hits and not pit_hits:
        return bat_hits

    # Case B：全部都是投手
    if pit_hits and not bat_hits:
        return pit_hits

    # Case C：混合 → 語義偏好
    batter_lean = {"BB%", "K%", "OBP", "SLG", "OPS", "ISO"}
    pitcher_lean = {"SO", "K", "K%", "H/9", "HR/9"}

    if metric in batter_lean and bat_hits:
        return bat_hits

    if metric in pitcher_lean and pit_hits:
        return pit_hits

    # Final fallback: batter > pitcher
    if bat_hits:
        return bat_hits
    if pit_hits:
        return pit_hits

    return hits

def generate_rag_answer(query, hits, routed):
    """
    根據 Query Type 生成結構化回答
    
    v6.0.4 修正：
    1. Ranking 查詢直接用 lookup_engine.rank()，不依賴 hybrid_search
    2. 保留其他查詢類型的邏輯
    """
    from answer_templates import (
        format_factual_answer,
        format_ranking_answer,
        format_comparison_answer,
        format_analysis_answer,
        is_valid_value,
        get_metric_name,
    )
    from stat_selection_config import detect_problem_type, get_analysis_stats
    
    qtype = routed.get("query_type", "factual")
    metric = routed.get("metric")
    players = routed.get("players", [])
    seasons = routed.get("seasons", [])
    intent = routed.get("intent")

    # ============================================================
    # 0. Analysis Query（分析查詢）
    # ============================================================
    
    if qtype == "analysis":
        if not hits:
            return "沒有找到相關數據進行分析。"
        
        # 取第一筆最相關的結果
        hit = hits[0]
        player_name = hit.get("player_name")
        season = hit.get("season")
        player_type = hit.get("type")
        
        # 識別問題類型
        problem_type = detect_problem_type(query)
        
        if not problem_type:            
            if player_type == "pitcher":
                # 投手的建議範例
                return f"無法識別具體問題類型。{player_name} 是投手，請嘗試更明確的描述：\n\n" \
                       f"**投手分析範例**：\n" \
                       f"- 「{player_name} 的控球為什麼這麼差」\n" \
                       f"- 「{player_name} 的壓制力為什麼下降」\n" \
                       f"- 「{player_name} 為什麼防禦率這麼高」\n" \
                       f"- 「{player_name} 為什麼容易被長打」\n" \
                       f"- 「{player_name} 為什麼三振率下降」"
            
            else:  # batter
                # 打者的建議範例
                return f"無法識別具體問題類型。{player_name} 是打者，請嘗試更明確的描述：\n\n" \
                       f"**打者分析範例**：\n" \
                       f"- 「{player_name} 的打擊率為什麼這麼低」\n" \
                       f"- 「{player_name} 的長打力為什麼不足」\n" \
                       f"- 「{player_name} 為什麼三振這麼多」\n" \
                       f"- 「{player_name} 的選球為什麼這麼差」\n" \
                       f"- 「{player_name} 最近為什麼狀態低迷」"
        
        # 獲取聯盟平均數據（未來可擴展）
        league_avg_data = None
        
        # 生成分析報告
        return format_analysis_answer(
            player_name=player_name,
            season=season,
            problem_type=problem_type,
            player_data=hit,
            league_avg_data=league_avg_data,
            player_type=player_type
        )
    
    # ============================================================
    # 1. Factual Query（單一數據查詢）
    # ============================================================
    elif qtype == "factual":
        if not hits:
            return "沒有找到相關數據。"
        
        # 取第一筆最相關的結果
        hit = hits[0]
        player_name = hit.get("player_name")
        season = hit.get("season")
        team = hit.get("team")
        player_type = hit.get("type")
        stats = hit.get("stats", {})
        
        # 檢查 metric 是否存在
        if metric:
            value = stats.get(metric)
            
            # 使用 answer_templates 的 format_factual_answer()
            return format_factual_answer(
                player_name=player_name,
                season=season,
                metric=metric,
                value=value,
                related_stats=stats,
                team=team,
                player_type=player_type
            )
        
        # 如果沒有指定 metric，顯示完整數據
        else:
            player_type_zh = "投手" if player_type == "pitcher" else "打者"
            answer = f"{player_name} 在 {season} 年（{team}）的 {player_type_zh} 數據：\n\n"
            
            # 顯示關鍵統計
            if player_type == "pitcher":
                key_stats = ["ERA", "WHIP", "K/9", "BB/9", "FIP", "IP", "W", "L"]
            else:
                key_stats = ["AVG", "OBP", "SLG", "OPS", "HR", "RBI", "wRC+"]
            
            for key in key_stats:
                if key in stats and is_valid_value(stats[key]):
                    metric_name = get_metric_name(key, player_type)
                    from answer_templates import format_value
                    formatted = format_value(stats[key], key)
                    answer += f"- {metric_name}: {formatted}\n"
            
            return answer
    
    # ============================================================
    # 2. Ranking Query（排名查詢
    # ============================================================
    elif qtype == "ranking":
        # 直接用 lookup_engine.rank() 
        # 不要依賴 hybrid_search 的結果
        if not metric:
            return "沒有指定排名指標。"
        
        season = seasons[0] if seasons else None
        if not season:
            return "沒有指定年份。"
        
        top_n = routed.get("top_n", 10)
        
        # 這個函數會返回「數據前 N」的球員，而不是「相似度前 N」
        lookup = LookupEngine()
        
        # rank() 返回 [(record, value), ...]
        ranking_results = lookup.rank(
            season=season,
            metric=metric,
            top_n=top_n,
            ptype=intent  # pitcher / batter
        )
 
        if not ranking_results:
            return f"沒有找到 {season} 年 {metric} 的數據。"
        
        # 轉換為 format_ranking_answer() 需要的格式
        rankings = []
        for rec, val in ranking_results:
            rankings.append({
                "player": rec.get("player_name"),
                "team": rec.get("team"),
                "value": val,
            })
        
        # 使用 answer_templates 的 format_ranking_answer()
        player_type = ranking_results[0][0].get("type") if ranking_results else None
        return format_ranking_answer(
            season=season,
            metric=metric,
            rankings=rankings,
            player_type=player_type,
        )
    
    # ============================================================
    # 3. Comparison Query（比較查詢）
    # ============================================================
    elif qtype == "comparison":
        if not hits or not metric:
            return "沒有找到相關數據。"
        
        # 判斷比較類型
        if len(players) >= 2 and len(seasons) <= 1:
            # 多球員比較（同一年份）
            comparison_type = "multi_player"
            season = seasons[0] if seasons else None
        elif len(players) == 1 and len(seasons) >= 2:
            # 單球員多賽季比較
            comparison_type = "multi_season"
            season = None
        else:
            # 預設：多球員比較
            comparison_type = "multi_player"
            season = seasons[0] if seasons else None
        
        # 從 hits 中提取比較數據
        comparisons = []
        hits = choose_role_for_metric(metric, routed.get("intent"), hits)
        for hit in hits:
            player_name = hit.get("player_name")
            hit_season = hit.get("season")
            team = hit.get("team")
            player_type = hit.get("type")
            stats = hit.get("stats", {})
            value = stats.get(metric)
            
            # 過濾 N/A 值
            if not is_valid_value(value):
                continue
            
            comparisons.append({
                "player": player_name,
                "season": hit_season,
                "team": team,
                "value": value
            })
        
        # 如果沒有有效數據
        if not comparisons:
            if season:
                return f"沒有找到 {season} 年有效的數據進行比較。"
            else:
                return f"沒有找到有效的數據進行比較。可能這些球員在指定年份沒有該類型的出賽記錄。"
        
        # 使用 answer_templates 的 format_comparison_answer()
        player_type = hits[0].get("type") if hits else None
        return format_comparison_answer(
            metric=metric,
            comparisons=comparisons,
            season=season,
            comparison_type=comparison_type,
            player_type=player_type
        )
      
    # ============================================================
    # 預設：顯示前幾筆結果
    # ============================================================
    else:
        if not hits:
            return "沒有找到相關數據。"
        
        answer = f"找到 {len(hits)} 筆相關數據：\n\n"
        for i, hit in enumerate(hits[:5], 1):
            player_name = hit.get("player_name")
            season = hit.get("season")
            team = hit.get("team")
            player_type = hit.get("type")
            
            answer += f"{i}. {player_name} ({season} {team}) - {player_type}\n"
        
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
        seasons = routed.get("seasons", [])
        top_n = routed.get("top_n") or topk

        print(f"\n{'='*60}")
        print(f"📊 Query: {query}")
        print(f"   Type: {qtype}, Metric: {metric}, Mode: {mode}, TopK: {top_n}")


        # ============================================================
        # Ranking Query（stats 排名，不用 hybrid）
        # ============================================================
        if qtype == "ranking" and metric:
            if not seasons:
                return jsonify({"ok": False, "error": "需要指定年份"}), 400

            season = seasons[0]
            print(f"   🎯 Ranking Query → season={season}, metric={metric}")
            ptype = routed.get("intent")

            ranking_results = lookup.rank(
                season=season,
                metric=metric,
                top_n=top_n,
                ptype=routed.get("intent")   # pitcher/batter
            )

            hits = []
            for rec, val in ranking_results:
                hits.append({
                    "record_key": rec.get("record_key"),
                    "player_name": rec.get("player_name"),
                    "season": rec.get("season"),
                    "team": rec.get("team"),
                    "type": rec.get("type"),
                    "stats": rec.get("stats"),
                    "score": float(val)  # ⭐ 用 stats 值，不是 hybrid score
                })

            print(f"✅ Ranking 成功: {len(hits)} 筆")

            # 回答（仍可使用 RAG answer）
            answer = generate_rag_answer(query, hits, routed)

            elapsed_time = time.time() - start_time

            # Ranking Query → 直接 return（不跑 Hybrid Search）
            return jsonify({
                "ok": True,
                "query": query,
                "routed": routed,
                "mode": qtype,
                "hits": hits,
                "search_results": hits,
                "structured": {
                    "kind": "ranking",
                    "metric": metric,
                    "season": season,
                    "results": [
                        {
                            "player": h["player_name"],
                            "value": h["score"],
                            "season": h["season"],
                            "team": h["team"]
                        }
                        for h in hits
                    ]
                },
                "answer": answer,
                "metrics": {
                    "ranking": True,
                    "response_time": elapsed_time
                }
            })

        # ============================================================
        # Factual / Comparison / Analysis → 執行 Hybrid Search 
        # ============================================================

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

        # ============================================================
        # Analysis Query 特殊處理
        # ============================================================
        if qtype == "analysis":
            if not hits:
                return jsonify({
                    "ok": False, 
                    "error": "沒有找到相關數據進行分析"
                }), 400
            
            # 取第一筆最相關的結果
            hit = hits[0]
            player_name = hit.get("player_name")
            season = hit.get("season")
            player_type = hit.get("type")
            
            # 識別問題類型
            from src.web.stat_selection_config import detect_problem_type
            problem_type = detect_problem_type(query)
            
            if not problem_type:
                # 根據球員類型給出建議
                if player_type == "pitcher":
                    suggestion = f"""無法識別具體問題類型。{player_name} 是投手，請嘗試更明確的描述：

                                **投手分析範例**：
                                - 「{player_name} 的控球為什麼這麼差」
                                - 「{player_name} 的壓制力為什麼下降」
                                - 「{player_name} 為什麼防禦率這麼高」
                                - 「{player_name} 為什麼容易被長打」"""
                else:
                    suggestion = f"""無法識別具體問題類型。{player_name} 是打者，請嘗試更明確的描述：

                                    **打者分析範例**：
                                    - 「{player_name} 的打擊率為什麼這麼低」
                                    - 「{player_name} 的長打力為什麼不足」
                                    - 「{player_name} 為什麼三振這麼多」
                                    - 「{player_name} 的選球為什麼這麼差」"""
                
                return jsonify({
                    "ok": False,
                    "error": suggestion
                }), 400
            
            # 整合 LLM Analysis
            if mode == "llm" and OLLAMA_AVAILABLE:
                # LLM 路徑
                llm_engine = AnalysisLLMEngine()
                fact_checker = FactChecker()
                league_avg = get_league_averages(season, player_type)
                
                try:
                    llm_answer = llm_engine.analyze(
                        query=query,
                        player_data=hit,
                        problem_type=problem_type,
                        league_avg=league_avg
                    )
                    
                    # 事實檢查
                    fact_check = fact_checker.verify_facts(llm_answer, hits)
                    
                    elapsed_time = time.time() - start_time
                    
                    return jsonify({
                        "ok": True,
                        "query": query,
                        "routed": routed,
                        "mode": "llm_analysis",
                        "answer": llm_answer,
                        "problem_type": problem_type,
                        "fact_check": fact_check,
                        "player": {
                            "name": player_name,
                            "season": season,
                            "type": player_type
                        },
                        "search_results": hits,
                        "metrics": {
                            **metrics,
                            "response_time": elapsed_time,
                            "fact_consistency": fact_check["confidence"],
                            "hallucination_count": fact_check["hallucination_count"]
                        }
                    })
                    
                except Exception as e:
                    print(f"❌ LLM Analysis 錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to RAG
                    mode = "rag"
            
            # RAG 路徑
            if mode == "rag" or not OLLAMA_AVAILABLE:
                from src.web.answer_templates import format_analysis_answer
                league_avg = get_league_averages(season, player_type) if 'get_league_averages' in dir() else None
                
                answer = format_analysis_answer(
                    player_name=player_name,
                    season=season,
                    problem_type=problem_type,
                    player_data=hit,
                    league_avg_data=league_avg,
                    player_type=player_type
                )
                
                elapsed_time = time.time() - start_time
                
                return jsonify({
                    "ok": True,
                    "query": query,
                    "routed": routed,
                    "mode": "rag_analysis",
                    "answer": answer,
                    "problem_type": problem_type,
                    "player": {
                        "name": player_name,
                        "season": season,
                        "type": player_type
                    },
                    "search_results": hits,
                    "metrics": {
                        **metrics,
                        "response_time": elapsed_time
                    }
                })

        # ============================================================
        # 生成回答
        # ============================================================
        if mode == "llm" and OLLAMA_AVAILABLE:
            answer = generate_llm_response(query, routed, raw_hits, history)
        else:
            answer = generate_rag_answer(query, hits, routed)

        elapsed_time = time.time() - start_time

        # ============================================================
        # 記錄指標 + 回傳
        # ============================================================
        response = {
            "ok": True,
            "query": query,
            "routed": routed,
            "mode": qtype,
            "search_results": hits,
            "hits": hits,
            "structured": None,
            "answer": answer,
            "metrics": metrics,
            "eval_metrics": {
                "recall_at_5": metrics["recall@k"],
                "precision_at_5": metrics["precision@k"],
                "mrr": metrics["mrr"]
            }
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
        "metrics_file": str(METRICS_FILE),
        "eval_metrics": {
            "recall_at_5": None,
            "precision_at_5": None,
            "mrr": None
        }
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