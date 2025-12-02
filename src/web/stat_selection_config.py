"""
統計數據智能選擇配置

使用方法：
1. 新增 Metric 組合 → 編輯 METRIC_RELATED_STATS
2. 新增查詢關鍵字 → 編輯 QUERY_KEYWORD_MAPPING
3. 新增統計類別 → 編輯 CATEGORY_STATS
4. 修改預設指標 → 編輯 DEFAULT_STATS
"""

# ============================================================
# 1. Metric 相關統計（當查詢明確指定 metric 時）
# ============================================================
METRIC_RELATED_STATS = {
    # 打者 - 打擊率相關
    "AVG": ["AVG", "OBP", "BABIP", "wOBA"],
    "OBP": ["OBP", "AVG", "BB%", "wOBA"],
    "SLG": ["SLG", "ISO", "HR", "XBH"],
    "OPS": ["OPS", "wOBA", "wRC+", "AVG"],
    "BABIP": ["BABIP", "AVG", "HardHit%", "LD%"],
    
    # 打者 - 長打相關
    "HR": ["HR", "ISO", "SLG", "Barrel%"],
    "ISO": ["ISO", "HR", "SLG", "HardHit%"],
    "Barrel%": ["Barrel%", "HardHit%", "EV", "HR"],
    
    # 打者 - 紀律相關
    "BB%": ["BB%", "K%", "OBP", "Swing%"],
    "K%": ["K%", "BB%", "Contact%", "Chase%"],
    "wOBA": ["wOBA", "wRC+", "OPS", "AVG"],
    "wRC+": ["wRC+", "wOBA", "OPS", "WAR"],
    
    # 打者 - Statcast
    "EV": ["EV", "LA", "Barrel%", "HardHit%"],
    "LA": ["LA", "EV", "FB%", "GB%"],
    "HardHit%": ["HardHit%", "EV", "Barrel%", "ISO"],
    
    # 打者 - 其他
    "WAR": ["WAR", "wRC+", "OPS", "Def"],
    "RBI": ["RBI", "HR", "wRC+", "Clutch"],
    "SB": ["SB", "Spd", "SB%", "BsR"],
    
    # 投手 - 防禦相關
    "ERA": ["ERA", "FIP", "xFIP", "SIERA"],
    "FIP": ["FIP", "xFIP", "ERA", "K%"],
    "xFIP": ["xFIP", "FIP", "ERA", "FB%"],
    "SIERA": ["SIERA", "xFIP", "FIP", "K-BB%"],
    "WHIP": ["WHIP", "BB/9", "H/9", "FIP"],
    
    # 投手 - 三振相關
    "K%": ["K%", "K/9", "CSW%", "SwStr%"],
    "K/9": ["K/9", "K%", "SO", "CSW%"],
    "SO": ["SO", "K/9", "K%", "IP"],
    "CSW%": ["CSW%", "K%", "Chase%", "SwStr%"],
    
    # 投手 - 控球相關
    "BB%": ["BB%", "BB/9", "WHIP", "K-BB%"],
    "BB/9": ["BB/9", "BB%", "WHIP", "FIP"],
    "K/BB": ["K/BB", "K%", "BB%", "K-BB%"],
    
    # 投手 - Statcast
    "EV_Against": ["EV", "HardHit%", "Barrel%", "xERA"],
    "Barrel%_Against": ["Barrel%", "HardHit%", "EV", "HR/9"],
    
    # 投手 - 其他
    "W": ["W", "L", "ERA", "QS"],
    "SV": ["SV", "ERA", "WHIP", "K/9"],
    "IP": ["IP", "GS", "QS", "Pitches"],
}

