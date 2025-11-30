"""
Week 5: 2024-2025 薪資手動數據
包含重要球員的薪資和合約資訊
"""

import json

# ============================================
# 2024-2025 薪資數據
# 基於公開的合約資訊
# ============================================

SALARY_DATA_2024 = {
    # 超級合約球員
    "Shohei Ohtani": {
        "current_salary": 70000000,
        "year": 2024,
        "team": "LAD",
        "contract_years": 10,
        "total_value": 700000000
    },
    
    "Mike Trout": {
        "current_salary": 37116666,
        "year": 2024,
        "team": "LAA",
        "contract_years": 12,
        "total_value": 426500000
    },
    
    "Aaron Judge": {
        "current_salary": 40000000,
        "year": 2024,
        "team": "NYY",
        "contract_years": 9,
        "total_value": 360000000
    },
    
    "Mookie Betts": {
        "current_salary": 30000000,
        "year": 2024,
        "team": "LAD",
        "contract_years": 12,
        "total_value": 365000000
    },
    
    "Francisco Lindor": {
        "current_salary": 34100000,
        "year": 2024,
        "team": "NYM",
        "contract_years": 10,
        "total_value": 341000000
    },
    
    "Fernando Tatis Jr.": {
        "current_salary": 36000000,
        "year": 2024,
        "team": "SD",
        "contract_years": 14,
        "total_value": 340000000
    },
    
    "Bryce Harper": {
        "current_salary": 27538462,
        "year": 2024,
        "team": "PHI",
        "contract_years": 13,
        "total_value": 330000000
    },
    
    "Gerrit Cole": {
        "current_salary": 36000000,
        "year": 2024,
        "team": "NYY",
        "contract_years": 9,
        "total_value": 324000000
    },
    
    "Giancarlo Stanton": {
        "current_salary": 32000000,
        "year": 2024,
        "team": "NYY",
        "contract_years": 13,
        "total_value": 325000000
    },
    
    "Corey Seager": {
        "current_salary": 33000000,
        "year": 2024,
        "team": "TEX",
        "contract_years": 10,
        "total_value": 325000000
    },
    
    "Marcus Semien": {
        "current_salary": 25000000,
        "year": 2024,
        "team": "TEX",
        "contract_years": 7,
        "total_value": 175000000
    },
    
    "Trea Turner": {
        "current_salary": 27272727,
        "year": 2024,
        "team": "PHI",
        "contract_years": 11,
        "total_value": 300000000
    },
    
    "Xander Bogaerts": {
        "current_salary": 27000000,
        "year": 2024,
        "team": "SD",
        "contract_years": 11,
        "total_value": 280000000
    },
    
    "Rafael Devers": {
        "current_salary": 27916666,
        "year": 2024,
        "team": "BOS",
        "contract_years": 10,
        "total_value": 313500000
    },
    
    "Manny Machado": {
        "current_salary": 30000000,
        "year": 2024,
        "team": "SD",
        "contract_years": 11,
        "total_value": 350000000
    },
    
    "Justin Verlander": {
        "current_salary": 43333333,
        "year": 2024,
        "team": "HOU",
        "contract_years": 2,
        "total_value": 86666666
    },
    
    "Max Scherzer": {
        "current_salary": 43333333,
        "year": 2024,
        "team": "TEX",
        "contract_years": 3,
        "total_value": 130000000
    },
    
    "Jacob deGrom": {
        "current_salary": 37000000,
        "year": 2024,
        "team": "TEX",
        "contract_years": 5,
        "total_value": 185000000
    },
    
    "Carlos Correa": {
        "current_salary": 33333333,
        "year": 2024,
        "team": "MIN",
        "contract_years": 6,
        "total_value": 200000000
    },
    
    "Freddie Freeman": {
        "current_salary": 27000000,
        "year": 2024,
        "team": "LAD",
        "contract_years": 6,
        "total_value": 162000000
    },
    
    "Matt Olson": {
        "current_salary": 21000000,
        "year": 2024,
        "team": "ATL",
        "contract_years": 8,
        "total_value": 168000000
    },
    
    "Austin Riley": {
        "current_salary": 21000000,
        "year": 2024,
        "team": "ATL",
        "contract_years": 10,
        "total_value": 212000000
    },
    
    "José Altuve": {
        "current_salary": 29000000,
        "year": 2024,
        "team": "HOU",
        "contract_years": 5,
        "total_value": 151000000
    },
    
    "Alex Bregman": {
        "current_salary": 28500000,
        "year": 2024,
        "team": "HOU",
        "contract_years": 5,
        "total_value": 100000000
    },
    
    "Kyle Tucker": {
        "current_salary": 11750000,
        "year": 2024,
        "team": "HOU",
        "contract_years": 1,
        "total_value": 11750000
    },
    
    "Yordan Alvarez": {
        "current_salary": 12500000,
        "year": 2024,
        "team": "HOU",
        "contract_years": 6,
        "total_value": 115000000
    },
    
    "Ronald Acuña Jr.": {
        "current_salary": 17000000,
        "year": 2024,
        "team": "ATL",
        "contract_years": 8,
        "total_value": 100000000
    },
    
    "Julio Rodríguez": {
        "current_salary": 6900000,
        "year": 2024,
        "team": "SEA",
        "contract_years": 7,
        "total_value": 120000000
    },
    
    "Pete Alonso": {
        "current_salary": 20500000,
        "year": 2024,
        "team": "NYM",
        "contract_years": 1,
        "total_value": 20500000
    },
    
    "Juan Soto": {
        "current_salary": 33000000,
        "year": 2024,
        "team": "NYY",
        "contract_years": 1,
        "total_value": 33000000
    },
    
    "Nolan Arenado": {
        "current_salary": 27000000,
        "year": 2024,
        "team": "STL",
        "contract_years": 8,
        "total_value": 260000000
    },
    
    "Paul Goldschmidt": {
        "current_salary": 26000000,
        "year": 2024,
        "team": "STL",
        "contract_years": 5,
        "total_value": 130000000
    },
    
    "Clayton Kershaw": {
        "current_salary": 10000000,
        "year": 2024,
        "team": "LAD",
        "contract_years": 1,
        "total_value": 10000000
    },
    
    "Zack Wheeler": {
        "current_salary": 42000000,
        "year": 2024,
        "team": "PHI",
        "contract_years": 3,
        "total_value": 126000000
    },
    
    "Aaron Nola": {
        "current_salary": 25000000,
        "year": 2024,
        "team": "PHI",
        "contract_years": 7,
        "total_value": 172000000
    },
    
    "Blake Snell": {
        "current_salary": 32000000,
        "year": 2024,
        "team": "SF",
        "contract_years": 2,
        "total_value": 62000000
    },
    
    "Corbin Burnes": {
        "current_salary": 15100000,
        "year": 2024,
        "team": "BAL",
        "contract_years": 1,
        "total_value": 15100000
    },
    
    "Sandy Alcantara": {
        "current_salary": 13000000,
        "year": 2024,
        "team": "MIA",
        "contract_years": 5,
        "total_value": 56000000
    },
    
    "Vladimir Guerrero Jr.": {
        "current_salary": 19900000,
        "year": 2024,
        "team": "TOR",
        "contract_years": 1,
        "total_value": 19900000
    },
    
    "Bo Bichette": {
        "current_salary": 10800000,
        "year": 2024,
        "team": "TOR",
        "contract_years": 1,
        "total_value": 10800000
    },
    
    "José Ramírez": {
        "current_salary": 14000000,
        "year": 2024,
        "team": "CLE",
        "contract_years": 7,
        "total_value": 141000000
    },
    
    "Salvador Pérez": {
        "current_salary": 20750000,
        "year": 2024,
        "team": "KC",
        "contract_years": 4,
        "total_value": 82000000
    },
    
    "J.T. Realmuto": {
        "current_salary": 23875000,
        "year": 2024,
        "team": "PHI",
        "contract_years": 5,
        "total_value": 115500000
    },
    
    "Will Smith": {
        "current_salary": 15000000,
        "year": 2024,
        "team": "LAD",
        "contract_years": 10,
        "total_value": 140000000
    },
    
    "Adley Rutschman": {
        "current_salary": 3100000,
        "year": 2024,
        "team": "BAL",
        "contract_years": 1,
        "total_value": 3100000
    },
    
    "Bobby Witt Jr.": {
        "current_salary": 7666666,
        "year": 2024,
        "team": "KC",
        "contract_years": 11,
        "total_value": 288777777
    },
    
    "Gunnar Henderson": {
        "current_salary": 800000,
        "year": 2024,
        "team": "BAL",
        "contract_years": 1,
        "total_value": 800000
    },
    
    "Elly De La Cruz": {
        "current_salary": 750000,
        "year": 2024,
        "team": "CIN",
        "contract_years": 1,
        "total_value": 750000
    },
    
    "Spencer Strider": {
        "current_salary": 900000,
        "year": 2024,
        "team": "ATL",
        "contract_years": 6,
        "total_value": 75000000
    },
    
    "Logan Webb": {
        "current_salary": 4600000,
        "year": 2024,
        "team": "SF",
        "contract_years": 5,
        "total_value": 90000000
    },
    
    "Kevin Gausman": {
        "current_salary": 25000000,
        "year": 2024,
        "team": "TOR",
        "contract_years": 5,
        "total_value": 110000000
    },
    
    "Luis Castillo": {
        "current_salary": 23000000,
        "year": 2024,
        "team": "SEA",
        "contract_years": 5,
        "total_value": 108000000
    },
    
    "Dylan Cease": {
        "current_salary": 8000000,
        "year": 2024,
        "team": "SD",
        "contract_years": 1,
        "total_value": 8000000
    },
    
    "Framber Valdez": {
        "current_salary": 12000000,
        "year": 2024,
        "team": "HOU",
        "contract_years": 1,
        "total_value": 12000000
    },
    
    "Christian Yelich": {
        "current_salary": 26000000,
        "year": 2024,
        "team": "MIL",
        "contract_years": 9,
        "total_value": 215000000
    },
}


