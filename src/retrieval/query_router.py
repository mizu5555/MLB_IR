# ============================================================
# Query Router v2 — 混合方案版
# 從 JSON 載入球員 + 自動別名生成 + 中文別名
# ============================================================

import re
import json
from pathlib import Path

# ------------------------------------------------------------
# 手動中文別名（補充自動生成的不足）
# ------------------------------------------------------------
MANUAL_ALIASES = {
    "大谷": "Shohei Ohtani",
    "大谷翔平": "Shohei Ohtani",
    "翔平": "Shohei Ohtani",
    "山本": "Yoshinobu Yamamoto",
    "山本由伸": "Yoshinobu Yamamoto",
    "鈴木誠也": "Seiya Suzuki",
    "鈴木": "Seiya Suzuki",
    "達比修": "Yu Darvish",
    "達比修有": "Yu Darvish",
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

    def __init__(self, data_path=None):
        """
        初始化 Query Router
        
        參數：
            data_path: training_data.json 的路徑（可選）
        """
        # 建立球員索引
        self.player_index = self._build_player_index(data_path)
        print(f"✅ Query Router 初始化完成，載入 {len(self.player_index)} 個球員別名")

    # ------------------------------------------------------------
    # 建立球員索引
    # ------------------------------------------------------------
    def _build_player_index(self, data_path=None):
        """
        從 training_data.json 建立球員索引
        
        返回：
            {
                "ohtani": "Shohei Ohtani",
                "shohei": "Shohei Ohtani",
                "shohei ohtani": "Shohei Ohtani",
                ...
            }
        """
        player_index = {}
        
        # 1. 載入 training_data.json
        if data_path is None:
            ROOT = Path(__file__).resolve().parents[2]
            data_path = ROOT / "data" / "mlb_data_adv" / "training_data.json"
        
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                training_data = json.load(f)
            
            print(f"📘 載入 training_data.json: {len(training_data)} 筆記錄")
            
            # 2. 提取所有唯一球員
            unique_players = set()
            for record in training_data:
                player_name = record.get("player_name")
                if player_name:
                    unique_players.add(player_name)
            
            print(f"📋 找到 {len(unique_players)} 位唯一球員")
            
            # 3. 為每個球員生成別名
            for player_name in unique_players:
                # 分割名字（假設格式：First Last 或 First Middle Last）
                parts = player_name.split()
                
                # 全名（小寫）
                full_name_lower = player_name.lower()
                player_index[full_name_lower] = player_name
                
                if len(parts) >= 2:
                    # 姓氏（Last name）
                    last_name = parts[-1].lower()
                    # 優先匹配長的，所以只在不存在時添加
                    if last_name not in player_index:
                        player_index[last_name] = player_name
                    
                    # 名字（First name）
                    first_name = parts[0].lower()
                    if first_name not in player_index:
                        player_index[first_name] = player_name
                
                # 處理特殊情況：如果有中間名
                if len(parts) == 3:
                    # First Last（去掉中間名）
                    first_last = f"{parts[0]} {parts[2]}".lower()
                    if first_last not in player_index:
                        player_index[first_last] = player_name
            
            # 4. 加入手動中文別名
            for alias, full_name in MANUAL_ALIASES.items():
                player_index[alias.lower()] = full_name
            
            print(f"✅ 球員索引建立完成：{len(player_index)} 個別名")
            
        except FileNotFoundError:
            print(f"⚠️ 找不到 training_data.json: {data_path}")
            print("⚠️ 使用手動別名...")
            # Fallback：只使用手動別名
            for alias, full_name in MANUAL_ALIASES.items():
                player_index[alias.lower()] = full_name
        
        except Exception as e:
            print(f"❌ 載入球員索引失敗: {e}")
            # Fallback：只使用手動別名
            for alias, full_name in MANUAL_ALIASES.items():
                player_index[alias.lower()] = full_name
        
        return player_index

    # ------------------------------------------------------------
    # 抽取球員名稱（使用球員索引）
    # ------------------------------------------------------------
    def extract_players(self, query: str):
        """
        從查詢中抽取球員名稱
        
        策略：
        1. 不分大小寫匹配
        2. 優先匹配完整名字（長的優先）
        3. 避免重複
        
        範例：
        - "Ohtani 跟 Judge 比較" → ["Shohei Ohtani", "Aaron Judge"]
        - "大谷 2023 全壘打" → ["Shohei Ohtani"]
        - "Yamamoto 防禦率" → ["Yoshinobu Yamamoto"]
        """
        players = []
        q_lower = query.lower()
        
        # 按別名長度排序（長的優先匹配，避免 "Shohei Ohtani" 被 "Ohtani" 提前匹配）
        sorted_aliases = sorted(self.player_index.items(), key=lambda x: len(x[0]), reverse=True)
        
        for alias, full_name in sorted_aliases:
            if alias in q_lower:
                if full_name not in players:  # 避免重複
                    players.append(full_name)
                    # 從查詢中移除已匹配的別名，避免重複匹配
                    q_lower = q_lower.replace(alias, "", 1)
        
        return players

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
    # v2 改進：更完整的 Comparison 判斷
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

        # 抽取球員（使用新的方法）
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


# ------------------------------------------------------------
# CLI 測試
# ------------------------------------------------------------
if __name__ == "__main__":
    qr = QueryRouter()
    
    print("\n" + "=" * 60)
    print("Query Router v2 測試（混合方案）")
    print("=" * 60)
    
    test_queries = [
        # 英文名字測試
        "Yamamoto 防禦率",
        "Judge 2024 HR",
        "Ohtani 跟 Judge 打擊率比較",
        
        # 中文名字測試
        "大谷 2022 2023 全壘打",
        "山本 投球表現",
        
        # 姓氏測試
        "Ohtani power 表現",
        "Judge 整體數據",
        
        # 多球員測試
        "大谷 山本 比較",
        
        # Ranking 測試
        "2024 全壘打前 10 名",
        
        # 沒有球員的查詢
        "2023 ERA 前 5 名",
    ]
    
    for q in test_queries:
        print(f"\n{'─' * 60}")
        print(f"查詢: {q}")
        routed = qr.route(q)
        print(f"  Type: {routed['query_type']}")
        print(f"  Players: {routed['players']}")
        print(f"  Seasons: {routed['seasons']}")
        print(f"  Metric: {routed['metric']}")
        print(f"  Top N: {routed['top_n']}")
        
        # 驗證球員是否正確識別
        if routed['players']:
            print(f"  ✅ 成功識別 {len(routed['players'])} 位球員")
        else:
            print(f"  ⚠️ 沒有識別到球員")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
    
    # 互動式測試
    print("\n輸入查詢測試（或 Enter 離開）：")
    while True:
        try:
            q = input("> ").strip()
        except EOFError:
            break

        if not q:
            break

        routed = qr.route(q)
        print("\n--- Routed Result ---")
        print(json.dumps(routed, ensure_ascii=False, indent=2))