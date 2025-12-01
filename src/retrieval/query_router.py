# ============================================================
# Query Router — 強化 Ranking / Comparison / Metric 抽取版
# ============================================================

import re
import json
from pathlib import Path

# ------------------------------------------------------------
# 中文 → 英文球員名稱映射（你可在這邊補充）
# ------------------------------------------------------------
PLAYER_ALIAS = {
    "大谷": "Shohei Ohtani",
    "大谷翔平": "Shohei Ohtani",
    "翔平": "Shohei Ohtani",
    "山本": "Yoshinobu Yamamoto",
    "山本由伸": "Yoshinobu Yamamoto",
    "鈴木誠也": "Seiya Suzuki",
}

# ------------------------------------------------------------
# Metric 映射（Ranking + Comparison 使用）
# ------------------------------------------------------------
METRIC_MAP = {
    # 打者
    "hr": "HR",
    "home runs": "HR",
    "全壘打": "HR",
    "ops": "OPS",
    "slugging": "SLG",
    "obp": "OBP",
    "打擊率": "AVG",
    "安打": "H",
    "rbi": "RBI",
    "打點": "RBI",
    "盜壘": "SB",

    # 投手
    "era": "ERA",
    "防禦率": "ERA",
    "so": "SO",
    "三振": "SO",
    "k%": "K%",
    "k/9": "K/9",
    "whip": "WHIP",
    "fip": "FIP",
}

# 附加：判斷 batting / pitching 意圖
BATTING_KEYWORDS = ["打擊", "打者", "batting", "hitting", "ops", "hr", "home runs", "slugging"]
PITCHING_KEYWORDS = ["投球", "投手", "pitching", "era", "whip", "fip", "三振"]


# ------------------------------------------------------------
# QueryRouter 本體
# ------------------------------------------------------------
class QueryRouter:

    def __init__(self):
        pass

    # ------------------------------------------------------------
    # 解析季節（2022, 2023...）
    # ------------------------------------------------------------
    def extract_seasons(self, query: str):
        years = re.findall(r"(20[0-2][0-9])", query)
        return list(sorted(set(int(y) for y in years)))

    # ------------------------------------------------------------
    # 找 top_n 查詢（例如：前 10 名 / top 5）
    # ------------------------------------------------------------
    def extract_top_n(self, query: str):
        # 中文
        m = re.search(r"前\s*(\d+)\s*名", query)
        if m:
            return int(m.group(1))

        # 英文
        m = re.search(r"top\s*(\d+)", query, re.I)
        if m:
            return int(m.group(1))

        return None

    # ------------------------------------------------------------
    # 解析 metric：OPS, HR, ERA, K%，SLG…
    # ------------------------------------------------------------
    def extract_metric(self, query: str):
        q = query.lower()
        for kw, metric in METRIC_MAP.items():
            if kw in q:
                return metric
        return None

    # ------------------------------------------------------------
    # 抽取球員名稱（中文 → 英文）
    # ------------------------------------------------------------
    def extract_players(self, query: str):
        players = []
        for zh, en in PLAYER_ALIAS.items():
            if zh in query:
                players.append(en)
        return players

    # ------------------------------------------------------------
    # 投打方向（intent）
    # ------------------------------------------------------------
    def detect_intent(self, query: str):
        q = query.lower()

        if any(k in q for k in PITCHING_KEYWORDS):
            return "pitching"
        if any(k in q for k in BATTING_KEYWORDS):
            return "batting"
        return None

    # ------------------------------------------------------------
    # Query Type（factual / ranking / comparison / analysis）
    # ------------------------------------------------------------
    def detect_query_type(self, query, players, metric, top_n):
        q = query.lower()

        # Ranking
        if top_n or ("前" in query and "名" in query):
            return "ranking"

        if "top" in q and re.search(r"top\s*\d+", q):
            return "ranking"

        # Comparison
        if "比" in query and len(players) >= 1 and metric:
            return "comparison"

        if "vs" in q or "compare" in q:
            return "comparison"

        # 如果只問單項數據：也算 factual
        return "factual"

    # ------------------------------------------------------------
    # Query Router 主流程
    # ------------------------------------------------------------
    def route(self, query: str):
        original = query

        # 抽取季節
        seasons = self.extract_seasons(query)

        # 抽取球員
        players = self.extract_players(query)

        # 投打方向
        intent = self.detect_intent(query)

        # metric（HR、ERA、OPS...）
        metric = self.extract_metric(query)

        # top_n
        top_n = self.extract_top_n(query)

        # Query Type
        qtype = self.detect_query_type(query, players, metric, top_n)

        # Type Boost（給 Hybrid Search）
        if intent == "pitching":
            type_boost = {"pitcher": 0.5, "batter": -0.3}
        elif intent == "batting":
            type_boost = {"batter": 0.5, "pitcher": -0.3}
        else:
            type_boost = {"batter": 0.0, "pitcher": 0.0}

        # normalized_query（避免詞重複）
        parts = []

        # 球員
        for p in players:
            parts.append(p)

        # 季節
        for y in seasons:
            parts.append(str(y))

        # metric
        if metric:
            parts.append(metric)

        # intent
        if intent:
            parts.append(intent)

        normalized = " ".join(parts) if parts else query

        return {
            "original_query": original,
            "normalized_query": normalized.strip(),
            "query_type": qtype,
            "intent": intent,
            "metric": metric,
            "players": players,
            "seasons": seasons,
            "top_n": top_n,
            "career": False,
            "type_boost": type_boost,
            "extra_tags": []
        }


# CLI 測試
if __name__ == "__main__":
    qr = QueryRouter()
    while True:
        q = input("\n輸入查詢（或 Enter 離開）：")
        if not q.strip():
            break

        routed = qr.route(q)
        print("\n--- Routed Result ---")
        print(json.dumps(routed, indent=2, ensure_ascii=False))
