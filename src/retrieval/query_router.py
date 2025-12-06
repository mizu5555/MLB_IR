# ============================================================
# Query Router v5 (v6.0.3 Bug Fix)
# 修正：
# 1. extract_top_n() 識別「前 N 高/低/快」（Bug 2）
# 2. extract_players() 支援中文綴詞（Bug 3）
# 3. 保留 v4 的所有修正（Intent 識別、Metric 長度排序）
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
# Metric 映射（Ranking + Comparison 使用）
# ------------------------------------------------------------
METRIC_MAP = {

    # =========================
    # 基礎打擊（Counting Stats）
    # =========================
    "hr": "HR",
    "全壘打": "HR",

    "hits": "Hits",
    "安打": "Hits",

    "rbi": "RBI",
    "打點": "RBI",

    "runs": "Runs",
    "得分": "Runs",

    "sb": "SB",
    "盜壘": "SB",

    "bb": "BB",
    "保送": "BB",

    "so": "SO",
    "三振": "SO",

    # =========================
    # 打擊率 / slash line
    # =========================
    "avg": "AVG",
    "打擊率": "AVG",

    "obp": "OBP",
    "上壘率": "OBP",

    "slg": "SLG",
    "長打率": "SLG",

    "ops": "OPS",
    "上壘加長打率": "OPS",

    # =========================
    # 進階打擊（Sabermetrics）
    # =========================
    "iso": "ISO",
    "純粹長打率": "ISO",

    "babip": "BABIP",
    "被內野安打率": "BABIP",
    "平均打球落點": "BABIP",

    "woba": "wOBA",
    "加權上壘率": "wOBA",

    "wrc+": "wRC+",
    "加權創造分": "wRC+",
    "加權得分創造+": "wRC+",

    "barrel%": "Barrel%",
    "強擊率": "Barrel%",
    "桶擊率": "Barrel%",

    "hardhit%": "HardHit%",
    "強勁擊球率": "HardHit%",
    "強擊球率": "HardHit%",

    "exit_velocity": "Exit_Velocity",
    "出棒速度": "Exit_Velocity",
    "擊球速度": "Exit_Velocity",

    "launch_angle": "Launch_Angle",
    "擊球仰角": "Launch_Angle",

    # =========================
    # 選球與揮棒能力（Plate discipline）
    # =========================
    "o-swing%": "O-Swing%",
    "o-swing": "O-Swing%",
    "壞球揮棒率": "O-Swing%",

    "z-swing%": "Z-Swing%",
    "好球揮棒率": "Z-Swing%",

    "swing%": "Swing%",
    "揮棒率": "Swing%",

    "o-contact%": "O-Contact%",
    "壞球接觸率": "O-Contact%",

    "z-contact%": "Z-Contact%",
    "好球接觸率": "Z-Contact%",

    "contact%": "Contact%",
    "接觸率": "Contact%",

    "csw%": "CSW%",
    "揮空加看球率": "CSW%",
    "揮空+叫好率": "CSW%",

    "swstr%": "SwStr%",
    "揮空率": "SwStr%",

    # =========================
    # 投手核心指標（ERA / FIP / WHIP）
    # =========================
    "era": "ERA",
    "防禦率": "ERA",

    "whip": "WHIP",
    "每局上壘率": "WHIP",

    "fip": "FIP",
    "獨立防禦率": "FIP",

    "xfip": "xFIP",
    "預期獨立防禦率": "xFIP",

    "siera": "SIERA",
    "技能互動調整防禦率": "SIERA",

    # =========================
    # 投手比率類（K/BB 類型）
    # =========================
    "k%": "K%",
    "三振率": "K%",

    "bb%": "BB%",
    "保送率": "BB%",

    "k/9": "K/9",
    "每九局三振": "K/9",

    "bb/9": "BB/9",
    "每九局保送": "BB/9",

    "k/bb": "K/BB",
    "三振保送比": "K/BB",

    # =========================
    # 被打結果（Batted-ball allowed）
    # =========================
    "home_runs_allowed": "Home_Runs_Allowed",
    "home runs allowed": "Home_Runs_Allowed",
    "被全壘打": "Home_Runs_Allowed",
    "被打全壘打": "Home_Runs_Allowed",

    "h/9": "H/9",
    "每九局被安打": "H/9",

    "hr/9": "HR/9",
    "每九局被全壘打": "HR/9",

    "innings pitched": "Innings_Pitched",
    "inning pitched": "Innings_Pitched",
    "ip": "Innings_Pitched",
    "投球局數": "Innings_Pitched",
    "局數": "Innings_Pitched",

    # =========================
    # 勝投相關
    # =========================
    "wins": "Wins",
    "勝場": "Wins",

    "losses": "Losses",
    "敗場": "Losses",

    "saves": "Saves",
    "救援成功": "Saves",

    # =========================
    # WAR 系列
    # =========================
    "war": "WAR",
    "勝場貢獻值": "WAR",

    # =========================
    # 英文別名（便於用戶直接輸入英文）
    # =========================
    "batting average": "AVG",
    "on-base percentage": "OBP",
    "slugging percentage": "SLG",
    "on-base plus slugging": "OPS",
    "home runs": "HR",
    "strikeouts": "Strikeouts",
    "earned run average": "ERA",
    "runs batted in": "RBI",
}