# ============================================================
# 2. 查詢關鍵字映射（當查詢包含特定關鍵字時）
# ============================================================
QUERY_KEYWORD_MAPPING = {
    # 中文關鍵字 - 按優先級排序（更具體的在前）
    "投球控球": "pitching_control",  
    "投手控球": "pitching_control",
    "投手三振": "pitching_strikeout",  
    "壓制力": "pitching_dominance",
    "全壘打": "power_hr",
    "長打": "power_slugging",
    "強擊": "power_barrel",
    "打擊率": "contact_average",
    "打擊": "contact_core",
    "安打": "contact_hits",
    "上壘": "contact_obp",
    "選球": "discipline_walks",
    "紀律": "discipline_patience",
    "三振": "discipline_strikeout",  
    "保送": "discipline_walks",
    "速度": "speed_running",
    "盜壘": "speed_stealing",
    "跑壘": "speed_baserunning",
    "防禦": "pitching_era",
    "投球": "pitching_core",
    "控球": "pitching_control",  
    "壓制": "pitching_dominance",
    "出棒": "statcast_exit",
    "擊球": "statcast_contact",
    "仰角": "statcast_launch",
    "進階": "advanced_metrics",
    "整體": "overall_performance",
    
    # 英文關鍵字
    "pitching control": "pitching_control",  
    "pitcher control": "pitching_control",
    "pitcher strikeout": "pitching_strikeout",  
    "dominance": "pitching_dominance",
    "home run": "power_hr",
    "power": "power_slugging",
    "slugging": "power_slugging",
    "barrel": "power_barrel",
    "average": "contact_average",
    "batting": "contact_core",
    "hitting": "contact_core",
    "contact": "contact_hits",
    "on-base": "contact_obp",
    "discipline": "discipline_patience",
    "walk": "discipline_walks",
    "strikeout": "discipline_strikeout",  
    "whiff": "discipline_strikeout",
    "speed": "speed_running",
    "steal": "speed_stealing",
    "running": "speed_baserunning",
    "era": "pitching_era",
    "pitching": "pitching_core",
    "control": "pitching_control",  
    "command": "pitching_control",
    "exit velocity": "statcast_exit",
    "launch angle": "statcast_launch",
    "statcast": "statcast_overall",
    "advanced": "advanced_metrics",
    "overall": "overall_performance",
}

# ============================================================
# 3. 統計類別定義（關鍵字對應的統計組）
# ============================================================
CATEGORY_STATS = {
    # 打者 - 長打力
    "power_hr": ["HR", "ISO", "SLG", "Barrel%"],
    "power_slugging": ["SLG", "ISO", "XBH", "HR"],
    "power_barrel": ["Barrel%", "HardHit%", "EV", "ISO"],
    
    # 打者 - 接觸能力
    "contact_average": ["AVG", "OBP", "BABIP", "Contact%"],
    "contact_core": ["AVG", "OBP", "SLG", "OPS"],
    "contact_hits": ["H", "AVG", "1B", "XBH"],
    "contact_obp": ["OBP", "AVG", "BB%", "wOBA"],
    
    # 打者 - 選球紀律
    "discipline_patience": ["BB%", "K%", "O-Swing%", "Z-Swing%"],
    "discipline_walks": ["BB%", "OBP", "BB", "BB/K"],
    "discipline_strikeout": ["K%", "Contact%", "SwStr%", "CSW%"],
    
    # 打者 - 速度
    "speed_running": ["Spd", "Sprint Speed", "BsR", "SB"],
    "speed_stealing": ["SB", "SB%", "Spd", "BsR"],
    "speed_baserunning": ["BsR", "Spd", "XBT%", "GDP"],
    
    # 打者 - Statcast
    "statcast_exit": ["EV", "maxEV", "HardHit%", "Barrel%"],
    "statcast_launch": ["LA", "FB%", "GB%", "LD%"],
    "statcast_contact": ["HardHit%", "Barrel%", "EV", "Sweet Spot%"],
    "statcast_overall": ["EV", "LA", "Barrel%", "xwOBA"],
    
    # 投手 - 防禦
    "pitching_era": ["ERA", "FIP", "xFIP", "SIERA"],
    "pitching_core": ["ERA", "WHIP", "K/9", "FIP"],
    
    # 投手 - 三振/壓制
    "pitching_dominance": ["K%", "K/9", "CSW%", "SwStr%"],
    "pitching_strikeout": ["K%", "K/9", "SO", "K-BB%"],
    
    # 投手 - 控球
    "pitching_control": ["BB%", "BB/9", "WHIP", "K/BB"],
    "pitching_command": ["BB%", "Zone%", "F-Strike%", "WHIP"],
    
    # 進階指標
    "advanced_metrics": ["wRC+", "wOBA", "WAR", "OPS+"],
    "overall_performance": ["WAR", "wRC+", "OPS", "wOBA"],
}

