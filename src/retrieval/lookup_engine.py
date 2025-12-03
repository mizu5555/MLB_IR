# ============================================================
# Lookup Engine v2 (v6.0.3 Bug Fix)
# 修正：
# 1. rank() 函數正確排序（Bug 1）
# 2. 保留 v6.0.2 的所有功能
# ============================================================

import json
from pathlib import Path

# -----------------------------------------------
# 自動判斷哪些指標越低越好
# -----------------------------------------------
LOWER_IS_BETTER = {
    "ERA", "FIP", "xFIP", "SIERA", "ERA-", "FIP-", "xFIP-",
    "WHIP", "BB/9", "HR/9", "BB%",
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
            print(f"[LookupEngine] Loaded {len(self.data)} records.")
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

    # ⭐⭐⭐ v6.0.3: 修正 Bug 1 - Ranking 正確排序 ⭐⭐⭐
    def rank(self, season, metric, top_n=10, ptype=None):
        """
        Ranking 查詢
        
        v6.0.3 修正：
        1. 確保排序邏輯正確（越高越好 vs 越低越好）
        2. 過濾無效值（None, N/A）
        3. 返回結果保持排序
        """
        metric = self.normalize_metric(metric)
        if metric is None:
            return []
        
        rows = []
        
        for rec in self.data:
            # 篩選條件：季節、類型
            if str(rec.get("season")) != str(season):
                continue
            if ptype and rec.get("type") != ptype:
                continue
            
            # 取得 metric 值
            val = self.lookup_value(rec, metric)
            
            # ⭐ 過濾無效值
            if val is None or val == "N/A":
                continue
            
            # 確保是數值
            try:
                val = float(val)
            except (ValueError, TypeError):
                continue
            
            rows.append((rec, val))
        
        # ⭐⭐⭐ 關鍵修正：正確排序 ⭐⭐⭐
        if self.is_lower_better(metric):
            # 越低越好（ERA, FIP, WHIP...）
            rows.sort(key=lambda x: x[1])  # 升序
        else:
            # 越高越好（HR, AVG, OPS...）
            rows.sort(key=lambda x: x[1], reverse=True)  # 降序
        
        # ⭐ 返回前 N 筆（保持排序）
        return rows[:top_n]

    # Ranking (從 routed_data 調用)
    def ranking(self, routed_data):
        """
        從 routed_data 提取參數並調用 rank()
        """
        metric = routed_data.get("metric")
        season = routed_data.get("seasons", [2023])[0]
        top_n = routed_data.get("top_n", 10)
        
        return self.rank(season=season, metric=metric, top_n=top_n)

    # Comparison
    def comparison(self, routed_data, records=None):
        """
        簡化版 comparison，找出符合條件的球員列表
        """
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


# ============================================================
# CLI 測試
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Lookup Engine v2 測試")
    print("=" * 60)
    
    lookup = LookupEngine()
    
    # 測試 Bug 1: Ranking 排序
    print("\n測試 1: 2024 全壘打前 10 名（應該從高到低）")
    results = lookup.rank(season=2024, metric="HR", top_n=10)
    for i, (rec, val) in enumerate(results, 1):
        print(f"  {i}. {rec['player_name']} - {val}")
    
    print("\n測試 2: 2023 防禦率前 3 名（應該從低到高）")
    results = lookup.rank(season=2023, metric="ERA", top_n=3)
    for i, (rec, val) in enumerate(results, 1):
        print(f"  {i}. {rec['player_name']} - {val}")
    
    print("\n✅ 測試完成")