# 附加：判斷 batter / pitcher 意圖
batter_KEYWORDS = [
    "打擊", "打者", "batter", "hitting", 
    "ops", "home runs", "slugging",
    "安打", "得分", "打點", "盜壘",
]

pitcher_KEYWORDS = [
    "投球", "投手", "pitcher", 
    "era", "whip", "fip",
    "防禦率",  # v6.0.2
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
            
            print(f"🏀 球員索引建立完成：{len(self.player_index)} 個別名")
            
        except Exception as e:
            print(f"⚠️ 載入 player_db.json 失敗: {e}")

    # ------------------------------------------------------------
    # 解析季節（2022, 2023...）
    # ------------------------------------------------------------
    def extract_seasons(self, query: str):
        years = re.findall(r"(20[0-2][0-9])", query)
        return list(sorted(set(int(y) for y in years)))

    # ------------------------------------------------------------
    # 找 top_n 查詢（例如：前 10 名 / top 5 / 前 3 高/低）
    # v6.0.3: 修正 Bug 2 - 識別「前 N 高/低/快」
    # ------------------------------------------------------------
    def extract_top_n(self, query: str):
        # 中文：前 N 名

        m = re.search(r"排名前\s*(\d+)\s*", query)
        if m:
            return int(m.group(1))
        
        m = re.search(r"前\s*(\d+)\s*(位|名)", query)
        if m:
            return int(m.group(1))
        
        m = re.search(r"最(高|低|快|慢|多|少)的\s*(\d+)\s*(位|名)", query)
        if m:
            return int(m.group(2))

        # ⭐ v6.0.3: 前 N 高/低/快/慢
        m = re.search(r"前\s*(\d+)\s*(高|低|快|慢|多|少)", query)
        if m:
            return int(m.group(1))

        # 英文：top N
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
        
        # 修正：按關鍵字長度排序（長的優先）
        sorted_metrics = sorted(METRIC_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        
        for kw, metric in sorted_metrics:
            if kw.lower() in q:
                return metric
            
        return None

    # ------------------------------------------------------------
    # 抽取球員名稱（中文 → 英文，支援姓氏/全名）
    # v6.0.3: 修正 Bug 3 - 支援中文綴詞（「Ohtani在2023的全壘打」）
    # ------------------------------------------------------------
    def extract_players(self, query: str):
        """
        從查詢中抽取球員名稱（支援中文、英文姓氏、英文全名）
        
        v6.0.3 修正：
        - 移除單詞邊界限制（\b 不支援中文）
        - 改用子字串匹配 + 長度優先（避免誤匹配）
        
        範例：
        - "大谷 2023" → ["Shohei Ohtani"]
        - "Ohtani 2023" → ["Shohei Ohtani"]
        - "Ohtani在2023的全壘打" → ["Shohei Ohtani"] ⭐ v6.0.3 修正
        - "Judge 跟 Ohtani 比較" → ["Aaron Judge", "Shohei Ohtani"]
        """
        players = []
        q_lower = query.lower()
        
        # ⭐ v6.0.3: 按別名長度排序（長的優先），避免誤匹配
        # 例如：「judge」優先於「ju」
        sorted_aliases = sorted(
            self.player_index.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        )
        
        for alias, full_name in sorted_aliases:
            # ⭐ v6.0.3: 移除單詞邊界限制，改用簡單子字串匹配
            if alias in q_lower:
                if full_name not in players:
                    players.append(full_name)
        
        return players

    # ------------------------------------------------------------
    # 投打方向（intent）
    # v6.0.2: 優先根據 metric 判斷，再根據關鍵字判斷
    # ------------------------------------------------------------
    def detect_intent(self, query: str, metric: str = None):
        """
        判斷查詢意圖：batter / pitcher / None
        
        v6.0.2 修正：
        1. 優先根據 metric 判斷（ERA → pitcher，HR → batter）
        2. 再根據關鍵字判斷（"投球" → pitcher，"打擊" → batter）
        """
        q = query.lower()
        
        # 1️⃣ 優先根據 metric 判斷
        if metric:
            # 投手指標
            if metric in ["ERA", "FIP", "xFIP", "SIERA", "WHIP", "K/9", "BB/9", "K/BB", "IP", "W", "L", "SV"]:
                return "pitcher"
            
            # 打者指標（但排除投手的 HR、BB、SO）
            if metric in ["AVG", "OBP", "SLG", "OPS", "wOBA", "wRC+", "ISO", "BABIP", "RBI", "R", "SB", "H", "2B", "3B"]:
                return "batter"
            
            # ⭐模糊指標（HR、BB、SO 可能是打者或投手)待更新
            # if metric in ["HR", "BB", "SO", "K%", "BB%"]:
               
        #  2️⃣ 再根據關鍵字判斷
        if any(k in q for k in pitcher_KEYWORDS):
            return "pitcher"
        if any(k in q for k in batter_KEYWORDS):
            return "batter"
        
        return None

    # ------------------------------------------------------------
    # Query Type（factual / ranking / comparison / analysis）
    # v6.1.0 新增analysis
    # ------------------------------------------------------------
    def detect_query_type(self, query, players, metric, top_n):
        
        q = query.lower()

        strong_analysis_keywords = [
        # 中文關鍵字
        "為什麼", "為何", "原因", "怎麼回事", "怎麼了",
        "分析", "診斷", "問題", "建議", "改善",
        "哪裡出問題", "什麼問題", "發生什麼事",
        
        # 英文強烈意圖
        "why", "what happened", "what's wrong",
        "analyze", "analysis", "diagnose", "problem",
        "suggest", "improve", "issue", "where's the issue",
        ]

        supporting_keywords = [
        # 表現相關（但必須配合強烈意圖）
        "壓制力", "控球", "打擊率", "長打力", "選球",
        "不佳", "下降", "低迷", "不好", "糟糕", "差",
        
        # 英文
        "poor", "bad", "struggling", "decline",
        "weakness", "strength",
        ]

        has_strong_intent = any(kw in q for kw in strong_analysis_keywords)
    
        if has_strong_intent:
            # 有強烈意圖 → 確定是 analysis
            return "analysis"
        
        # 檢查是否同時包含支援性關鍵字（需要至少 2 個）
        support_count = sum(1 for kw in supporting_keywords if kw in q)
        
        if support_count >= 2 and len(query) > 10:
            # 有多個支援性關鍵字，且查詢足夠長 → 可能是 analysis
            # 但還需要排除其他明確的查詢類型
            
            # 排除：如果有數字（可能是 ranking 或 comparison）
            if top_n or "前" in query or "top" in q:
                pass  # 繼續往下判斷（不是 analysis）
            elif "vs" in q or "比" in query or "跟" in query:
                pass  # 繼續往下判斷（可能是 comparison）
            else:
                return "analysis"

        if top_n:
            return "ranking"

        if ("前" in query or "最" in query) and ("名" in query or "高" in query or "低" in query or "快" in query or "慢" in query):
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

        # ⭐⭐⭐ v6.0.2: 傳入 metric 參數 ⭐⭐⭐
        intent = self.detect_intent(query, metric)

        # top_n
        top_n = self.extract_top_n(query)

        # Query Type
        qtype = self.detect_query_type(query, players, metric, top_n)

        # Type Boost（給 Hybrid Search）
        if intent == "pitcher":
            type_boost = {"pitcher": 0.5, "batter": -0.3}
        elif intent == "batter":
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
    print(f"\n✅ Query Router v5 初始化完成，載入 {len(qr.player_index)} 個球員別名\n")
    
    # 測試 Bug 2 和 Bug 3
    test_cases = [
        "大谷2023年投球壓制力為什麼下降",
        "2023 防禦率前 3 低",
        "2023 全壘打前 3 高",
        "Ohtani 2023 全壘打",
        "Ohtani在2023的全壘打",
    ]
    
    for q in test_cases:
        routed = qr.route(q)
        print(f"\n查詢: {q}")
        print(f"  Query Type: {routed['query_type']}")
        print(f"  Top N: {routed['top_n']}")
        print(f"  Players: {routed['players']}")
        print(f"  Metric: {routed['metric']}")