# ============================================================
# 4. 預設統計（無關鍵字時使用）
# ============================================================
DEFAULT_STATS = {
    "batter": ["AVG", "HR", "OPS", "wRC+"],
    "pitcher": ["ERA", "WHIP", "K%", "FIP"],
}

# ============================================================
# 5. 統計說明（可選，用於生成解釋）
# ============================================================
STAT_DESCRIPTIONS = {
    # 打者
    "AVG": "打擊率",
    "OBP": "上壘率",
    "SLG": "長打率",
    "OPS": "整體攻擊指數",
    "HR": "全壘打",
    "ISO": "長打力",
    "wOBA": "加權上壘率",
    "wRC+": "加權得分創造（100=平均）",
    "WAR": "勝場貢獻值",
    "Barrel%": "強勁擊球率",
    "HardHit%": "強擊球率",
    "EV": "出棒初速",
    "LA": "擊球仰角",
    "K%": "三振率",
    "BB%": "保送率",
    "BABIP": "場內打擊率",
    "Spd": "速度分數",
    "SB": "盜壘",
    "RBI": "打點",
    
    # 投手
    "ERA": "防禦率",
    "FIP": "投手獨立防禦率",
    "xFIP": "預期FIP",
    "SIERA": "技能互動ERA",
    "WHIP": "每局被上壘率",
    "K/9": "每九局三振",
    "BB/9": "每九局保送",
    "K/BB": "三振保送比",
    "K%": "三振率（投手）",
    "BB%": "保送率（投手）",
    "CSW%": "好球揮空率",
    "SwStr%": "揮空率",
    "W": "勝場",
    "L": "敗場",
    "SV": "救援成功",
    "IP": "投球局數",
}


# ============================================================
# 6. 越低越好的指標（Lower is Better）
# ============================================================
LOWER_IS_BETTER_STATS = {
    # 投手指標（越低越好）
    "ERA", "FIP", "xFIP", "SIERA", "WHIP",
    "BB/9", "H/9", "HR/9", "BB%",
    "ERA-", "FIP-", "xFIP-",  # minus 版本（100 以下越好）
    "BABIP",  # 通常越低越好（投手）
    "O-Contact%",  # 追打率越低越好
    "Z-Swing%",  # 好球區揮棒率（投手希望打者少揮）
    
    # 打者指標（越低越好）
    "K%",  # 三振率（打者）
    "O-Swing%",  # 壞球揮棒率
    "Chase%",  # 追打率
    "SwStr%",  # 揮空率（打者）
    "GDP",  # 雙殺打
}


def is_lower_better(stat_key):
    """判斷該統計是否越低越好"""
    return stat_key in LOWER_IS_BETTER_STATS


