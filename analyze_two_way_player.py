"""
演示二刀流球員（如 Shohei Ohtani）的數據處理
"""

import json


def analyze_two_way_player(player_name: str = "Shohei Ohtani"):
    """
    分析二刀流球員的數據結構
    
    Args:
        player_name: 球員名字
    """
    
    print("=" * 80)
    print(f"分析二刀流球員: {player_name}")
    print("=" * 80)
    
    # 載入文檔
    print("\n載入球員文檔...")
    try:
        with open('./mlb_data/week5_mlb_documents_final_enhanced.json', 'r', encoding='utf-8') as f:
            documents = json.load(f)
    except FileNotFoundError:
        print("❌ 文件未找到，請先執行整合腳本")
        return
    
    print(f"✅ 載入 {len(documents)} 筆記錄")
    
    # 尋找該球員的所有記錄
    print(f"\n搜尋 {player_name} 的所有記錄...")
    
    player_records = []
    
    if isinstance(documents, list):
        for doc in documents:
            if doc.get('player_name') == player_name:
                player_records.append(doc)
    else:
        for doc in documents.values():
            if doc.get('player_name') == player_name:
                player_records.append(doc)
    
    if not player_records:
        print(f"❌ 找不到 {player_name} 的記錄")
        print("\n可能原因:")
        print("  1. 名字拼寫不同（例如：Shohei Ohtani vs Shohei Otani）")
        print("  2. 該球員不在數據集中")
        return
    
    print(f"✅ 找到 {len(player_records)} 筆記錄")
    
    # 分析記錄結構
    print("\n" + "=" * 80)
    print("記錄結構分析")
    print("=" * 80)
    
    # 按賽季和類型分組
    by_season = {}
    
    for record in player_records:
        season = record.get('season')
        player_type = record.get('type')
        
        if season not in by_season:
            by_season[season] = {}
        
        by_season[season][player_type] = record
    
    # 顯示每個賽季的記錄
    for season in sorted(by_season.keys()):
        print(f"\n【{season} 賽季】")
        print("-" * 80)
        
        season_data = by_season[season]
        
        # 打者記錄
        if 'batter' in season_data:
            batter_record = season_data['batter']
            print("\n✅ 打者記錄:")
            print(f"   基礎數據: PA={batter_record.get('PA', 'N/A')}, "
                  f"HR={batter_record.get('HR', 'N/A')}, "
                  f"AVG={batter_record.get('AVG', 'N/A')}")
            
            if 'statcast' in batter_record and batter_record['statcast']:
                statcast = batter_record['statcast']
                print(f"   Statcast 欄位數: {len(statcast)}")
                
                # 顯示關鍵指標
                key_metrics = ['EV', 'LA', 'Barrel%', 'HardHit%', 'xwOBA', 'wRC+', 'WAR']
                print("   關鍵指標:")
                for metric in key_metrics:
                    if metric in statcast:
                        val = statcast[metric]
                        if isinstance(val, float):
                            print(f"     • {metric}: {val:.3f}")
                        else:
                            print(f"     • {metric}: {val}")
            else:
                print("   ⚠️  無 Statcast 數據")
        
        # 投手記錄
        if 'pitcher' in season_data:
            pitcher_record = season_data['pitcher']
            print("\n✅ 投手記錄:")
            print(f"   基礎數據: IP={pitcher_record.get('IP', 'N/A')}, "
                  f"ERA={pitcher_record.get('ERA', 'N/A')}, "
                  f"K={pitcher_record.get('SO', 'N/A')}")
            
            if 'statcast' in pitcher_record and pitcher_record['statcast']:
                statcast = pitcher_record['statcast']
                print(f"   Statcast 欄位數: {len(statcast)}")
                
                # 顯示關鍵指標
                key_metrics = ['FAv', 'K%', 'Whiff%', 'Chase%', 'xERA', 'FIP', 'WAR']
                print("   關鍵指標:")
                for metric in key_metrics:
                    if metric in statcast:
                        val = statcast[metric]
                        if isinstance(val, float):
                            print(f"     • {metric}: {val:.3f}")
                        else:
                            print(f"     • {metric}: {val}")
            else:
                print("   ⚠️  無 Statcast 數據")
    
    # 查詢測試
    print("\n" + "=" * 80)
    print("查詢測試")
    print("=" * 80)
    
    test_queries = [
        f"What is {player_name}'s exit velocity?",
        f"What is {player_name}'s fastball velocity?",
        f"How many home runs did {player_name} hit?",
        f"What is {player_name}'s ERA?"
    ]
    
    print("\n當你詢問以下問題時，系統會如何回答：")
    
    for query in test_queries:
        print(f"\n問題: {query}")
        
        # 判斷問題類型
        is_batter_query = any(keyword in query.lower() for keyword in 
                             ['exit velocity', 'home run', 'hit', 'batting', 'avg', 'ops'])
        is_pitcher_query = any(keyword in query.lower() for keyword in 
                              ['fastball', 'era', 'pitch', 'strikeout', 'k%'])
        
        if is_batter_query:
            print("  → 系統會返回【打者】記錄")
        elif is_pitcher_query:
            print("  → 系統會返回【投手】記錄")
        else:
            print("  → 系統會返回【所有】記錄（打者 + 投手）")
    
    # 總結
    print("\n" + "=" * 80)
    print("二刀流球員數據結構總結")
    print("=" * 80)
    
    print(f"""
📊 數據結構:
   每個賽季有 2 筆獨立記錄:
   • 一筆打者記錄（type: 'batter'）
   • 一筆投手記錄（type: 'pitcher'）

📈 Statcast 數據:
   • 打者 Statcast: 從 statcast_batters_enhanced.csv
   • 投手 Statcast: 從 statcast_pitchers_enhanced.csv
   • 完全獨立，不會混淆

🔍 查詢邏輯:
   1. 關鍵字判斷: 根據問題中的關鍵字判斷類型
      • "exit velocity", "home run" → 打者
      • "fastball velocity", "ERA" → 投手
   
   2. 智能路由: 系統自動選擇正確的記錄類型
   
   3. 模糊查詢: 如果不確定，返回所有記錄讓用戶選擇

✅ 優點:
   • 數據清晰分離
   • 查詢精確
   • 支援完整的打者和投手分析
   • 不會出現數據混淆

💡 實際應用:
   • "Ohtani 的 exit velocity" → 返回打者數據
   • "Ohtani 的 fastball velocity" → 返回投手數據
   • "分析 Ohtani 的表現" → 返回打者 + 投手數據
""")


def main():
    """主程式"""
    
    import sys
    
    player_name = "Shohei Ohtani"
    
    if len(sys.argv) > 1:
        player_name = " ".join(sys.argv[1:])
    
    analyze_two_way_player(player_name)
    
    print("\n" + "=" * 80)
    print("✨ 分析完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
