# ================================================
# Lookup Engine (修正版 + Class 包裝)
# 支援 factual / ranking / comparison 查詢
# ================================================

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
    "全壘打": "HR",
    "全壘打數": "HR",
    "安打": "HITS",
    "得分": "R",
    "打點": "RBI",
    "盜壘": "SB",
    "三振": "SO",
    "保送": "BB",
    "打擊率": "AVG",
    "上壘率": "OBP",
    "長打率": "SLG",
    "OPS": "OPS",
    "ISO": "ISO",
    "BABIP": "BABIP",
    "WOBA": "wOBA",
    "WRC+": "wRC+",
    "防禦率": "ERA",
    "ERA": "ERA",
    "FIP": "FIP",
    "XFIP": "xFIP",
    "SIERA": "SIERA",
    "WHIP": "WHIP",
}


# ------------------------------------------------
# LookupEngine Class
# ------------------------------------------------
class LookupEngine:

    def __init__(self):
        ROOT = Path(__file__).resolve().parents[2]
        train_path = ROOT / "data" / "mlb_data_adv" / "training_data.json"

        with open(train_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        print(f"[LookupEngine] Loaded {len(self.data)} records.")


    # ----------------------------
    # metric 標準化
    # ----------------------------
    def normalize_metric(self, metric: str):
        if not metric:
            return None
        metric = metric.strip().upper()

        # 中文→英文
        lower = metric.lower()
        if lower in METRIC_ALIAS:
            return METRIC_ALIAS[lower]
        if metric in METRIC_ALIAS:
            return METRIC_ALIAS[metric]

        return metric


    # ----------------------------
    # factual 查詢（單一值）
    # ----------------------------
    def lookup_value(self, record, metric):
        metric = self.normalize_metric(metric)
        if metric is None:
            return None

        stats = record["stats"]

        # 完整相同 key
        if metric in stats:
            return stats[metric]

        # 大小寫忽略搜索
        for k, v in stats.items():
            if k.lower() == metric.lower():
                return v

        return None


    # ----------------------------
    # 排序方式判定
    # ----------------------------
    def is_lower_better(self, metric):
        metric = self.normalize_metric(metric)
        return metric in LOWER_IS_BETTER


    # ----------------------------
    # Ranking 查詢（top N）
    # ----------------------------
    def rank(self, season: int, metric: str, top_n: int = 10, ptype=None):
        metric = self.normalize_metric(metric)
        rows = []

        for rec in self.data:
            if rec["season"] != season:
                continue
            if ptype and rec["type"] != ptype:
                continue

            val = self.lookup_value(rec, metric)
            if isinstance(val, (int, float)):
                rows.append((rec, val))

        # 排序邏輯
        if self.is_lower_better(metric):
            rows.sort(key=lambda x: x[1])         # 越低越好
        else:
            rows.sort(key=lambda x: x[1], reverse=True)

        return rows[:top_n]


    # ----------------------------
    # 找球員紀錄（含大谷投打分離）
    # ----------------------------
    def find_player_record(self, name: str, season: int, ptype=None):
        name = name.lower()

        # 精準 match type
        for rec in self.data:
            if rec["player_name"].lower() == name and rec["season"] == season:
                if ptype is None or rec["type"] == ptype:
                    return rec

        # fallback（大谷沒有投球年份）
        for rec in self.data:
            if rec["player_name"].lower() == name and rec["season"] == season:
                return rec

        return None


    # ----------------------------
    # Comparison：回傳玩家本身的該指標
    # ----------------------------
    def compare(self, players: list, season: int, metric: str, ptype=None):
        metric = self.normalize_metric(metric)
        results = []

        for name in players:
            rec = self.find_player_record(name, season, ptype)
            if rec is None:
                continue

            val = self.lookup_value(rec, metric)
            if isinstance(val, (int, float)):
                results.append((rec, val))

        return results


    # ----------------------------
    # 找出比某人高（或低）的球員
    # ----------------------------
    def find_relative_players(self, base_record, metric, season, ptype=None):
        metric = self.normalize_metric(metric)
        base_value = self.lookup_value(base_record, metric)

        if base_value is None or not isinstance(base_value, (int, float)):
            return []

        rows = []
        lower_better = self.is_lower_better(metric)

        for rec in self.data:
            if rec["season"] != season:
                continue
            if ptype and rec["type"] != ptype:
                continue

            val = self.lookup_value(rec, metric)
            if not isinstance(val, (int, float)):
                continue

            if lower_better:
                if val < base_value:
                    rows.append((rec, val))
            else:
                if val > base_value:
                    rows.append((rec, val))

        # 排序
        if lower_better:
            rows.sort(key=lambda x: x[1])
        else:
            rows.sort(key=lambda x: x[1], reverse=True)

        return rows