def save_salary_data():
    """儲存薪資數據"""
    
    print("=" * 80)
    print("儲存 2024-2025 薪資數據")
    print("=" * 80)
    
    # 儲存
    output_file = "./mlb_data/week5_salaries.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(SALARY_DATA_2024, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 薪資數據已儲存: {output_file}")
    print(f"   總球員數: {len(SALARY_DATA_2024)}")
    
    # 統計
    total_value = sum(p['total_value'] for p in SALARY_DATA_2024.values())
    avg_salary = sum(p['current_salary'] for p in SALARY_DATA_2024.values()) / len(SALARY_DATA_2024)
    
    print(f"\n薪資統計:")
    print(f"   平均年薪: ${avg_salary:,.0f}")
    print(f"   合約總額: ${total_value:,.0f}")
    
    # 顯示前 10 位
    print(f"\n薪資最高的 10 位球員:")
    sorted_players = sorted(SALARY_DATA_2024.items(),
                           key=lambda x: x[1]['current_salary'],
                           reverse=True)
    
    for i, (player, salary_info) in enumerate(sorted_players[:10], 1):
        print(f"\n{i}. {player}")
        print(f"   年薪: ${salary_info['current_salary']:,}")
        print(f"   球隊: {salary_info['team']}")
        print(f"   合約: {salary_info['contract_years']} 年 / ${salary_info['total_value']:,}")


if __name__ == "__main__":
    save_salary_data()
    
    print("\n" + "=" * 80)
    print("✨ 完成！")
    print("=" * 80)
    print("\n下一步：")
    print("  python week5_integrate_data.py  (整合數據)")
