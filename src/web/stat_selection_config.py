"""
統計數據智能選擇配置

使用方法：
1. 新增 Metric 組合 → 編輯 METRIC_RELATED_STATS
2. 新增查詢關鍵字 → 編輯 QUERY_KEYWORD_MAPPING
3. 新增統計類別 → 編輯 CATEGORY_STATS
4. 修改預設指標 → 編輯 DEFAULT_STATS
5. 分析問題 → 統計數據映射，修改 ANALYSIS_PROBLEM_STATS
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


# ============================================================
# 問題類型自動識別
# ============================================================
PROBLEM_KEYWORDS = {
    # 投手問題
    "壓制力不足": ["壓制", "壓制力", "三振", "被打", "被安打", "dominance", "strikeout"],
    "控球問題": ["控球", "保送", "四壞", "walk", "control", "command"],
    "被長打": ["長打", "全壘打", "二壘打", "被轟", "home run", "power", "slugging"],
    "防禦率高": ["防禦率", "era", "失分", "自責分"],
    "體力問題": ["後段", "第三輪", "投球局數", "疲勞", "stamina", "fatigue"],
    
    # 打者問題
    "打擊率低": ["打擊率", "安打", "avg", "batting average", "contact"],
    "長打力不足": ["長打", "全壘打", "power", "slugging", "iso"],
    "選球不佳": ["選球", "保送", "三振", "discipline", "patience", "walk"],
    "不擅長應付": ["對抗", "對決", "應付", "面對", "against", "vs"],
    "近況低迷": ["最近", "近期", "近況", "lately", "recently", "slump"],
}


# ============================================================
# 問題類型 → 分析數據映射
# ============================================================
ANALYSIS_PROBLEM_STATS = {
    # === 投手問題分析 ===
    "壓制力不足": {
        "main_stats": ["K%", "K/9", "CSW%", "SwStr%"],       # 主要診斷指標
        "supporting_stats": ["HardHit%", "Barrel%", "EV"],   # 支援分析
        "comparison_baseline": "league_avg",                  # 比較基準
        "analysis_focus": [
            "三振能力是否下降",
            "好球揮空率是否偏低",
            "被強擊球比例是否過高"
        ]
    },
    
    "控球問題": {
        "main_stats": ["BB%", "BB/9", "Zone%", "F-Strike%"],
        "supporting_stats": ["WHIP", "K/BB", "O-Contact%"],
        "comparison_baseline": "league_avg",
        "analysis_focus": [
            "保送率是否過高",
            "好球帶進壘率是否不足",
            "首球好球率是否偏低"
        ]
    },
    
    "被長打": {
        "main_stats": ["HR/9", "ISO_Against", "Barrel%", "FB%"],
        "supporting_stats": ["EV", "HardHit%", "LA"],
        "comparison_baseline": "league_avg",
        "analysis_focus": [
            "被全壘打率是否偏高",
            "被擊球初速是否過快",
            "飛球比例是否過高"
        ]
    },
    
    "防禦率高": {
        "main_stats": ["ERA", "FIP", "xFIP", "BABIP"],
        "supporting_stats": ["LOB%", "HR/9", "WHIP"],
        "comparison_baseline": "league_avg",
        "analysis_focus": [
            "防禦率是否高於預期（FIP/xFIP）",
            "場內打擊率是否異常",
            "殘壘率是否偏低（運氣因素）"
        ]
    },
    
    "體力問題": {
        "main_stats": ["IP", "Pitches", "TTO%", "QS"],
        "supporting_stats": ["vFA", "K%", "BB%"],  # vFA = 球速
        "comparison_baseline": "first_3_innings",
        "analysis_focus": [
            "後段局數表現是否明顯下降",
            "球速是否遞減",
            "三振/保送比例變化"
        ]
    },
    
    # === 打者問題分析 ===
    "打擊率低": {
        "main_stats": ["AVG", "BABIP", "Contact%", "K%"],
        "supporting_stats": ["LD%", "GB%", "IF/FB"],
        "comparison_baseline": "league_avg",
        "analysis_focus": [
            "接觸率是否不足",
            "場內打擊率是否偏低（運氣）",
            "擊球型態是否不理想"
        ]
    },
    
    "長打力不足": {
        "main_stats": ["ISO", "SLG", "HR", "Barrel%"],
        "supporting_stats": ["EV", "maxEV", "HardHit%", "LA"],
        "comparison_baseline": "league_avg",
        "analysis_focus": [
            "出棒初速是否不足",
            "強擊球率是否偏低",
            "擊球仰角是否不理想"
        ]
    },
    
    "選球不佳": {
        "main_stats": ["BB%", "K%", "O-Swing%", "Z-Swing%"],
        "supporting_stats": ["Chase%", "Contact%", "SwStr%"],
        "comparison_baseline": "league_avg",
        "analysis_focus": [
            "壞球追打率是否過高",
            "保送率是否不足",
            "揮空率是否偏高"
        ]
    },
    
    "不擅長應付": {
        "main_stats": ["AVG", "OPS", "K%", "wOBA"],
        "supporting_stats": ["ISO", "BB%", "Contact%"],
        "comparison_baseline": "vs_other_pitchers",
        "analysis_focus": [
            "特定對手表現是否明顯下降",
            "打擊紀律是否改變",
            "長打能力是否受壓制"
        ]
    },
    
    "近況低迷": {
        "main_stats": ["AVG", "OPS", "wRC+", "K%"],
        "supporting_stats": ["BABIP", "HardHit%", "EV"],
        "comparison_baseline": "season_avg",
        "analysis_focus": [
            "近期表現與賽季平均比較",
            "運氣因素（BABIP）是否異常",
            "擊球品質是否下降"
        ]
    },
}


# ============================================================
# 自動識別問題類型
# ============================================================
def detect_problem_type(query: str) -> str:
    """
    從查詢中識別問題類型
    
    Args:
        query: 用戶查詢字串
    
    Returns:
        問題類型（如 "壓制力不足"）或 None
    """
    query_lower = query.lower()
    
    # 按關鍵字匹配度排序（越多匹配越優先）
    matches = []
    
    for problem_type, keywords in PROBLEM_KEYWORDS.items():
        match_count = sum(1 for kw in keywords if kw.lower() in query_lower)
        if match_count > 0:
            matches.append((problem_type, match_count))
    
    if matches:
        # 返回匹配度最高的問題類型
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]
    
    return None


# ============================================================
# 獲取分析所需的統計數據
# ============================================================
def get_analysis_stats(problem_type: str) -> dict:
    """
    獲取特定問題類型需要的統計數據
    
    Args:
        problem_type: 問題類型
    
    Returns:
        統計數據配置字典
    """
    if problem_type not in ANALYSIS_PROBLEM_STATS:
        # 預設返回通用分析數據
        return {
            "main_stats": ["AVG", "OPS", "wRC+"],
            "supporting_stats": ["K%", "BB%", "ISO"],
            "comparison_baseline": "league_avg",
            "analysis_focus": ["整體表現評估"]
        }
    
    return ANALYSIS_PROBLEM_STATS[problem_type]


# ============================================================
# 測試
# ============================================================
if __name__ == "__main__":
    test_queries = [
        "大谷2023年投球壓制力為什麼下降",
        "Yamamoto的控球有什麼問題",
        "Judge最近打擊率怎麼這麼低",
        "分析Ohtani的長打力表現",
    ]
    
    print("=" * 60)
    print("問題類型識別測試")
    print("=" * 60)
    
    for query in test_queries:
        problem_type = detect_problem_type(query)
        print(f"\n查詢: {query}")
        print(f"問題類型: {problem_type}")
        
        if problem_type:
            stats = get_analysis_stats(problem_type)
            print(f"主要指標: {stats['main_stats']}")
            print(f"支援指標: {stats['supporting_stats']}")
            print(f"分析重點: {stats['analysis_focus'][0]}")



