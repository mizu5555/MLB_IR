"""
Week 5: 完整數據收集腳本
整合 Phase 2 (獎項) + Phase 3 (薪資) + Phase 4 (Statcast)

使用 pybaseball 的 Lahman 模組和 Statcast 功能
"""

import pandas as pd
import json
import time
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# 確保已安裝 pybaseball
try:
    from pybaseball.lahman import awards_players, all_star_full, salaries
    from pybaseball import statcast, statcast_batter, statcast_pitcher
    print("✅ pybaseball 已載入")
except ImportError:
    print("❌ 請先安裝 pybaseball: pip install pybaseball")
    exit(1)

# ============================================
# 配置
# ============================================

# Phase 2: 獎項年份
AWARDS_YEARS = [2022, 2023, 2024, 2025]

# Phase 3: 薪資年份
SALARY_YEARS = [2024, 2025]

# Phase 4: Statcast 年份
STATCAST_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

# 獎項類型映射
AWARD_TYPE_MAP = {
    'MVP': 'Most Valuable Player',
    'Cy Young Award': 'Cy Young',
    'Rookie of the Year': 'Rookie of the Year',
    'Gold Glove': 'Gold Glove',
    'Silver Slugger': 'Silver Slugger',
    # 其他獎項會自動包含
}

# ============================================
# Phase 2: 獎項數據收集
# ============================================

def collect_awards_data() -> pd.DataFrame:
    """
    收集球員獎項數據
    
    Returns:
        DataFrame with columns: player_name, award_id, year_id, league_id, tie, notes
    """
    
    print("\n" + "=" * 80)
    print("Phase 2: 收集獎項數據")
    print("=" * 80)
    
    try:
        # 使用 pybaseball 獲取獎項數據
        print("正在下載獎項數據...")
        awards_df = awards_players()
        
        print(f"✅ 成功下載 {len(awards_df)} 筆獎項記錄")
        print(f"年份範圍: {awards_df['yearID'].min()} - {awards_df['yearID'].max()}")
        
        # 過濾我們需要的年份
        awards_filtered = awards_df[awards_df['yearID'].isin(AWARDS_YEARS)].copy()
        print(f"✅ 過濾後: {len(awards_filtered)} 筆 ({AWARDS_YEARS[0]}-{AWARDS_YEARS[-1]})")
        
        # 查看獎項類型
        print("\n獎項類型統計:")
        award_counts = awards_filtered['awardID'].value_counts()
        for award, count in award_counts.items():
            print(f"  {award}: {count} 筆")
        
        return awards_filtered
        
    except Exception as e:
        print(f"❌ 獎項數據收集失敗: {e}")
        return pd.DataFrame()


def collect_allstar_data() -> pd.DataFrame:
    """
    收集全明星數據
    
    Returns:
        DataFrame with All-Star selections
    """
    
    print("\n正在下載全明星數據...")
    
    try:
        allstar_df = all_star_full()
        
        print(f"✅ 成功下載 {len(allstar_df)} 筆全明星記錄")
        
        # 過濾年份
        allstar_filtered = allstar_df[allstar_df['yearID'].isin(AWARDS_YEARS)].copy()
        print(f"✅ 過濾後: {len(allstar_filtered)} 筆 ({AWARDS_YEARS[0]}-{AWARDS_YEARS[-1]})")
        
        return allstar_filtered
        
    except Exception as e:
        print(f"❌ 全明星數據收集失敗: {e}")
        return pd.DataFrame()


