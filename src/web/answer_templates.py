# ============================================================
# Answer Templates v3 (v6.0.2 Bug Fix)
# 修正：
# 1. 投手的 AVG 顯示為「被打擊率 (BAA)」而非「打擊率 (AVG)」
# 2. 加強所有模板的 N/A 值處理（過濾 None、"N/A"、空字串）
# 3. format_comparison_answer() 過濾無效數據（解決大谷多賽季崩潰）
# ============================================================

# ------------------------------------------------------------
# Metric 名稱映射（中文顯示）
# ------------------------------------------------------------
METRIC_NAMES_ZH = {
    # 打者指標
    "AVG": "打擊率 (AVG)",
    "OBP": "上壘率 (OBP)",
    "SLG": "長打率 (SLG)",
    "OPS": "OPS",
    "HR": "全壘打 (HR)",
    "RBI": "打點 (RBI)",
    "H": "安打 (H)",
    "R": "得分 (R)",
    "SB": "盜壘 (SB)",
    "BB": "保送 (BB)",
    "SO": "三振 (SO)",
    "wOBA": "wOBA",
    "wRC+": "wRC+",
    "ISO": "ISO",
    "BABIP": "BABIP",
    
    # ⭐ v6.0.2: 投手的 AVG 是「被打擊率」
    "BAA": "被打擊率 (BAA)",
    
    # 投手指標
    "ERA": "防禦率 (ERA)",
    "WHIP": "WHIP",
    "FIP": "FIP",
    "xFIP": "xFIP",
    "SIERA": "SIERA",
    "K/9": "K/9",
    "BB/9": "BB/9",
    "K/BB": "K/BB",
    "IP": "投球局數 (IP)",
    "W": "勝場 (W)",
    "L": "敗場 (L)",
    "SV": "救援成功 (SV)",
    "K%": "三振率 (K%)",
    "BB%": "保送率 (BB%)",
}

# ⭐ v6.0.2: 新增 - 投手指標的 Metric 名稱（用於判斷是否需要轉換 AVG → BAA）
PITCHER_METRICS = {
    "ERA", "WHIP", "FIP", "xFIP", "SIERA",
    "K/9", "BB/9", "K/BB", "IP", "W", "L", "SV",
    "K%", "BB%",
}


# ------------------------------------------------------------
# 工具函式：處理 Metric 名稱（投手 AVG → BAA）
# ------------------------------------------------------------
def get_metric_name(metric: str, player_type: str = None) -> str:
    """
    取得 Metric 的中文名稱
    
    v6.0.2 特殊處理：
    - 如果是投手的 AVG，顯示為「被打擊率 (BAA)」
    - 如果是打者的 AVG，顯示為「打擊率 (AVG)」
    """
    if metric == "AVG" and player_type == "pitcher":
        return "被打擊率 (BAA)"
    
    return METRIC_NAMES_ZH.get(metric, metric)


# ------------------------------------------------------------
# 工具函式：檢查數值是否有效
# ------------------------------------------------------------
def is_valid_value(value):
    """
    檢查數值是否有效（不是 None、N/A、空字串）
    """
    if value is None:
        return False
    if value == "N/A":
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    
    # 嘗試轉換為 float（確保是數值）
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


# ------------------------------------------------------------
# 工具函式：格式化數值
# ------------------------------------------------------------
def format_value(value, metric: str = None):
    """
    格式化數值顯示
    """
    if not is_valid_value(value):
        return "N/A"
    
    try:
        val = float(value)
        
        # 百分比指標（K%, BB%）
        if metric and "%" in metric:
            return f"{val:.1f}%"
        
        # 防禦率、打擊率（3 位小數）
        if metric in ["ERA", "AVG", "OBP", "SLG", "OPS", "WHIP", "FIP", "xFIP", "wOBA", "BABIP"]:
            return f"{val:.3f}"
        
        # 整數（HR, RBI, W, L, SV）
        if metric in ["HR", "RBI", "W", "L", "SV", "H", "R", "SB", "BB", "SO"]:
            return f"{int(val)}"
        
        # 投球局數（1 位小數）
        if metric == "IP":
            return f"{val:.1f}"
        
        # 進階指標（整數或 1 位小數）
        if metric in ["wRC+", "K/9", "BB/9", "K/BB"]:
            if val >= 10:
                return f"{int(val)}"
            else:
                return f"{val:.1f}"
        
        # 預設（3 位小數）
        return f"{val:.3f}"
    
    except:
        return str(value)


