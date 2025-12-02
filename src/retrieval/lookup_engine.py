# src/retrieval/lookup_engine.py
import json
from pathlib import Path

# -----------------------------------------------
# 自動判斷哪些指標越低越好
# -----------------------------------------------
LOWER_IS_BETTER = {
    "ERA", "FIP", "xFIP", "SIERA", "ERA-", "FIP-", "xFIP-",
    "WHIP", "BB/9", "HR/9",
}

# ------------------------------------------------
# 中文 → 英文 metric 映射
# ------------------------------------------------
METRIC_ALIAS = {
    "全壘打": "HR", "安打": "HITS", "得分": "R", "打點": "RBI", "盜壘": "SB",
    "三振": "SO", "保送": "BB", "打擊率": "AVG", "上壘率": "OBP", "長打率": "SLG",
    "OPS": "OPS", "ISO": "ISO", "BABIP": "BABIP", "WOBA": "wOBA", "WRC+": "wRC+",
    "防禦率": "ERA", "ERA": "ERA", "FIP": "FIP", "WHIP": "WHIP",
    "出棒速度": "ExitVelocity", "擊球仰角": "LaunchAngle"
}

class LookupEngine:
    def __init__(self):
        # 定義絕對路徑，避免相對路徑錯誤
        self.root = Path(__file__).resolve().parents[2]
        self.data_path = self.root / "data" / "mlb_data_adv" / "training_data.json"
        
        self.data = []
        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            print(f"✅ LookupEngine Loaded {len(self.data)} records.")
        else:
            print(f"⚠️ Warning: Training data not found at {self.data_path}")

    def normalize_metric(self, metric: str):
        if not metric: return None
        metric = metric.strip()
        # 英文轉大寫，中文保持原樣查表
        if metric.upper() in METRIC_ALIAS.values(): # 已經是英文縮寫
            return metric.upper()
        return METRIC_ALIAS.get(metric, metric) # 查表或回傳原值

    def lookup_value(self, record, metric):
        norm_metric = self.normalize_metric(metric)
        stats = record.get("stats", {})
        
        # 1. 精確匹配
        if norm_metric in stats: return stats[norm_metric]
        
        # 2. 大小寫模糊匹配
        for k, v in stats.items():
            if k.upper() == str(norm_metric).upper():
                return v
        return None

    def is_lower_better(self, metric):
        norm = self.normalize_metric(metric)
        return norm in LOWER_IS_BETTER

    # Ranking
    def ranking(self, routed_data):
        # 從 routed_data 提取參數
        metric = routed_data.get("metric")
        season = routed_data.get("seasons", [2023])[0]
        top_n = routed_data.get("top_n", 10)
        
        rows = []
        for rec in self.data:
            if str(rec.get("season")) != str(season): continue
            
            val = self.lookup_value(rec, metric)
            if isinstance(val, (int, float)):
                rows.append(rec) # 這裡改回傳 record 物件，方便前端顯示

        # 排序
        metric_name = self.normalize_metric(metric)
        reverse = not self.is_lower_better(metric_name)
        
        rows.sort(key=lambda x: self.lookup_value(x, metric_name), reverse=reverse)
        return rows[:top_n]

    # Comparison
    def comparison(self, routed_data, records=None):
        # 簡化版 comparison，找出符合條件的球員列表
        metric = routed_data.get("metric")
        season = routed_data.get("seasons", [2023])[0]
        target_players = routed_data.get("players", [])
        
        results = []
        for rec in self.data:
            if str(rec.get("season")) != str(season): continue
            
            # 如果有指定球員，只回傳這些球員；沒指定則視為篩選全部
            if target_players:
                # 模糊匹配姓名
                if any(p.lower() in rec["player_name"].lower() for p in target_players):
                    val = self.lookup_value(rec, metric)
                    rec["_temp_val"] = val # 暫存數值方便前端顯示
                    results.append(rec)
            else:
                # 沒指定球員時的邏輯 (例如：找出所有 HR > 30 的人)，這裡暫略
                pass

        return results

    # Factual (單一數據查詢)
    def factual(self, record, metric):
        val = self.lookup_value(record, metric)
        return {
            "player_name": record.get("player_name"),
            "metric": metric,
            "value": val,
            "season": record.get("season"),
            "team": record.get("team")
        }