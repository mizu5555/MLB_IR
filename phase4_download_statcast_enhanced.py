"""
Phase 4 Enhanced: 下載所有可用的 Statcast 數據
包含打者和投手的所有進階指標
"""

import pandas as pd
import json
from datetime import datetime
import time


def download_season_statcast_batters(year: int) -> pd.DataFrame:
    """
    下載打者完整 Statcast 數據
    
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
        print(f"  ✅ 可用欄位: {len(df.columns)} 個")
        
        # 定義所有可能的 Statcast 欄位（按類別）
        
        # 基本信息
        basic_cols = ['Name', 'Team', 'PA', 'AB', 'H', '1B', '2B', '3B', 'HR', 'R', 'RBI']
        
        # 進階打擊指標
        advanced_cols = ['AVG', 'OBP', 'SLG', 'OPS', 'wOBA', 'wRC+', 'ISO', 'BABIP']
        
        # Statcast 擊球質量
        batted_ball_cols = [
            'EV', 'LA', 'Barrel%', 'HardHit%', 'maxEV',
            'GB%', 'FB%', 'LD%', 'IFFB%', 'Pull%', 'Cent%', 'Oppo%',
            'Soft%', 'Med%', 'Hard%', 'HR/FB'
        ]
        
        # Statcast 預期數據
        expected_cols = ['xBA', 'xSLG', 'xwOBA', 'xISO', 'xAVG', 'xOBP']
        
        # 紀律性指標
        discipline_cols = [
            'BB%', 'K%', 'BB/K', 'O-Swing%', 'Z-Swing%', 'Swing%',
            'O-Contact%', 'Z-Contact%', 'Contact%', 'Zone%', 'F-Strike%',
            'SwStr%', 'CStr%'
        ]
        
        # 跑壘指標
        baserunning_cols = ['Sprint Speed', 'Spd', 'wSB', 'UBR', 'wRC', 'BsR']
        
        # 綜合價值
        value_cols = ['WAR', 'Off', 'Def', 'RAR', 'Dollars']
        
        # 合併所有欄位
        all_desired_cols = (basic_cols + advanced_cols + batted_ball_cols + 
                           expected_cols + discipline_cols + baserunning_cols + 
                           value_cols)
        
        # 檢查哪些欄位存在
        available_columns = ['Name']  # 確保有 Name
        for col in all_desired_cols:
            if col in df.columns and col != 'Name':
                available_columns.append(col)
        
        print(f"  ✅ 找到 {len(available_columns)} 個相關欄位")
        
        df_filtered = df[available_columns].copy()
        
        # 重命名關鍵欄位（保持原始名稱的也可以）
        column_mapping = {
            'Name': 'player_name'
        }
        
        df_filtered = df_filtered.rename(columns=column_mapping)
        
        # 添加年份
        df_filtered['year'] = year
        
        return df_filtered
        
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return pd.DataFrame()


def download_season_statcast_pitchers(year: int) -> pd.DataFrame:
    """
    下載投手完整 Statcast 數據
    
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
        print(f"  ✅ 可用欄位: {len(df.columns)} 個")
        
        # 定義所有可能的投手 Statcast 欄位
        
        # 基本信息
        basic_cols = ['Name', 'Team', 'W', 'L', 'SV', 'G', 'GS', 'IP', 'H', 'R', 'ER', 'HR', 'BB', 'SO']
        
        # 進階投球指標
        advanced_cols = ['ERA', 'WHIP', 'K/9', 'BB/9', 'K%', 'BB%', 'K-BB%', 'FIP', 'xFIP', 'SIERA']
        
        # 球種分布
        pitch_mix_cols = ['FA%', 'FT%', 'FC%', 'FS%', 'FO%', 'SI%', 'SL%', 'CU%', 'KC%', 'EP%', 'CH%', 'SC%', 'KN%']
        
        # 球速
        velocity_cols = ['FAv', 'FTv', 'FCv', 'FSv', 'FOv', 'SIv', 'SLv', 'CUv', 'KCv', 'EPv', 'CHv', 'SCV', 'KNv', 'vFA (pi)']
        
        # Statcast 投球質量
        statcast_cols = [
            'Barrel%', 'HardHit%', 'EV', 'LA', 'maxEV',
            'GB%', 'FB%', 'LD%', 'IFFB%', 'Pull%', 'Cent%', 'Oppo%',
            'Soft%', 'Med%', 'Hard%', 'HR/FB'
        ]
        
        # 預期數據
        expected_cols = ['xBA', 'xSLG', 'xwOBA', 'xISO', 'xERA', 'xFIP']
        
        # 控球指標
        control_cols = [
            'O-Swing%', 'Z-Swing%', 'Swing%', 'O-Contact%', 'Z-Contact%', 
            'Contact%', 'Zone%', 'F-Strike%', 'SwStr%', 'CStr%',
            'CSW%', 'Chase%', 'Whiff%', 'Called Strike%'
        ]
        
        # 進階指標
        misc_cols = ['LOB%', 'HR/9', 'wOBA', 'BABIP', 'FIP-', 'xFIP-', 'K/BB']
        
        # 綜合價值
        value_cols = ['WAR', 'RA9-WAR', 'RAR', 'Dollars']
        
        # 合併所有欄位
        all_desired_cols = (basic_cols + advanced_cols + pitch_mix_cols + 
                           velocity_cols + statcast_cols + expected_cols + 
                           control_cols + misc_cols + value_cols)
        
        # 檢查哪些欄位存在
        available_columns = ['Name']
        for col in all_desired_cols:
            if col in df.columns and col != 'Name':
                available_columns.append(col)
        
        print(f"  ✅ 找到 {len(available_columns)} 個相關欄位")
        
        df_filtered = df[available_columns].copy()
        
        # 重命名關鍵欄位
        column_mapping = {
            'Name': 'player_name'
        }
        
        df_filtered = df_filtered.rename(columns=column_mapping)
        
        # 添加年份
        df_filtered['year'] = year
        
        return df_filtered
        
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return pd.DataFrame()