# ------------------------------------------------------------
# 1. Factual Query 模板
# ------------------------------------------------------------
def format_factual_answer(
    player_name, season, metric, value, 
    related_stats=None, team=None, player_type=None
):
    """
    Factual 查詢回答模板
    
    v6.0.2 修正：
    1. 處理 N/A 或缺失值
    2. 投手的 AVG 顯示為「被打擊率 (BAA)」
    """
    # ⭐ v6.0.2: 使用 get_metric_name() 處理投手 AVG
    metric_name = get_metric_name(metric, player_type)
    
    # ⭐ 修正：處理 N/A 或缺失值
    if not is_valid_value(value):
        team_str = f"（{team}）" if team else ""
        player_type_zh = "投手" if player_type == "pitcher" else "打者"
        
        # 判斷是否是跨類型查詢（投手被問打者指標 or 打者被問投手指標）
        if metric in PITCHER_METRICS and player_type == "batter":
            return f"{player_name} 在 {season} 年是以打者身份出賽，沒有 {metric_name} 數據。\n\n如果您想查詢投球數據，請指定投球的年份（如果該球員有投球記錄）。"
        elif metric not in PITCHER_METRICS and player_type == "pitcher":
            # 投手被問打者指標
            if metric == "AVG":
                return f"{player_name} 在 {season} 年是以投手身份出賽。\n\n💡 提示：如果您想查詢「被打擊率 (BAA)」，該球員的數據是 {format_value(value, 'BAA')}。如果您想查詢投手的「打擊率 (AVG)」，投手通常不作為主要打者，數據可能不完整。"
            else:
                return f"{player_name} 在 {season} 年是以投手身份出賽，沒有完整的 {metric_name} 數據（投手通常不作為主要打者）。\n\n如果您想查詢打擊數據，請指定打擊的年份。"
        else:
            return f"{player_name} 在 {season} 年{team_str}沒有 {metric_name} 數據。\n\n可能該球員該年度沒有該類型的出賽記錄，或是數據尚未統計完整。"
    
    # 格式化數值
    formatted_value = format_value(value, metric)
    
    # 基本回答
    team_str = f"（{team}）" if team else ""
    answer = f"{player_name} 在 {season} 年{team_str}的 {metric_name} 為 **{formatted_value}**。"
    
    # 如果有相關數據，補充說明
    if related_stats and isinstance(related_stats, dict):
        extra_info = []
        
        # 根據 metric 補充相關數據
        if metric in ["AVG", "OBP", "SLG"]:
            if "OPS" in related_stats:
                extra_info.append(f"OPS: {format_value(related_stats['OPS'], 'OPS')}")
        
        if metric == "HR":
            if "RBI" in related_stats:
                extra_info.append(f"打點 (RBI): {format_value(related_stats['RBI'], 'RBI')}")
        
        if metric == "ERA":
            if "WHIP" in related_stats:
                extra_info.append(f"WHIP: {format_value(related_stats['WHIP'], 'WHIP')}")
            if "K/9" in related_stats:
                extra_info.append(f"K/9: {format_value(related_stats['K/9'], 'K/9')}")
        
        if extra_info:
            answer += "\n\n**相關數據**：" + " | ".join(extra_info)
    
    return answer


# ------------------------------------------------------------
# 2. Ranking Query 模板
# ------------------------------------------------------------
def format_ranking_answer(season, metric, rankings, player_type=None):
    """
    Ranking 查詢回答模板
    
    v6.0.2 修正：
    1. 過濾 N/A 值
    2. 投手的 AVG 顯示為「被打擊率 (BAA)」
    """
    # ⭐ v6.0.2: 使用 get_metric_name()
    metric_name = get_metric_name(metric, player_type)
    
    # ⭐ 修正：過濾 N/A 值
    valid_rankings = []
    for r in rankings:
        val = r.get("value")
        if is_valid_value(val):
            valid_rankings.append(r)
    
    if not valid_rankings:
        return f"沒有找到 {season} 年 {metric_name} 的有效數據。"
    
    # 標題
    answer = f"### {season} 年 {metric_name} 排名前 {len(valid_rankings)} 名\n\n"
    
    # 排名列表
    for i, r in enumerate(valid_rankings, 1):
        player = r.get("player")
        team = r.get("team", "")
        value = r.get("value")
        
        formatted_value = format_value(value, metric)
        team_str = f" ({team})" if team else ""
        
        answer += f"{i}. **{player}**{team_str} - {formatted_value}\n"
    
    return answer


