"""
Week 5: 2022-2025 完整獎項手動數據
包含所有主要獎項的得獎球員
"""

import json

# ============================================
# 2022-2025 獎項數據（完整版）
# ============================================

AWARDS_DATA_2022_2025 = {
    # ========================================
    # 2024 年獎項
    # ========================================
    "Aaron Judge": {
        "MVP": [2022],
        "All-Star": [2017, 2018, 2021, 2022, 2023, 2024],
        "Silver Slugger": [2021, 2022, 2024],
        "Home Run Leader": [2017, 2022, 2024],
        "Rookie of the Year": [2017]
    },
    
    "Shohei Ohtani": {
        "MVP": [2021, 2023, 2024],
        "All-Star": [2021, 2022, 2023, 2024],
        "Silver Slugger": [2021, 2023, 2024],
        "Home Run Leader": [2021]
    },
    
    # 2024 MVP
    "Shohei Ohtani": {
        "MVP": [2021, 2023, 2024],
        "All-Star": [2021, 2022, 2023, 2024],
        "Silver Slugger": [2021, 2023, 2024]
    },
    
    # 2024 Cy Young
    "Tarik Skubal": {
        "Cy Young Award": [2024],
        "All-Star": [2024]
    },
    
    "Chris Sale": {
        "Cy Young Award": [2024],
        "All-Star": [2024]
    },
    
    # 2024 Rookie of the Year
    "Luis Gil": {
        "Rookie of the Year": [2024],
        "All-Star": [2024]
    },
    
    "Paul Skenes": {
        "Rookie of the Year": [2024],
        "All-Star": [2024]
    },
    
    # ========================================
    # 2023 年獎項
    # ========================================
    
    # 2023 MVP
    "Ronald Acuña Jr.": {
        "MVP": [2023],
        "All-Star": [2019, 2021, 2023],
        "Silver Slugger": [2019, 2023],
        "Rookie of the Year": [2018],
        "Stolen Base Leader": [2023]
    },
    
    # 2023 Cy Young
    "Gerrit Cole": {
        "Cy Young Award": [2023],
        "All-Star": [2015, 2019, 2021, 2023],
        "Strikeout Leader": [2019]
    },
    
    "Blake Snell": {
        "Cy Young Award": [2018, 2023],
        "All-Star": [2018, 2023]
    },
    
    # 2023 Rookie of the Year
    "Gunnar Henderson": {
        "Rookie of the Year": [2023],
        "All-Star": [2023, 2024],
        "Silver Slugger": [2023]
    },
    
    "Corbin Carroll": {
        "Rookie of the Year": [2023],
        "All-Star": [2023],
        "Gold Glove": [2023],
        "Silver Slugger": [2023]
    },
    
    # ========================================
    # 2022 年獎項
    # ========================================
    
    # 2022 MVP 已在 Aaron Judge 中
    
    # 2022 NL MVP
    "Paul Goldschmidt": {
        "MVP": [2022],
        "All-Star": [2013, 2015, 2016, 2017, 2018, 2022],
        "Gold Glove": [2013, 2015, 2017, 2018],
        "Silver Slugger": [2013, 2015, 2017, 2018, 2022]
    },
    
    # 2022 Cy Young
    "Justin Verlander": {
        "Cy Young Award": [2011, 2019, 2022],
        "MVP": [2011],
        "All-Star": [2007, 2009, 2011, 2012, 2018, 2019, 2022],
        "Rookie of the Year": [2006],
        "No-Hitter": [2007, 2011]
    },
    
    "Sandy Alcantara": {
        "Cy Young Award": [2022],
        "All-Star": [2022, 2023]
    },
    
    # 2022 Rookie of the Year
    "Julio Rodríguez": {
        "Rookie of the Year": [2022],
        "All-Star": [2022, 2023],
        "Silver Slugger": [2022, 2023],
        "Gold Glove": [2022, 2023]
    },
    
    "Michael Harris II": {
        "Rookie of the Year": [2022],
        "All-Star": [2022],
        "Gold Glove": [2022, 2023]
    },
    
    # ========================================
    # 其他重要球員（2022-2024 All-Star 或多次得獎）
    # ========================================
    
    "Mike Trout": {
        "MVP": [2014, 2016, 2019],
        "All-Star": [2012, 2013, 2014, 2015, 2016, 2018, 2019, 2021, 2022],
        "Silver Slugger": [2012, 2013, 2014, 2015, 2016, 2019],
        "Rookie of the Year": [2012]
    },
    
    "Mookie Betts": {
        "MVP": [2018],
        "All-Star": [2016, 2018, 2019, 2021, 2022, 2023, 2024],
        "Gold Glove": [2016, 2017, 2018, 2019, 2020, 2021],
        "Silver Slugger": [2016, 2018, 2020]
    },
    
    "Freddie Freeman": {
        "MVP": [2020],
        "All-Star": [2013, 2014, 2018, 2019, 2020, 2021, 2023, 2024],
        "Silver Slugger": [2019, 2020],
        "Gold Glove": [2018, 2020]
    },
    
    "Jose Altuve": {
        "MVP": [2017],
        "All-Star": [2012, 2014, 2015, 2016, 2017, 2018, 2022, 2024],
        "Silver Slugger": [2014, 2015, 2016, 2017],
        "Batting Title": [2014, 2016, 2017],
        "Gold Glove": [2015]
    },
    
    "Juan Soto": {
        "All-Star": [2018, 2021, 2022, 2023],
        "Silver Slugger": [2020, 2021],
        "Batting Title": [2020]
    },
    
    "Bryce Harper": {
        "MVP": [2015, 2021],
        "All-Star": [2012, 2013, 2015, 2016, 2017, 2018, 2022],
        "Silver Slugger": [2015, 2021],
        "Rookie of the Year": [2012],
        "Home Run Leader": [2015]
    },
    
    "Yordan Alvarez": {
        "All-Star": [2022, 2023],
        "Silver Slugger": [2022, 2023],
        "Rookie of the Year": [2019]
    },
    
    "Kyle Tucker": {
        "All-Star": [2023, 2024],
        "Silver Slugger": [2023],
        "Gold Glove": [2022]
    },
    
    "Corey Seager": {
        "All-Star": [2016, 2017, 2023],
        "Silver Slugger": [2016, 2017, 2023],
        "Rookie of the Year": [2016],
        "World Series MVP": [2020]
    },
    
    "Marcus Semien": {
        "All-Star": [2019, 2021, 2023],
        "Silver Slugger": [2021],
        "Gold Glove": [2021]
    },
    
    "Francisco Lindor": {
        "All-Star": [2016, 2017, 2018, 2019, 2021, 2023, 2024],
        "Gold Glove": [2016, 2019, 2023, 2024],
        "Silver Slugger": [2017, 2018]
    },
    
    "Pete Alonso": {
        "All-Star": [2019, 2021, 2023, 2024],
        "Silver Slugger": [2019, 2022],
        "Rookie of the Year": [2019],
        "Home Run Leader": [2019, 2022]
    },
    
    "Vladimir Guerrero Jr.": {
        "All-Star": [2021, 2022],
        "Silver Slugger": [2021],
        "Rookie of the Year": [2019]
    },
    
    "Bo Bichette": {
        "All-Star": [2021, 2022],
        "Silver Slugger": [2021]
    },
    
    "Rafael Devers": {
        "All-Star": [2021, 2022, 2023],
        "Silver Slugger": [2021, 2022, 2023]
    },
    
    "Austin Riley": {
        "All-Star": [2022, 2023],
        "Silver Slugger": [2022, 2023],
        "Gold Glove": [2023]
    },
    
    "Matt Olson": {
        "All-Star": [2021, 2023],
        "Gold Glove": [2018, 2021, 2022, 2023],
        "Silver Slugger": [2021, 2023]
    },
    
    "Adolis García": {
        "All-Star": [2023],
        "Silver Slugger": [2023],
        "World Series MVP": [2023]
    },
    
    "Nolan Arenado": {
        "All-Star": [2015, 2016, 2017, 2018, 2019, 2022],
        "Gold Glove": [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2022],
        "Silver Slugger": [2015, 2016, 2017, 2018]
    },
    
    "Manny Machado": {
        "All-Star": [2013, 2015, 2016, 2018, 2022, 2023],
        "Gold Glove": [2013, 2015],
        "Silver Slugger": [2022]
    },
    
    "Trea Turner": {
        "All-Star": [2021, 2022],
        "Silver Slugger": [2021]
    },
    
    "Xander Bogaerts": {
        "All-Star": [2016, 2019, 2021, 2022],
        "Silver Slugger": [2019, 2022]
    },
    
    "José Ramírez": {
        "All-Star": [2017, 2018, 2022, 2024],
        "Silver Slugger": [2017, 2018, 2022, 2024]
    },
    
    "Marcus Stroman": {
        "All-Star": [2019],
        "Gold Glove": [2017, 2019]
    },
    
    # ========================================
    # 投手（2022-2024）
    # ========================================
    
    "Zack Wheeler": {
        "All-Star": [2021, 2023],
        "Cy Young 第二名": [2021]
    },
    
    "Spencer Strider": {
        "All-Star": [2023],
        "Strikeout Leader": [2023]
    },
    
    "Dylan Cease": {
        "All-Star": [2022],
        "Cy Young 第二名": [2022]
    },
    
    "Corbin Burnes": {
        "Cy Young Award": [2021],
        "All-Star": [2021, 2022],
        "ERA Leader": [2021]
    },
    
    "Logan Webb": {
        "All-Star": [2022, 2023]
    },
    
    "Kevin Gausman": {
        "All-Star": [2021, 2022, 2023]
    },
    
    "Shane McClanahan": {
        "All-Star": [2023]
    },
    
    "Framber Valdez": {
        "All-Star": [2022, 2023],
        "Gold Glove": [2023]
    },
    
    "Alek Manoah": {
        "All-Star": [2022]
    },
    
    "Shane Bieber": {
        "Cy Young Award": [2020],
        "All-Star": [2019, 2021],
        "Strikeout Leader": [2020]
    },
    
    "Clayton Kershaw": {
        "Cy Young Award": [2011, 2013, 2014],
        "MVP": [2014],
        "All-Star": [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018],
        "Gold Glove": [2011, 2012, 2013, 2014]
    },
    
    "Max Scherzer": {
        "Cy Young Award": [2013, 2016, 2017],
        "All-Star": [2013, 2015, 2016, 2017, 2018, 2019, 2021]
    },
    
    "Yu Darvish": {
        "All-Star": [2012, 2013, 2017, 2023]
    },
    
    "Emmanuel Clase": {
        "All-Star": [2022, 2023, 2024],
        "Reliever of the Year": [2022, 2023]
    },
    
    "Josh Hader": {
        "All-Star": [2018, 2019, 2021, 2022, 2023],
        "Reliever of the Year": [2018, 2019, 2021]
    },
    
    "Devin Williams": {
        "All-Star": [2023],
        "Reliever of the Year": [2020]
    },
    
    "Félix Bautista": {
        "All-Star": [2023],
        "Reliever of the Year": [2023]
    },
    
    # ========================================
    # 2024 新秀和新興球員
    # ========================================
    
    "Elly De La Cruz": {
        "All-Star": [2024]
    },
    
    "Bobby Witt Jr.": {
        "All-Star": [2023, 2024],
        "Silver Slugger": [2024]
    },
    
    "Jackson Holliday": {
        "Rookie": [2024]
    },
    
    "Yoshinobu Yamamoto": {
        "All-Star": [2024]
    },
    
    "Jackson Chourio": {
        "Rookie": [2024]
    },
    
    # ========================================
    # 更多 All-Star 常客（2022-2024）
    # ========================================
    
    "Salvador Pérez": {
        "All-Star": [2013, 2015, 2016, 2017, 2018, 2021, 2023],
        "Gold Glove": [2013, 2014, 2015, 2016, 2017, 2018, 2021],
        "Silver Slugger": [2016, 2018, 2021]
    },
    
    "Will Smith": {
        "All-Star": [2022, 2024],
        "Silver Slugger": [2021]
    },
    
    "Adley Rutschman": {
        "All-Star": [2023],
        "Silver Slugger": [2023],
        "Gold Glove": [2023]
    },
    
    "J.T. Realmuto": {
        "All-Star": [2018, 2019, 2021, 2022, 2023],
        "Gold Glove": [2019, 2020, 2023],
        "Silver Slugger": [2019, 2022]
    },
    
    "Dansby Swanson": {
        "All-Star": [2022],
        "Gold Glove": [2022, 2023]
    },
    
    "Willy Adames": {
        "All-Star": [2024],
        "Silver Slugger": [2024]
    },
    
    "Seiya Suzuki": {
        "All-Star": [2024]
    },
    
    "Christian Yelich": {
        "MVP": [2018],
        "All-Star": [2018, 2019, 2023],
        "Silver Slugger": [2018, 2019],
        "Gold Glove": [2014]
    },
    
    "Ketel Marte": {
        "All-Star": [2019, 2024],
        "Gold Glove": [2024]
    },
    
    "Steven Kwan": {
        "All-Star": [2022, 2024],
        "Gold Glove": [2022, 2023, 2024]
    },
    
    "Josh Jung": {
        "Rookie": [2023]
    },
    
    "Anthony Volpe": {
        "Rookie": [2023]
    },
    
    "Masataka Yoshida": {
        "Rookie": [2023]
    },
    
    "Esteury Ruiz": {
        "Stolen Base Leader": [2023]
    },
    
    "Kyle Schwarber": {
        "All-Star": [2021, 2024],
        "Silver Slugger": [2024],
        "Home Run Leader": [2022]
    },
    
    "Teoscar Hernández": {
        "All-Star": [2021, 2024],
        "Silver Slugger": [2021]
    },
    
    "Randy Arozarena": {
        "All-Star": [2023],
        "Rookie of the Year 提名": [2021]
    },
    
    "Jazz Chisholm Jr.": {
        "All-Star": [2022]
    },
}