# ============================================================
# 主函數：智能選擇統計數據
# ============================================================
def select_stats_for_comparison(routed, common_type):
    """
    根據查詢內容智能選擇要顯示的統計數據
    
    優先級：
    1. 查詢明確指定的 metric → 使用 METRIC_RELATED_STATS
    2. 查詢包含特定關鍵字 → 使用 CATEGORY_STATS（考慮球員類型）
    3. 預設核心指標 → 使用 DEFAULT_STATS
    
    Args:
        routed: QueryRouter 返回的路由資訊
        common_type: 球員類型 ("batter" or "pitcher")
    
    Returns:
        list: 要顯示的統計指標列表
    """
    # 1. 檢查是否指定了 metric
    metric = routed.get("metric")
    if metric and metric in METRIC_RELATED_STATS:
        print(f"   📊 根據 metric '{metric}' 選擇統計")
        return METRIC_RELATED_STATS[metric]
    
    # 2. 檢查查詢關鍵字（按從長到短排序，優先匹配更具體的關鍵字）
    query = routed.get("original_query", "").lower()
    
    # 先嘗試匹配多字關鍵字（更具體）
    keywords_sorted = sorted(QUERY_KEYWORD_MAPPING.items(), 
                            key=lambda x: len(x[0]), 
                            reverse=True)
    
    for keyword, category in keywords_sorted:
        if keyword in query:
            if category in CATEGORY_STATS:
                # ⭐ 特殊處理：三振可能是打者或投手
                if category == "discipline_strikeout" and common_type == "pitcher":
                    # 如果是投手，改用投手三振類別
                    if "pitching_strikeout" in CATEGORY_STATS:
                        print(f"   📊 根據關鍵字 '{keyword}' + 類型 '{common_type}' → 類別 'pitching_strikeout'")
                        return CATEGORY_STATS["pitching_strikeout"]
                
                print(f"   📊 根據關鍵字 '{keyword}' → 類別 '{category}'")
                return CATEGORY_STATS[category]
    
    # 3. 預設核心指標
    print(f"   📊 使用預設核心指標")
    return DEFAULT_STATS.get(common_type, ["AVG", "HR", "OPS"])


def get_stat_description(stat_key):
    """獲取統計指標的中文說明"""
    return STAT_DESCRIPTIONS.get(stat_key, stat_key)


# ============================================================
# 使用範例
# ============================================================
if __name__ == "__main__":
    # 測試不同查詢
    test_cases = [
        {
            "original_query": "Ohtani 跟 Judge 全壘打比較", 
            "metric": None, 
            "type": "batter",
            "expected": ["HR", "ISO", "SLG", "Barrel%"]
        },
        {
            "original_query": "比較打擊率", 
            "metric": "AVG", 
            "type": "batter",
            "expected": ["AVG", "OBP", "BABIP", "wOBA"]
        },
        {
            "original_query": "Yamamoto 防禦率", 
            "metric": "ERA", 
            "type": "pitcher",
            "expected": ["ERA", "FIP", "xFIP", "SIERA"]
        },
        {
            "original_query": "投球控球比較", 
            "metric": None, 
            "type": "pitcher",
            "expected": ["BB%", "BB/9", "WHIP", "K/BB"]
        },
        {
            "original_query": "整體表現", 
            "metric": None, 
            "type": "batter",
            "expected": ["WAR", "wRC+", "OPS", "wOBA"]
        },
        {
            "original_query": "速度比較",
            "metric": None,
            "type": "batter",
            "expected": ["Spd", "Sprint Speed", "BsR", "SB"]
        },
        {
            "original_query": "三振比較",
            "metric": None,
            "type": "pitcher",
            "expected": ["K%", "K/9", "SO", "K-BB%"]
        },
    ]
    
    print("=" * 60)
    print("統計數據選擇測試")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {case['original_query']}")
        print(f"  類型: {case['type']}")
        print(f"  Metric: {case.get('metric', 'None')}")
        
        stats = select_stats_for_comparison(case, case["type"])
        expected = case.get("expected", [])
        
        print(f"  選擇: {stats}")
        
        if expected:
            if stats == expected:
                print(f"  ✅ PASS")
                passed += 1
            else:
                print(f"  ❌ FAIL - 預期: {expected}")
                failed += 1
        else:
            print(f"  ⚠️  無預期結果")
    
    print("\n" + "=" * 60)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    print("=" * 60)
    
    # 測試 is_lower_better
    print("\n\n越低越好測試:")
    test_stats = ["ERA", "HR", "K%", "AVG", "WHIP", "OPS"]
    for stat in test_stats:
        result = is_lower_better(stat)
        print(f"  {stat}: {'越低越好' if result else '越高越好'}")