# ------------------------------------------------------------
# 3. Comparison Query 模板
# ------------------------------------------------------------
def format_comparison_answer(metric, comparisons, season=None, comparison_type="multi_player", player_type=None):
    """
    Comparison 查詢回答模板
    
    v6.0.2 修正：
    1. 過濾 N/A 值（解決大谷多賽季崩潰）
    2. 投手的 AVG 顯示為「被打擊率 (BAA)」
    """
    # ⭐ v6.0.2: 使用 get_metric_name()
    metric_name = get_metric_name(metric, player_type)
    
    # ⭐⭐⭐ 關鍵修正：過濾 N/A 值 ⭐⭐⭐
    valid_comparisons = []
    for comp in comparisons:
        val = comp.get("value")
        if is_valid_value(val):
            valid_comparisons.append(comp)
    
    if not valid_comparisons:
        if season:
            return f"沒有找到 {season} 年有效的 {metric_name} 數據進行比較。可能這些球員在指定年份沒有該類型的出賽記錄。"
        else:
            return f"沒有找到有效的 {metric_name} 數據進行比較。可能這些球員在指定年份沒有該類型的出賽記錄。"
    
    # 多球員比較
    if comparison_type == "multi_player":
        if season:
            answer = f"### {season} 年 {metric_name} 比較\n\n"
        else:
            answer = f"### {metric_name} 比較\n\n"
        
        for comp in valid_comparisons:
            player = comp.get("player")
            team = comp.get("team", "")
            value = comp.get("value")
            
            formatted_value = format_value(value, metric)
            team_str = f" ({team})" if team else ""
            
            answer += f"- **{player}**{team_str}: {formatted_value}\n"
        
        return answer
    
    # 單球員多賽季比較
    elif comparison_type == "multi_season":
        player_name = valid_comparisons[0].get("player") if valid_comparisons else "該球員"
        answer = f"### {player_name} 在不同賽季的 {metric_name} 比較\n\n"
        
        for comp in valid_comparisons:
            season = comp.get("season")
            team = comp.get("team", "")
            value = comp.get("value")
            
            formatted_value = format_value(value, metric)
            team_str = f" ({team})" if team else ""
            
            answer += f"- **{season}**{team_str}: {formatted_value}\n"
        
        return answer
    
    return "比較數據準備中..."


# ============================================================
# CLI 測試
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Answer Templates v3 測試")
    print("=" * 60)
    
    # 測試 1: Factual（投手 AVG → BAA）
    print("\n測試 1: 投手 AVG（應該顯示「被打擊率 (BAA)」）")
    answer = format_factual_answer(
        player_name="Yoshinobu Yamamoto",
        season=2024,
        metric="AVG",
        value=0.226,
        team="LAD",
        player_type="pitcher"
    )
    print(answer)
    
    # 測試 2: Factual（N/A 值）
    print("\n測試 2: N/A 值處理")
    answer = format_factual_answer(
        player_name="Shohei Ohtani",
        season=2024,
        metric="ERA",
        value="N/A",
        team="LAD",
        player_type="batter"
    )
    print(answer)
    
    # 測試 3: Comparison（過濾 N/A）
    print("\n測試 3: Comparison 過濾 N/A")
    comparisons = [
        {"player": "Shohei Ohtani", "season": 2022, "value": 44},
        {"player": "Shohei Ohtani", "season": 2023, "value": "N/A"},  # 應該被過濾
        {"player": "Shohei Ohtani", "season": 2024, "value": 54},
    ]
    answer = format_comparison_answer(
        metric="HR",
        comparisons=comparisons,
        comparison_type="multi_season"
    )
    print(answer)
    
    print("\n✅ 測試完成")