def download_all_years(years: list = [2022, 2023, 2024]) -> tuple:
    """
    下載多個年份的數據
    
    Args:
        years: 年份列表
    
    Returns:
        (打者 DataFrame, 投手 DataFrame)
    """
    
    all_batters = []
    all_pitchers = []
    
    for year in years:
        print(f"\n{'=' * 80}")
        print(f"處理 {year} 年數據")
        print('=' * 80)
        
        # 下載打者數據
        batters_df = download_season_statcast_batters(year)
        if not batters_df.empty:
            all_batters.append(batters_df)
        
        # 禮貌性延遲
        print("  ⏳ 等待 3 秒...")
        time.sleep(3)
        
        # 下載投手數據
        pitchers_df = download_season_statcast_pitchers(year)
        if not pitchers_df.empty:
            all_pitchers.append(pitchers_df)
        
        # 禮貌性延遲（除了最後一年）
        if year != years[-1]:
            print("  ⏳ 等待 3 秒...")
            time.sleep(3)
    
    # 合併所有年份
    batters_combined = pd.concat(all_batters, ignore_index=True) if all_batters else pd.DataFrame()
    pitchers_combined = pd.concat(all_pitchers, ignore_index=True) if all_pitchers else pd.DataFrame()
    
    return batters_combined, pitchers_combined


