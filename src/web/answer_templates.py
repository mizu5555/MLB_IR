# ============================================================
# Answer Templates System
# 回答模板系統 - 根據查詢類型生成結構化回答
# ============================================================

def format_factual_answer(player_name, season, metric, value, related_stats, team="", player_type="batter", season_specified=True):
    """
    Factual Query 模板
    
    用途：查詢某球員「特定年份或最新年份」的某一項或多項數據。
    
    參數：
        player_name: 球員姓名
        season: 賽季年份
        metric: 主要查詢指標（如 "ERA", "HR"）
        value: 主要指標的值
        related_stats: dict，相關統計數據 {"FIP": 3.02, "xFIP": 3.21, ...}
        team: 球隊縮寫
        player_type: "batter" 或 "pitcher"
        season_specified: 用戶是否指定了年份
    
    回傳：格式化的回答字串
    """
    
    # 中文指標名稱映射
    METRIC_NAMES_ZH = {
        "ERA": "防禦率（ERA）",
        "FIP": "FIP",
        "xFIP": "xFIP",
        "SIERA": "SIERA",
        "WHIP": "WHIP",
        "K%": "三振率（K%）",
        "BB%": "保送率（BB%）",
        "K/9": "每九局三振（K/9）",
        "BB/9": "每九局保送（BB/9）",
        "HR": "全壘打（HR）",
        "AVG": "打擊率（AVG）",
        "OBP": "上壘率（OBP）",
        "SLG": "長打率（SLG）",
        "OPS": "OPS",
        "ISO": "純長打率（ISO）",
        "wOBA": "wOBA",
        "wRC+": "wRC+",
        "WAR": "WAR",
        "BABIP": "BABIP",
        "Barrel%": "Barrel%",
        "HardHit%": "強擊率（HardHit%）",
        "EV": "平均擊球初速（EV）",
        "LA": "平均發射角度（LA）",
        "Spd": "速度（Spd）",
        "SB": "盜壘（SB）",
    }
    
    # 生成主要回答
    metric_name = METRIC_NAMES_ZH.get(metric, metric)
    team_str = f"（{team}）" if team else ""
    
    if season_specified:
        answer = f"{player_name} 在 {season} 年 MLB 賽季{team_str}的{metric_name}為 **{value}**。\n\n"
    else:
        answer = f"{player_name} 最近一個賽季（{season}）{team_str}的{metric_name}為 **{value}**。\n\n"
    
    # 加入相關數據
    if related_stats:
        player_type_zh = "投球表現" if player_type == "pitcher" else "打擊表現"
        answer += f"其他{player_type_zh}數據：\n"
        
        for key, val in related_stats.items():
            if key != metric:  # 不重複顯示主要指標
                stat_name = METRIC_NAMES_ZH.get(key, key)
                answer += f"- {stat_name}: {val}\n"
    
    answer += "\n其他詳細數據可以參考下方「原始數據來源」。"
    
    return answer


def format_ranking_answer(season, metric, rankings, season_specified=True, player_type="batter"):
    """
    Ranking Query 模板
    
    用途：查詢一整年聯盟排名，如「2023 全壘打前5名」。
    
    參數：
        season: 賽季年份
        metric: 排名指標（如 "HR", "ERA"）
        rankings: list of dict，排名數據
                  [{"rank": 1, "player": "Judge", "value": 58, "team": "NYY"}, ...]
        season_specified: 用戶是否指定了年份
        player_type: "batter" 或 "pitcher"
    
    回傳：格式化的回答字串
    """
    
    METRIC_NAMES_ZH = {
        "ERA": "防禦率（ERA）",
        "FIP": "FIP",
        "WHIP": "WHIP",
        "K%": "三振率（K%）",
        "K/9": "每九局三振（K/9）",
        "HR": "全壘打",
        "AVG": "打擊率",
        "OBP": "上壘率",
        "SLG": "長打率",
        "OPS": "OPS",
        "wRC+": "wRC+",
        "WAR": "WAR",
        "RBI": "打點",
        "SB": "盜壘",
    }
    
    metric_name = METRIC_NAMES_ZH.get(metric, metric)
    
    if season_specified:
        answer = f"以下是 MLB {season} 年的 **{metric_name}** 前 {len(rankings)} 名：\n\n"
    else:
        answer = f"您未指定年份，以下為最新賽季（{season}）的 **{metric_name}** 排名：\n\n"
    
    # 生成排名列表
    for rank_data in rankings:
        rank = rank_data.get("rank", "?")
        player = rank_data.get("player", "Unknown")
        value = rank_data.get("value", "N/A")
        team = rank_data.get("team", "")
        
        team_str = f" ({team})" if team else ""
        answer += f"{rank}. **{player}**{team_str} – {value}\n"
    
    answer += "\n其他詳細數據可以參考下方「原始數據來源」。"
    
    return answer