def organize_awards_by_player(awards_df: pd.DataFrame, allstar_df: pd.DataFrame) -> Dict:
    """
    將獎項數據按球員組織
    
    Returns:
        {
            'Aaron Judge': {
                'MVP': [2022],
                'All-Star': [2022, 2023, 2024],
                'total_count': 4
            }
        }
    """
    
    print("\n正在組織獎項數據...")
    
    player_awards = {}
    
    # 處理獎項數據
    if not awards_df.empty:
        for _, row in awards_df.iterrows():
            # Lahman 使用 playerID，我們需要轉換成球員名字
            # 這裡簡化處理，使用 playerID 作為 key
            player_id = row['playerID']
            award_type = row['awardID']
            year = int(row['yearID'])
            
            if player_id not in player_awards:
                player_awards[player_id] = {}
            
            if award_type not in player_awards[player_id]:
                player_awards[player_id][award_type] = []
            
            if year not in player_awards[player_id][award_type]:
                player_awards[player_id][award_type].append(year)
    
    # 處理全明星數據
    if not allstar_df.empty:
        for _, row in allstar_df.iterrows():
            player_id = row['playerID']
            year = int(row['yearID'])
            
            if player_id not in player_awards:
                player_awards[player_id] = {}
            
            if 'All-Star' not in player_awards[player_id]:
                player_awards[player_id]['All-Star'] = []
            
            if year not in player_awards[player_id]['All-Star']:
                player_awards[player_id]['All-Star'].append(year)
    
    # 計算總獎項數
    for player_id in player_awards:
        total = sum(len(years) for award, years in player_awards[player_id].items())
        player_awards[player_id]['total_count'] = total
    
    print(f"✅ 組織完成: {len(player_awards)} 位球員")
    
    return player_awards


# ============================================
# Phase 3: 薪資數據收集
# ============================================

def collect_salary_data() -> pd.DataFrame:
    """
    收集球員薪資數據
    
    Returns:
        DataFrame with salary information
    """
    
    print("\n" + "=" * 80)
    print("Phase 3: 收集薪資數據")
    print("=" * 80)
    
    try:
        print("正在下載薪資數據...")
        salary_df = salaries()
        
        print(f"✅ 成功下載 {len(salary_df)} 筆薪資記錄")
        print(f"年份範圍: {salary_df['yearID'].min()} - {salary_df['yearID'].max()}")
        
        # 過濾我們需要的年份
        salary_filtered = salary_df[salary_df['yearID'].isin(SALARY_YEARS)].copy()
        print(f"✅ 過濾後: {len(salary_filtered)} 筆 ({SALARY_YEARS[0]}-{SALARY_YEARS[-1]})")
        
        # 統計
        print(f"\n薪資統計:")
        print(f"  最高薪資: ${salary_filtered['salary'].max():,.0f}")
        print(f"  平均薪資: ${salary_filtered['salary'].mean():,.0f}")
        print(f"  球員數: {salary_filtered['playerID'].nunique()}")
        
        return salary_filtered
        
    except Exception as e:
        print(f"❌ 薪資數據收集失敗: {e}")
        return pd.DataFrame()


def organize_salary_by_player(salary_df: pd.DataFrame) -> Dict:
    """
    將薪資數據按球員組織（取最新年份）
    
    Returns:
        {
            'judgeaa01': {
                'current_salary': 40000000,
                'year': 2024,
                'team': 'NYY'
            }
        }
    """
    
    print("\n正在組織薪資數據...")
    
    player_salaries = {}
    
    if not salary_df.empty:
        # 按球員分組，取最新年份的薪資
        for player_id, group in salary_df.groupby('playerID'):
            latest_record = group.sort_values('yearID', ascending=False).iloc[0]
            
            player_salaries[player_id] = {
                'current_salary': int(latest_record['salary']),
                'year': int(latest_record['yearID']),
                'team': latest_record['teamID']
            }
    
    print(f"✅ 組織完成: {len(player_salaries)} 位球員")
    
    return player_salaries


# ============================================
# Phase 4: Statcast 數據收集
# ============================================

