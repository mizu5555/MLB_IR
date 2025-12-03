# ============================================================
# Query Router v4 (v6.0.2 Bug Fix)
# 修正：
# 1. route() 調用 detect_intent() 時傳入 metric 參數（關鍵修正！）
# 2. 擴充 PITCHING_KEYWORDS（加入「防禦率」）
# 3. extract_metric() 按關鍵字長度排序（長的優先）
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
}

# ------------------------------------------------------------
# Metric 映射（按長度排序，長的優先）
# ------------------------------------------------------------
METRIC_MAP = {
    # ⭐ 投手指標（優先級最高，完整匹配）
    "防禦率": "ERA",
    "投球局數": "IP",
    "被安打": "H",
    "被全壘打": "HR",
    "保送": "BB",
    "三振": "SO",
    "自責分": "ER",
    "勝場": "W",
    "敗場": "L",
    "救援成功": "SV",
    
    # ⭐ 打者指標（優先級次之）
    "打擊率": "AVG",
    "上壘率": "OBP",
    "長打率": "SLG",
    "全壘打": "HR",
    "安打": "H",
    "得分": "R",
    "打點": "RBI",
    "盜壘": "SB",
    "保送": "BB",
    "三振": "SO",
    
    # 英文縮寫（最後匹配）
    "era": "ERA",
    "whip": "WHIP",
    "fip": "FIP",
    "xfip": "xFIP",
    "siera": "SIERA",
    "k/9": "K/9",
    "bb/9": "BB/9",
    "k/bb": "K/BB",
    "ip": "IP",
    "w": "W",
    "l": "L",
    "sv": "SV",
    "hr": "HR",
    "home runs": "HR",
    "ops": "OPS",
    "slugging": "SLG",
    "obp": "OBP",
    "avg": "AVG",
    "rbi": "RBI",
    "sb": "SB",
    "woba": "wOBA",
    "wrc+": "wRC+",
    "iso": "ISO",
    "babip": "BABIP",
}

# 附加：判斷 batting / pitching 意圖
BATTING_KEYWORDS = [
    "打擊", "打者", "batting", "hitting", 
    "ops", "home runs", "slugging",
    "安打", "得分", "打點", "盜壘",
]

PITCHING_KEYWORDS = [
    "投球", "投手", "pitching", 
    "era", "whip", "fip",
    "防禦率",
    "投球局數", "被安打", "保送",
    "三振", "k/9", "k%",
]


