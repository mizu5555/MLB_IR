"""
Week 5: 獎項數據收集（不使用 Lahman）

策略：
1. 使用現有球員名字作為基礎
2. 從 Baseball Reference 爬取獎項數據
3. 或使用手動建立的獎項數據集
"""

import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import time


# 手動建立的主要獎項數據（2022-2024）
# 這些是公開資訊，可以從 MLB 官網、Baseball Reference 等來源確認

KNOWN_AWARDS = {
    # 2022 年獎項
    2022: {
        'MVP': {
            'AL': 'Aaron Judge',
            'NL': 'Paul Goldschmidt'
        },
        'Cy Young': {
            'AL': 'Justin Verlander',
            'NL': 'Sandy Alcantara'
        },
        'Rookie of the Year': {
            'AL': 'Julio Rodriguez',
            'NL': 'Michael Harris II'
        },
        'All-Star': [
            # AL 樣本
            'Aaron Judge', 'Shohei Ohtani', 'Mike Trout', 'José Ramírez',
            'Vladimir Guerrero Jr.', 'Rafael Devers', 'Xander Bogaerts',
            # NL 樣本
            'Ronald Acuña Jr.', 'Mookie Betts', 'Paul Goldschmidt',
            'Manny Machado', 'Juan Soto', 'Austin Riley'
        ]
    },
    
    # 2023 年獎項
    2023: {
        'MVP': {
            'AL': 'Shohei Ohtani',
            'NL': 'Ronald Acuña Jr.'
        },
        'Cy Young': {
            'AL': 'Gerrit Cole',
            'NL': 'Blake Snell'
        },
        'Rookie of the Year': {
            'AL': 'Gunnar Henderson',
            'NL': 'Corbin Carroll'
        },
        'All-Star': [
            # AL 樣本
            'Shohei Ohtani', 'Aaron Judge', 'Julio Rodriguez', 'Marcus Semien',
            'Corey Seager', 'Adolis García', 'Randy Arozarena',
            # NL 樣本
            'Ronald Acuña Jr.', 'Freddie Freeman', 'Mookie Betts',
            'Juan Soto', 'Corbin Carroll', 'Christian Yelich'
        ]
    },
    
    # 2024 年獎項
    2024: {
        'MVP': {
            'AL': 'Aaron Judge',
            'NL': 'Shohei Ohtani'
        },
        'Cy Young': {
            'AL': 'Tarik Skubal',
            'NL': 'Chris Sale'
        },
        'Rookie of the Year': {
            'AL': 'Colton Cowser',
            'NL': 'Paul Skenes'
        },
        'All-Star': [
            # AL 樣本
            'Aaron Judge', 'Juan Soto', 'Gunnar Henderson', 'José Ramírez',
            'Bobby Witt Jr.', 'Yordan Alvarez', 'Kyle Tucker',
            # NL 樣本
            'Shohei Ohtani', 'Bryce Harper', 'Mookie Betts',
            'Ronald Acuña Jr.', 'Trea Turner', 'Francisco Lindor'
        ]
    }
}


def collect_awards_from_manual_data() -> Dict[str, Dict]:
    """
    從手動建立的獎項數據收集
    
    Returns:
        {
            'Aaron Judge': {
                'MVP': [2022, 2024],
                'All-Star': [2022, 2023, 2024],
                'total_count': 5
            }
        }
    """
    
    print("=" * 80)
    print("收集獎項數據（使用已知獎項資料）")
    print("=" * 80)
    
    player_awards = {}
    
    for year, awards in KNOWN_AWARDS.items():
        print(f"\n處理 {year} 年獎項...")
        
        # MVP
        for league, player in awards['MVP'].items():
            if player not in player_awards:
                player_awards[player] = {}
            if 'MVP' not in player_awards[player]:
                player_awards[player]['MVP'] = []
            player_awards[player]['MVP'].append(year)
            print(f"  ✅ {player} - MVP ({league})")
        
        # Cy Young
        for league, player in awards['Cy Young'].items():
            if player not in player_awards:
                player_awards[player] = {}
            if 'Cy Young' not in player_awards[player]:
                player_awards[player]['Cy Young'] = []
            player_awards[player]['Cy Young'].append(year)
            print(f"  ✅ {player} - Cy Young ({league})")
        
        # Rookie of the Year
        for league, player in awards['Rookie of the Year'].items():
            if player not in player_awards:
                player_awards[player] = {}
            if 'Rookie of the Year' not in player_awards[player]:
                player_awards[player]['Rookie of the Year'] = []
            player_awards[player]['Rookie of the Year'].append(year)
            print(f"  ✅ {player} - Rookie of the Year ({league})")
        
        # All-Star
        for player in awards['All-Star']:
            if player not in player_awards:
                player_awards[player] = {}
            if 'All-Star' not in player_awards[player]:
                player_awards[player]['All-Star'] = []
            if year not in player_awards[player]['All-Star']:
                player_awards[player]['All-Star'].append(year)
        
        print(f"  ✅ All-Star: {len(awards['All-Star'])} 位球員")
    
    # 計算總獎項數
    for player in player_awards:
        total = sum(len(years) for years in player_awards[player].values())
        player_awards[player]['total_count'] = total
    
    print(f"\n✅ 總計：{len(player_awards)} 位獲獎球員")
    
    return player_awards


def expand_awards_with_existing_players(awards: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    根據現有球員資料擴充獎項數據
    
    策略：
    1. 載入現有球員名單
    2. 對於已知的獲獎球員，加入其獎項
    3. 對於其他球員，設為無獎項
    """
    
    print("\n" + "=" * 80)
    print("擴充獎項數據")
    print("=" * 80)
    
    try:
        # 載入現有球員
        with open('./mlb_data/mlb_documents.json', 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        print(f"✅ 載入 {len(documents)} 筆球員資料")
        
        # 收集所有唯一球員
        unique_players = set(doc['player_name'] for doc in documents)
        print(f"✅ 發現 {len(unique_players)} 位唯一球員")
        
        # 統計有獎項的球員
        players_with_awards = len([p for p in unique_players if p in awards])
        players_without_awards = len(unique_players) - players_with_awards
        
        print(f"\n統計：")
        print(f"  有獎項: {players_with_awards} 位")
        print(f"  無獎項: {players_without_awards} 位")
        
        return awards
        
    except Exception as e:
        print(f"⚠️  擴充失敗: {e}")
        return awards


def save_awards_data(awards: Dict[str, Dict]):
    """儲存獎項數據"""
    
    # 儲存原始格式
    output_file = "./mlb_data/week5_awards.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(awards, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 獎項數據已儲存: {output_file}")
    
    # 顯示樣本
    print("\n[獎項樣本]")
    sample_players = sorted(list(awards.items()), 
                           key=lambda x: x[1]['total_count'], 
                           reverse=True)[:5]
    
    for player_name, player_awards in sample_players:
        print(f"\n{player_name}:")
        for award_type, years in player_awards.items():
            if award_type != 'total_count':
                print(f"  {award_type}: {years}")
        print(f"  總計: {player_awards['total_count']} 個獎項")


if __name__ == "__main__":
    
    # 收集獎項
    awards = collect_awards_from_manual_data()
    
    # 擴充獎項（與現有球員比對）
    awards = expand_awards_with_existing_players(awards)
    
    # 儲存
    save_awards_data(awards)
    
    print("\n" + "=" * 80)
    print("✨ 獎項數據收集完成")
    print("=" * 80)
    print("\n下一步：")
    print("  python week5_integrate_awards_simple.py")