def save_awards_data():
    """儲存獎項數據"""
    
    print("=" * 80)
    print("儲存 2022-2025 完整獎項數據")
    print("=" * 80)
    
    # 計算總獎項數
    for player in AWARDS_DATA_2022_2025:
        awards = AWARDS_DATA_2022_2025[player]
        total = sum(len(years) for key, years in awards.items() 
                   if isinstance(years, list))
        awards['total_count'] = total
    
    # 儲存
    output_file = "./mlb_data/week5_awards.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(AWARDS_DATA_2022_2025, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 獎項數據已儲存: {output_file}")
    print(f"   總球員數: {len(AWARDS_DATA_2022_2025)}")
    
    # 統計
    mvp_count = sum(1 for p, a in AWARDS_DATA_2022_2025.items() if 'MVP' in a)
    cy_young_count = sum(1 for p, a in AWARDS_DATA_2022_2025.items() if 'Cy Young Award' in a)
    roy_count = sum(1 for p, a in AWARDS_DATA_2022_2025.items() if 'Rookie of the Year' in a)
    all_star_count = sum(1 for p, a in AWARDS_DATA_2022_2025.items() if 'All-Star' in a)
    
    print(f"\n獎項統計:")
    print(f"   MVP 得主: {mvp_count} 位")
    print(f"   Cy Young 得主: {cy_young_count} 位")
    print(f"   ROY 得主: {roy_count} 位")
    print(f"   All-Star: {all_star_count} 位")
    
    # 顯示前 10 位
    print(f"\n前 10 位球員（按獎項總數）:")
    sorted_players = sorted(AWARDS_DATA_2022_2025.items(),
                           key=lambda x: x[1]['total_count'],
                           reverse=True)
    
    for i, (player, awards) in enumerate(sorted_players[:10], 1):
        print(f"\n{i}. {player} ({awards['total_count']} 個獎項)")
        for award_type, years in sorted(awards.items()):
            if award_type != 'total_count' and years:
                if isinstance(years, list):
                    print(f"   {award_type}: {years}")
                else:
                    print(f"   {award_type}: {years}")


if __name__ == "__main__":
    save_awards_data()
    
    print("\n" + "=" * 80)
    print("✨ 完成！")
    print("=" * 80)
    print("\n下一步：")
    print("  1. python week5_manual_salaries.py  (薪資數據)")
    print("  2. python week5_integrate_data.py   (整合)")