def format_comparison_answer(metric, comparisons, season=None, comparison_type="multi_player"):
    """
    Comparison Query 模板
    
    用途：比較兩球員、或同一球員兩年份。
    
    參數：
        metric: 比較指標（如 "HR", "ERA"）
        comparisons: list of dict，比較數據
                     [{"player": "Ohtani", "season": 2023, "value": 44, "team": "LAA"}, ...]
        season: 賽季年份（用於多球員比較）
        comparison_type: "multi_player"（多球員）或 "multi_season"（多賽季）
    
    回傳：格式化的回答字串
    """
    
    METRIC_NAMES_ZH = {
        "ERA": "防禦率（ERA）",
        "FIP": "FIP",
        "WHIP": "WHIP",
        "K%": "三振率（K%）",
        "HR": "全壘打",
        "AVG": "打擊率",
        "OBP": "上壘率",
        "SLG": "長打率",
        "OPS": "OPS",
        "wRC+": "wRC+",
        "WAR": "WAR",
    }
    
    metric_name = METRIC_NAMES_ZH.get(metric, metric) if metric else "數據"
    
    if comparison_type == "multi_player":
        # 多球員比較（同年）
        if season:
            answer = f"{season} 年賽季中，**{metric_name}** 比較如下：\n\n"
        else:
            answer = f"**{metric_name}** 比較如下：\n\n"
        
        # 排序（數值由高到低）
        sorted_comparisons = sorted(comparisons, key=lambda x: float(x.get("value", 0)), reverse=True)
        
        for comp in sorted_comparisons:
            player = comp.get("player", "Unknown")
            value = comp.get("value", "N/A")
            team = comp.get("team", "")
            
            team_str = f" ({team})" if team else ""
            answer += f"- **{player}**{team_str}: {value}\n"
        
        # 加入結論
        if len(sorted_comparisons) >= 2:
            best_player = sorted_comparisons[0].get("player", "")
            best_value = sorted_comparisons[0].get("value", "")
            answer += f"\n結論：**{best_player}** 的 {metric_name} 較佳（{best_value}）。\n"
    
    else:
        # 單球員多賽季比較
        player_name = comparisons[0].get("player", "Unknown") if comparisons else "Unknown"
        answer = f"**{player_name}** 在不同賽季的 **{metric_name}** 比較如下：\n\n"
        
        # 按年份排序
        sorted_comparisons = sorted(comparisons, key=lambda x: x.get("season", 0))
        
        for comp in sorted_comparisons:
            season_year = comp.get("season", "?")
            value = comp.get("value", "N/A")
            team = comp.get("team", "")
            
            team_str = f" ({team})" if team else ""
            answer += f"- {season_year}{team_str}: {value}\n"
        
        # 計算差異
        if len(sorted_comparisons) >= 2:
            first_value = float(sorted_comparisons[0].get("value", 0))
            last_value = float(sorted_comparisons[-1].get("value", 0))
            diff = last_value - first_value
            
            if diff > 0:
                answer += f"\n趨勢：從 {sorted_comparisons[0].get('season')} 到 {sorted_comparisons[-1].get('season')} 增加了 **{diff:.2f}**。\n"
            elif diff < 0:
                answer += f"\n趨勢：從 {sorted_comparisons[0].get('season')} 到 {sorted_comparisons[-1].get('season')} 減少了 **{abs(diff):.2f}**。\n"
            else:
                answer += f"\n趨勢：從 {sorted_comparisons[0].get('season')} 到 {sorted_comparisons[-1].get('season')} 維持穩定。\n"
    
    answer += "\n其他詳細數據可以參考下方「原始數據來源」。"
    
    return answer