# ------------------------------------------------------------
# QueryRouter 本體
# ------------------------------------------------------------
class QueryRouter:

    def __init__(self):
        """
        初始化 Query Router
        v6.0.2: 從 player_db.json 載入球員別名
        """
        self.player_index = {}
        self._load_player_db()

    def _load_player_db(self):
        """
        從 player_db.json 載入球員資料，建立別名索引
        格式：{ "球員名_ID": { "name": "英文全名", "id": "660271", "seasons": {...} } }
        """
        try:
            root = Path(__file__).resolve().parents[2]
            player_db_path = root / "data" / "mlb_data_adv" / "player_db.json"
            
            if not player_db_path.exists():
                print(f"⚠️ player_db.json 不存在: {player_db_path}")
                return
            
            with open(player_db_path, "r", encoding="utf-8") as f:
                player_db = json.load(f)
            
            print(f"📘 載入 player_db.json: {len(player_db)} 位球員")
            
            # 建立別名索引
            for key, info in player_db.items():
                name = info.get("name", "")
                if not name:
                    continue
                
                # 1. 英文全名
                self.player_index[name.lower()] = name
                
                # 2. 姓氏（例如 "Ohtani"）
                parts = name.split()
                if len(parts) >= 2:
                    last_name = parts[-1]
                    self.player_index[last_name.lower()] = name
                
                # 3. 名字（例如 "Shohei"）
                if len(parts) >= 2:
                    first_name = parts[0]
                    self.player_index[first_name.lower()] = name
            
            # 4. 加入中文別名
            for zh, en in PLAYER_ALIAS.items():
                self.player_index[zh.lower()] = en
            
            print(f"✅ 球員索引建立完成：{len(self.player_index)} 個別名")
            
        except Exception as e:
            print(f"⚠️ 載入 player_db.json 失敗: {e}")

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
    # v6.0.2: 按關鍵字長度排序（長的優先）
    # ------------------------------------------------------------
    def extract_metric(self, query: str):
        q = query.lower()
        
        # ⭐ 修正：按關鍵字長度排序（長的優先）
        sorted_metrics = sorted(METRIC_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        
        for kw, metric in sorted_metrics:
            if kw in q:
                return metric
        
        return None

    # ------------------------------------------------------------
    # 抽取球員名稱（中文 → 英文，支援姓氏/全名）
    # v6.0.2: 使用 player_index 查詢
    # ------------------------------------------------------------
    def extract_players(self, query: str):
        """
        從查詢中抽取球員名稱（支援中文、英文姓氏、英文全名）
        
        範例：
        - "大谷 2023" → ["Shohei Ohtani"]
        - "Ohtani 2023" → ["Shohei Ohtani"]
        - "Judge 跟 Ohtani 比較" → ["Aaron Judge", "Shohei Ohtani"]
        """
        players = []
        q_lower = query.lower()
        
        # 遍歷所有別名，檢查是否在查詢中
        for alias, full_name in self.player_index.items():
            # 使用單詞邊界匹配（避免部分匹配，例如 "judge" 不會匹配到 "judged"）
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, q_lower):
                if full_name not in players:
                    players.append(full_name)
        
        return players

    # ------------------------------------------------------------
    # 投打方向（intent）
    # v6.0.2: 優先根據 metric 判斷，再根據關鍵字判斷
    # ------------------------------------------------------------
    def detect_intent(self, query: str, metric: str = None):
        """
        判斷查詢意圖：batting / pitching / None
        
        v6.0.2 修正：
        1. 優先根據 metric 判斷（ERA → pitching，HR → batting）
        2. 再根據關鍵字判斷（"投球" → pitching，"打擊" → batting）
        """
        # ⭐ 1️⃣ 優先根據 metric 判斷
        if metric:
            # 投手指標
            if metric in ["ERA", "FIP", "xFIP", "SIERA", "WHIP", "K/9", "BB/9", "K/BB", "IP", "W", "L", "SV"]:
                return "pitching"
            
            # 打者指標（但排除投手的 HR、BB、SO）
            if metric in ["AVG", "OBP", "SLG", "OPS", "wOBA", "wRC+", "ISO", "BABIP", "RBI", "R", "SB"]:
                return "batting"
            
            # 模糊指標（HR、BB、SO 可能是打者或投手）
            # 這時候繼續根據關鍵字判斷
        
        # ⭐ 2️⃣ 再根據關鍵字判斷
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
        if "比" in query and len(players) >= 1:
            return "comparison"

        if "vs" in q or "compare" in q or "跟" in query:
            return "comparison"
        
        # 多賽季比較（例如：大谷 2022 2023 全壘打）
        seasons = self.extract_seasons(query)
        if len(seasons) >= 2 and len(players) >= 1:
            return "comparison"

        # 如果只問單項數據：也算 factual
        return "factual"

    # ------------------------------------------------------------
    # Query Router 主流程
    # v6.0.2: 修正 detect_intent() 調用時傳入 metric 參數
    # ------------------------------------------------------------
    def route(self, query: str):
        original = query

        # 抽取季節
        seasons = self.extract_seasons(query)

        # 抽取球員
        players = self.extract_players(query)

        # 抽取 metric（HR、ERA、OPS...）
        metric = self.extract_metric(query)

        # ⭐⭐⭐ 關鍵修正：傳入 metric 參數 ⭐⭐⭐
        intent = self.detect_intent(query, metric)

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
    print(f"\n✅ Query Router v4 初始化完成，載入 {len(qr.player_index)} 個球員別名\n")
    
    while True:
        q = input("\n輸入查詢（或 Enter 離開）：")
        if not q.strip():
            break

        routed = qr.route(q)
        print("\n--- Routed Result ---")
        print(json.dumps(routed, indent=2, ensure_ascii=False))