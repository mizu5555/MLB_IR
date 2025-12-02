# ============================================================
# Query Router — 強化版（支援中英文球員名）
# ============================================================

import re
import json
from pathlib import Path

# ------------------------------------------------------------
# 中文 → 英文球員名稱映射
# ------------------------------------------------------------
PLAYER_ALIAS = {
    "大谷": "Shohei Ohtani",
    "大谷翔平": "Shohei Ohtani",
    "翔平": "Shohei Ohtani",
    "山本": "Yoshinobu Yamamoto",
    "山本由伸": "Yoshinobu Yamamoto",
    "鈴木誠也": "Seiya Suzuki",
    "達比修": "Yu Darvish",
    "達比修有": "Yu Darvish",
    "菊池雄星": "Yusei Kikuchi",
    "前田健太": "Kenta Maeda",
}

# 常見英文球員名（姓氏）
COMMON_PLAYERS = [
    "Ohtani", "Judge", "Trout", "Betts", "Acuna", "Freeman", "Soto", 
    "Tatis", "Harper", "Turner", "Devers", "Altuve", "Vladdy", "Olson",
    "Yamamoto", "Darvish", "Suzuki", "Kikuchi", "Maeda",
    "Verlander", "Cole", "Scherzer", "deGrom", "Kershaw"
]

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
    # v6 改進：更完整的 Comparison 判斷
    # ------------------------------------------------------------
    def detect_query_type(self, query, players, metric, top_n, seasons):
        """
        改進版 Query Type 判斷
        
        新增邏輯：
        1. 多位球員 (players >= 2) → comparison
        2. 單球員多賽季 (players == 1 and seasons >= 2) → comparison
        3. 有「比」字 + 至少 1 個球員 → comparison（不要求 metric）
        """
        q = query.lower()

        # 1️⃣ Ranking（優先級最高）
        if top_n or ("前" in query and "名" in query):
            return "ranking"

        if "top" in q and re.search(r"top\s*\d+", q):
            return "ranking"

        # 2️⃣ Comparison（優先級第二）
        # 改進 1: 多位球員
        if len(players) >= 2:
            return "comparison"
        
        # 改進 2: 單球員多賽季
        if len(players) == 1 and len(seasons) >= 2:
            return "comparison"
        
        # 改進 3: 有「比」字 + 至少 1 個球員（不要求 metric）
        if "比" in query and len(players) >= 1:
            return "comparison"

        # 其他比較關鍵字
        if "vs" in q or "compare" in q:
            return "comparison"

        # 3️⃣ Factual（預設）
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

        # Query Type（傳入 seasons 參數）
        qtype = self.detect_query_type(query, players, metric, top_n, seasons)

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
    
    print("=" * 60)
    print("Query Router v6 測試")
    print("=" * 60)
    
    test_queries = [
        "Yamamoto 防禦率",
        "2024 全壘打前 10 名",
        "Ohtani 跟 Judge 打擊率比較",
        "Ohtani 2022 2023 全壘打",
        "Judge power 表現",
        "大谷 山本 比較",
    ]
    
    for q in test_queries:
        print(f"\n查詢: {q}")
        routed = qr.route(q)
        print(f"  Type: {routed['query_type']}")
        print(f"  Players: {routed['players']}")
        print(f"  Seasons: {routed['seasons']}")
        print(f"  Metric: {routed['metric']}")
        print(f"  Top N: {routed['top_n']}")