# ============================================================
# 工具函數：從檢索結果提取數據
# ============================================================

def extract_comparison_data(hits, metric, key_stats):
    """
    從檢索結果中提取比較數據
    
    參數：
        hits: 檢索結果列表
        metric: 主要比較指標
        key_stats: 要提取的統計列表
    
    回傳：list of dict
    """
    comparisons = []
    
    for hit in hits:
        stats = hit.get("stats", {})
        value = stats.get(metric, "N/A")
        
        comparisons.append({
            "player": hit.get("player_name", "Unknown"),
            "season": hit.get("season", ""),
            "value": value,
            "team": hit.get("team", ""),
            "stats": {k: stats.get(k, "N/A") for k in key_stats if k in stats}
        })
    
    return comparisons


def extract_ranking_data(hits, metric):
    """
    從檢索結果中提取排名數據
    
    參數：
        hits: 檢索結果列表（已按 metric 排序）
        metric: 排名指標
    
    回傳：list of dict
    """
    rankings = []
    
    for idx, hit in enumerate(hits, start=1):
        stats = hit.get("stats", {})
        value = stats.get(metric, "N/A")
        
        rankings.append({
            "rank": idx,
            "player": hit.get("player_name", "Unknown"),
            "value": value,
            "team": hit.get("team", ""),
            "season": hit.get("season", "")
        })
    
    return rankings


# ============================================================
# 測試函數
# ============================================================

if __name__ == "__main__":
    # 測試 Factual
    print("=" * 60)
    print("測試 1: Factual Query")
    print("=" * 60)
    answer = format_factual_answer(
        player_name="Yoshinobu Yamamoto",
        season=2024,
        metric="ERA",
        value=3.00,
        related_stats={"FIP": 3.02, "xFIP": 3.21, "SIERA": 3.15},
        team="LAD",
        player_type="pitcher",
        season_specified=True
    )
    print(answer)
    print()
    
    # 測試 Ranking
    print("=" * 60)
    print("測試 2: Ranking Query")
    print("=" * 60)
    rankings = [
        {"rank": 1, "player": "Aaron Judge", "value": 58, "team": "NYY"},
        {"rank": 2, "player": "Kyle Schwarber", "value": 46, "team": "PHI"},
        {"rank": 3, "player": "Shohei Ohtani", "value": 44, "team": "LAA"}
    ]
    answer = format_ranking_answer(
        season=2024,
        metric="HR",
        rankings=rankings,
        season_specified=True
    )
    print(answer)
    print()
    
    # 測試 Comparison (多球員)
    print("=" * 60)
    print("測試 3: Comparison Query (多球員)")
    print("=" * 60)
    comparisons = [
        {"player": "Shohei Ohtani", "season": 2023, "value": 0.304, "team": "LAA"},
        {"player": "Aaron Judge", "season": 2023, "value": 0.267, "team": "NYY"}
    ]
    answer = format_comparison_answer(
        metric="AVG",
        comparisons=comparisons,
        season=2023,
        comparison_type="multi_player"
    )
    print(answer)
    print()
    
    # 測試 Comparison (多賽季)
    print("=" * 60)
    print("測試 4: Comparison Query (多賽季)")
    print("=" * 60)
    comparisons = [
        {"player": "Shohei Ohtani", "season": 2022, "value": 34, "team": "LAA"},
        {"player": "Shohei Ohtani", "season": 2023, "value": 44, "team": "LAA"}
    ]
    answer = format_comparison_answer(
        metric="HR",
        comparisons=comparisons,
        comparison_type="multi_season"
    )
    print(answer)