def collect_statcast_data_sample() -> Dict:
    """
    收集 Statcast 數據（樣本）
    
    注意：完整的 Statcast 數據量很大，這裡先收集樣本
    實際使用時可能需要分批處理
    
    Returns:
        Dictionary with Statcast metrics by player
    """
    
    print("\n" + "=" * 80)
    print("Phase 4: 收集 Statcast 數據（樣本）")
    print("=" * 80)
    
    print("⚠️  Statcast 數據量很大，建議使用 statcast_batter() 和 statcast_pitcher()")
    print("⚠️  這裡先建立數據結構，實際收集需要分批處理")
    
    # 範例結構
    statcast_data = {
        'note': 'Statcast 數據需要按球員分批收集',
        'years': STATCAST_YEARS,
        'metrics': [
            'exit_velocity_avg',
            'launch_angle_avg', 
            'sprint_speed',
            'hard_hit_pct',
            'barrel_pct',
            'xBA',
            'xwOBA'
        ],
        'example': {
            'Aaron Judge': {
                'exit_velocity_avg': 95.5,
                'launch_angle_avg': 15.2,
                'hard_hit_pct': 52.3,
                'barrel_pct': 18.5
            }
        }
    }
    
    print("✅ Statcast 數據結構已建立")
    print(f"   年份: {STATCAST_YEARS}")
    print(f"   指標: {len(statcast_data['metrics'])} 項")
    
    return statcast_data


# ============================================
# 主程式
# ============================================

def main():
    """主執行流程"""
    
    print("=" * 80)
    print("Week 5: 完整數據收集")
    print("=" * 80)
    print(f"Phase 2 - 獎項: {AWARDS_YEARS}")
    print(f"Phase 3 - 薪資: {SALARY_YEARS}")
    print(f"Phase 4 - Statcast: {STATCAST_YEARS}")
    print("=" * 80)
    
    # Phase 2: 獎項
    awards_df = collect_awards_data()
    allstar_df = collect_allstar_data()
    player_awards = organize_awards_by_player(awards_df, allstar_df)
    
    # Phase 3: 薪資
    salary_df = collect_salary_data()
    player_salaries = organize_salary_by_player(salary_df)
    
    # Phase 4: Statcast（樣本）
    statcast_data = collect_statcast_data_sample()
    
    # 儲存數據
    print("\n" + "=" * 80)
    print("儲存數據")
    print("=" * 80)
    
    # 儲存獎項
    output_awards = "./mlb_data/week5_awards.json"
    with open(output_awards, 'w', encoding='utf-8') as f:
        json.dump(player_awards, f, indent=2, ensure_ascii=False)
    print(f"✅ 獎項數據: {output_awards}")
    
    # 儲存薪資
    output_salary = "./mlb_data/week5_salaries.json"
    with open(output_salary, 'w', encoding='utf-8') as f:
        json.dump(player_salaries, f, indent=2, ensure_ascii=False)
    print(f"✅ 薪資數據: {output_salary}")
    
    # 儲存 Statcast
    output_statcast = "./mlb_data/week5_statcast_structure.json"
    with open(output_statcast, 'w', encoding='utf-8') as f:
        json.dump(statcast_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Statcast 結構: {output_statcast}")
    
    # 統計
    print("\n" + "=" * 80)
    print("收集完成統計")
    print("=" * 80)
    print(f"獎項: {len(player_awards)} 位球員")
    print(f"薪資: {len(player_salaries)} 位球員")
    print(f"Statcast: 結構已建立")
    
    # 顯示樣本
    print("\n[獎項樣本]")
    sample_awards = list(player_awards.items())[:3]
    for player_id, awards in sample_awards:
        print(f"\n{player_id}:")
        for award_type, years in awards.items():
            if award_type != 'total_count':
                print(f"  {award_type}: {years}")
    
    print("\n[薪資樣本]")
    sample_salaries = list(player_salaries.items())[:3]
    for player_id, salary_info in sample_salaries:
        print(f"\n{player_id}:")
        print(f"  薪資: ${salary_info['current_salary']:,}")
        print(f"  年份: {salary_info['year']}")
        print(f"  球隊: {salary_info['team']}")
    
    print("\n" + "=" * 80)
    print("✨ Week 5 數據收集完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
