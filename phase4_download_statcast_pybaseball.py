"""
Phase 4: 使用 pybaseball 下載 Statcast 數據（備選方案）
這個方法更可靠，但速度較慢
"""

import pandas as pd
import json
from datetime import datetime
import time


def download_season_statcast_batters(year: int) -> pd.DataFrame:
    """
    使用 pybaseball 下載打者 Statcast 數據
    
    Args:
        year: 年份
    
    Returns:
        DataFrame
    """
    
    print(f"\n下載 {year} 打者 Statcast 數據...")
    
    try:
        from pybaseball import batting_stats
        
        # 獲取該年度打擊數據
        df = batting_stats(year, qual=50)  # 最少 50 PA
        
        print(f"  ✅ 成功下載 {len(df)} 位打者")
        
        # 選擇需要的欄位
        columns_to_keep = [
            'Name', 'PA', 'Barrel%', 'HardHit%', 
            'EV', 'LA', 'xBA', 'xSLG', 'xwOBA', 'Sprint Speed'
        ]
        
        # 檢查哪些欄位存在
        available_columns = [col for col in columns_to_keep if col in df.columns]
        
        if not available_columns:
            print(f"  ⚠️  找不到 Statcast 欄位")
            return pd.DataFrame()
        
        df_filtered = df[available_columns].copy()
        
        # 重命名欄位
        column_mapping = {
            'Name': 'player_name',
            'PA': 'PA',
            'Barrel%': 'barrel_rate',
            'HardHit%': 'hard_hit_rate',
            'EV': 'exit_velocity',
            'LA': 'launch_angle',
            'xBA': 'xba',
            'xSLG': 'xslg',
            'xwOBA': 'xwoba',
            'Sprint Speed': 'sprint_speed'
        }
        
        df_filtered = df_filtered.rename(columns=column_mapping)
        df_filtered['year'] = year
        
        return df_filtered
        
    except ImportError:
        print("  ❌ pybaseball 未安裝")
        print("  請執行: pip install pybaseball --break-system-packages")
        return pd.DataFrame()
    except Exception as e:
        print(f"  ❌ 下載失敗: {e}")
        return pd.DataFrame()


def download_season_statcast_pitchers(year: int) -> pd.DataFrame:
    """
    使用 pybaseball 下載投手 Statcast 數據
    
    Args:
        year: 年份
    
    Returns:
        DataFrame
    """
    
    print(f"\n下載 {year} 投手 Statcast 數據...")
    
    try:
        from pybaseball import pitching_stats
        
        # 獲取該年度投球數據
        df = pitching_stats(year, qual=20)  # 最少 20 IP
        
        print(f"  ✅ 成功下載 {len(df)} 位投手")
        
        # 選擇需要的欄位
        columns_to_keep = [
            'Name', 'IP', 'FB%', 'FBv', 
            'K%', 'Whiff%', 'Chase%', 'Barrel%', 'HardHit%'
        ]
        
        # 檢查哪些欄位存在
        available_columns = [col for col in columns_to_keep if col in df.columns]
        
        if not available_columns:
            print(f"  ⚠️  找不到 Statcast 欄位")
            return pd.DataFrame()
        
        df_filtered = df[available_columns].copy()
        
        # 重命名欄位
        column_mapping = {
            'Name': 'player_name',
            'IP': 'IP',
            'FB%': 'fastball_percent',
            'FBv': 'fastball_velocity',
            'K%': 'strikeout_rate',
            'Whiff%': 'whiff_rate',
            'Chase%': 'chase_rate',
            'Barrel%': 'barrel_rate_against',
            'HardHit%': 'hard_hit_rate_against'
        }
        
        df_filtered = df_filtered.rename(columns=column_mapping)
        df_filtered['year'] = year
        
        return df_filtered
        
    except ImportError:
        print("  ❌ pybaseball 未安裝")
        print("  請執行: pip install pybaseball --break-system-packages")
        return pd.DataFrame()
    except Exception as e:
        print(f"  ❌ 下載失敗: {e}")
        return pd.DataFrame()


def download_all_years(years: list) -> dict:
    """下載多年數據"""
    
    print("=" * 80)
    print("Phase 4: 使用 pybaseball 下載 Statcast 數據")
    print("=" * 80)
    print("\n注意：pybaseball 需要從 FanGraphs 爬取數據")
    print("這可能需要 10-15 分鐘...\n")
    
    all_batters = []
    all_pitchers = []
    
    for year in years:
        print(f"\n{'=' * 80}")
        print(f"處理 {year} 年")
        print('=' * 80)
        
        # 下載打者
        batters_df = download_season_statcast_batters(year)
        if not batters_df.empty:
            all_batters.append(batters_df)
        
        time.sleep(3)  # 禮貌性延遲
        
        # 下載投手
        pitchers_df = download_season_statcast_pitchers(year)
        if not pitchers_df.empty:
            all_pitchers.append(pitchers_df)
        
        time.sleep(3)
    
    # 合併
    batters_combined = pd.concat(all_batters, ignore_index=True) if all_batters else pd.DataFrame()
    pitchers_combined = pd.concat(all_pitchers, ignore_index=True) if all_pitchers else pd.DataFrame()
    
    print("\n" + "=" * 80)
    print("下載完成")
    print("=" * 80)
    print(f"打者數據: {len(batters_combined)} 筆")
    print(f"投手數據: {len(pitchers_combined)} 筆")
    
    return {
        'batters': batters_combined,
        'pitchers': pitchers_combined
    }