def save_data(batters_df: pd.DataFrame, pitchers_df: pd.DataFrame):
    """
    儲存數據為 CSV 和 JSON
    
    Args:
        batters_df: 打者數據
        pitchers_df: 投手數據
    """
    
    print("\n" + "=" * 80)
    print("儲存數據")
    print("=" * 80)
    
    # 儲存 CSV
    batters_csv = './mlb_data/statcast_batters_enhanced.csv'
    pitchers_csv = './mlb_data/statcast_pitchers_enhanced.csv'
    
    batters_df.to_csv(batters_csv, index=False, encoding='utf-8')
    pitchers_df.to_csv(pitchers_csv, index=False, encoding='utf-8')
    
    print(f"✅ 打者 CSV: {batters_csv}")
    print(f"✅ 投手 CSV: {pitchers_csv}")
    
    # 轉換為 JSON 格式
    print("\n轉換為 JSON 格式...")
    
    statcast_json = {}
    
    # 處理打者
    for _, row in batters_df.iterrows():
        player_name = row['player_name']
        year = row['year']
        key = f"{player_name}_{year}"
        
        # 轉換為字典，跳過 NaN
        data = {
            'player_name': player_name,
            'year': int(year),
            'type': 'batter'
        }
        
        for col in batters_df.columns:
            if col not in ['player_name', 'year']:
                val = row[col]
                # 安全檢查：跳過 NaN 和 None
                try:
                    # 檢查是否是 NaN（支援多種類型）
                    if pd.isna(val):
                        continue
                    
                    # 轉換數值類型
                    if isinstance(val, (int, float)):
                        data[col] = float(val)
                    elif isinstance(val, str):
                        data[col] = val
                    else:
                        # 嘗試轉換為字串
                        data[col] = str(val)
                except (ValueError, TypeError):
                    # 如果轉換失敗，跳過這個欄位
                    continue
        
        statcast_json[key] = data
    
    # 處理投手
    for _, row in pitchers_df.iterrows():
        player_name = row['player_name']
        year = row['year']
        key = f"{player_name}_{year}"
        
        data = {
            'player_name': player_name,
            'year': int(year),
            'type': 'pitcher'
        }
        
        for col in pitchers_df.columns:
            if col not in ['player_name', 'year']:
                val = row[col]
                # 安全檢查：跳過 NaN 和 None
                try:
                    if pd.isna(val):
                        continue
                    
                    # 轉換數值類型
                    if isinstance(val, (int, float)):
                        data[col] = float(val)
                    elif isinstance(val, str):
                        data[col] = val
                    else:
                        data[col] = str(val)
                except (ValueError, TypeError):
                    continue
        
        statcast_json[key] = data
    
    # 儲存 JSON
    json_file = './mlb_data/week5_statcast_enhanced.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(statcast_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON: {json_file}")
    print(f"   總球員數: {len(statcast_json)}")
    
    # 統計
    print("\n數據統計:")
    print(f"  打者記錄: {len(batters_df)}")
    print(f"  投手記錄: {len(pitchers_df)}")
    print(f"  打者欄位數: {len(batters_df.columns)}")
    print(f"  投手欄位數: {len(pitchers_df.columns)}")


def main():
    """主程式"""
    
    print("=" * 80)
    print("Phase 4 Enhanced: 下載完整 Statcast 數據")
    print("=" * 80)
    print("\n這會下載所有可用的進階棒球數據指標")
    print("預計時間: 10-15 分鐘")
    print("\n包含:")
    print("  ✅ 所有打者進階數據（擊球質量、預期數據、紀律性等）")
    print("  ✅ 所有投手進階數據（球種、球速、控球、預期數據等）")
    print("  ✅ 2022-2024 三個完整賽季")
    
    # 下載數據
    batters_df, pitchers_df = download_all_years([2022, 2023, 2024])
    
    if batters_df.empty and pitchers_df.empty:
        print("\n❌ 沒有數據被下載")
        return
    
    # 儲存數據
    save_data(batters_df, pitchers_df)
    
    print("\n" + "=" * 80)
    print("✨ 完成！")
    print("=" * 80)
    print("\n下一步:")
    print("  python phase4_integrate_statcast_enhanced.py  # 整合增強數據")


if __name__ == "__main__":
    main()