def save_data(data: dict):
    """儲存數據"""
    
    print("\n" + "=" * 80)
    print("儲存數據")
    print("=" * 80)
    
    # 儲存 CSV
    if not data['batters'].empty:
        csv_file = './mlb_data/statcast_batters_raw.csv'
        data['batters'].to_csv(csv_file, index=False, encoding='utf-8')
        print(f"✅ 打者 CSV: {csv_file}")
    
    if not data['pitchers'].empty:
        csv_file = './mlb_data/statcast_pitchers_raw.csv'
        data['pitchers'].to_csv(csv_file, index=False, encoding='utf-8')
        print(f"✅ 投手 CSV: {csv_file}")
    
    # 轉換為 JSON
    print("\n轉換為 JSON 格式...")
    
    combined_json = {}
    
    # 打者
    for _, row in data['batters'].iterrows():
        player_name = row.get('player_name', '')
        year = row.get('year', 2024)
        key = f"{player_name}_{year}"
        
        combined_json[key] = {
            'player_name': player_name,
            'year': int(year),
            'type': 'batter',
            'exit_velocity': float(row.get('exit_velocity', 0)) if pd.notna(row.get('exit_velocity')) else None,
            'launch_angle': float(row.get('launch_angle', 0)) if pd.notna(row.get('launch_angle')) else None,
            'barrel_rate': float(row.get('barrel_rate', 0)) if pd.notna(row.get('barrel_rate')) else None,
            'hard_hit_rate': float(row.get('hard_hit_rate', 0)) if pd.notna(row.get('hard_hit_rate')) else None,
            'xba': float(row.get('xba', 0)) if pd.notna(row.get('xba')) else None,
            'xslg': float(row.get('xslg', 0)) if pd.notna(row.get('xslg')) else None,
            'xwoba': float(row.get('xwoba', 0)) if pd.notna(row.get('xwoba')) else None,
            'sprint_speed': float(row.get('sprint_speed', 0)) if pd.notna(row.get('sprint_speed')) else None,
        }
    
    # 投手
    for _, row in data['pitchers'].iterrows():
        player_name = row.get('player_name', '')
        year = row.get('year', 2024)
        key = f"{player_name}_{year}"
        
        combined_json[key] = {
            'player_name': player_name,
            'year': int(year),
            'type': 'pitcher',
            'fastball_velocity': float(row.get('fastball_velocity', 0)) if pd.notna(row.get('fastball_velocity')) else None,
            'fastball_spin': None,  # FanGraphs 沒有這個
            'whiff_rate': float(row.get('whiff_rate', 0)) if pd.notna(row.get('whiff_rate')) else None,
            'chase_rate': float(row.get('chase_rate', 0)) if pd.notna(row.get('chase_rate')) else None,
            'barrel_rate_against': float(row.get('barrel_rate_against', 0)) if pd.notna(row.get('barrel_rate_against')) else None,
            'hard_hit_rate_against': float(row.get('hard_hit_rate_against', 0)) if pd.notna(row.get('hard_hit_rate_against')) else None,
        }
    
    # 儲存 JSON
    output_file = './mlb_data/week5_statcast.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON: {output_file}")
    print(f"   總球員數: {len(combined_json)}")


def main():
    """主程式"""
    
    print("\n" + "=" * 80)
    print("Phase 4: pybaseball 版本（備選方案）")
    print("=" * 80)
    
    # 檢查 pybaseball
    try:
        import pybaseball
        print(f"✅ pybaseball 已安裝: {pybaseball.__version__}")
    except ImportError:
        print("❌ pybaseball 未安裝")
        print("\n請執行:")
        print("  pip install pybaseball --break-system-packages")
        return
    
    years = [2022, 2023, 2024]
    
    print(f"\n準備下載 {years} 年份的數據...")
    print("預計時間：10-15 分鐘\n")
    
    try:
        # 下載數據
        data = download_all_years(years)
        
        # 儲存數據
        save_data(data)
        
        print("\n" + "=" * 80)
        print("✨ 下載完成！")
        print("=" * 80)
        print("\n下一步:")
        print("  python phase4_integrate_statcast.py")
        
    except KeyboardInterrupt:
        print("\n\n下載被中斷")
    except Exception as e:
        print(f"\n\n❌ 下載失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
