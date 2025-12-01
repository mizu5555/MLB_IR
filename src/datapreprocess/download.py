"""
下載所有可用的 Statcast 數據 (FanGraphs Source)
功能: 
1. 下載 2022-2024 打者與投手數據
2. 處理交易球員重複問題 (保留 Total)
3. 輸出 statcast_batters_enhanced.csv 和 statcast_pitchers_enhanced.csv
"""

import pandas as pd
import json
import time
import os
from pybaseball import batting_stats, pitching_stats

# === 1. 路徑設定 (自動抓取相對路徑) ===
# 取得目前腳本所在的目錄 (src/datapreprocess)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 設定輸出目錄 (回到根目錄 -> data -> raw_adv)
OUTPUT_DIR = os.path.join(CURRENT_DIR, '..', '..', 'data', 'raw_adv')

# 確保目錄存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"建立目錄: {OUTPUT_DIR}")

def download_season_statcast_batters(year: int) -> pd.DataFrame:
    """下載打者數據並進行去重處理"""
    print(f"\n下載 {year} 打者數據...")
    
    try:
        # qual=50 抓取較多樣本
        df = batting_stats(year, qual=50)
        
        # === 關鍵修正: 處理交易球員 ===
        # 如果有 IDfg 欄位，依照 PA (打席) 排序，並對 ID 去重
        # 這樣可以確保保留 "Total" (合計) 數據，而非只保留某支球隊的數據
        if 'IDfg' in df.columns:
            original_len = len(df)
            # 依照 PA 降序排列 (由大到小)，然後保留第一個 ID (即 PA 最多的那筆)
            df = df.sort_values('PA', ascending=False).drop_duplicates(subset=['IDfg'], keep='first')
            print(f"  🔹 去除重複/交易球員後: {original_len} -> {len(df)} 位打者")
        
        # 複製並整理
        df_filtered = df.copy()
        
        # 重命名關鍵欄位，方便後續對照
        column_mapping = {
            'Name': 'player_name',
            'IDfg': 'player_id'
        }
        df_filtered = df_filtered.rename(columns=column_mapping)
        
        # 添加年份
        df_filtered['year'] = year
        
        return df_filtered
        
    except Exception as e:
        print(f"下載打者錯誤: {e}")
        return pd.DataFrame()

def download_season_statcast_pitchers(year: int) -> pd.DataFrame:
    """下載投手數據並進行去重處理"""
    print(f"\n下載 {year} 投手數據...")
    
    try:
        # qual=20 抓取較多樣本
        df = pitching_stats(year, qual=20)
        
        # === 關鍵修正: 處理交易球員 ===
        # 投手依照 IP (投球局數) 排序去重
        if 'IDfg' in df.columns:
            original_len = len(df)
            df = df.sort_values('IP', ascending=False).drop_duplicates(subset=['IDfg'], keep='first')
            print(f"  🔹 去除重複/交易球員後: {original_len} -> {len(df)} 位投手")

        df_filtered = df.copy()
        
        # 重命名
        column_mapping = {
            'Name': 'player_name',
            'IDfg': 'player_id'
        }
        df_filtered = df_filtered.rename(columns=column_mapping)
        
        # 添加年份
        df_filtered['year'] = year
        
        return df_filtered
        
    except Exception as e:
        print(f"下載投手錯誤: {e}")
        return pd.DataFrame()

def download_all_years(years: list = [2022, 2023, 2024]):
    """下載多個年份並合併"""
    all_batters = []
    all_pitchers = []
    
    for year in years:
        # 打者
        b_df = download_season_statcast_batters(year)
        if not b_df.empty:
            all_batters.append(b_df)
        
        print("  ⏳ 休息 2 秒...")
        time.sleep(2)
        
        # 投手
        p_df = download_season_statcast_pitchers(year)
        if not p_df.empty:
            all_pitchers.append(p_df)
            
        if year != years[-1]:
            time.sleep(2)
    
    # 合併 DataFrame
    batters_combined = pd.concat(all_batters, ignore_index=True) if all_batters else pd.DataFrame()
    pitchers_combined = pd.concat(all_pitchers, ignore_index=True) if all_pitchers else pd.DataFrame()
    
    return batters_combined, pitchers_combined

def save_data(batters_df: pd.DataFrame, pitchers_df: pd.DataFrame):
    """儲存 CSV 和 JSON (修正版：防止二刀流覆蓋)"""
    
    print("\n" + "=" * 80)
    print(f"儲存數據至: {OUTPUT_DIR}")
    print("=" * 80)
    
    # 1. 儲存 CSV (保持不變)
    batters_csv = os.path.join(OUTPUT_DIR, 'statcast_batters_enhanced.csv')
    pitchers_csv = os.path.join(OUTPUT_DIR, 'statcast_pitchers_enhanced.csv')
    batters_df.to_csv(batters_csv, index=False, encoding='utf-8')
    pitchers_df.to_csv(pitchers_csv, index=False, encoding='utf-8')
    print(f"✅ CSV 已儲存")
    
    # 2. 轉換為 JSON
    print("\n轉換為 JSON 格式 (Key 加入 Type 以防止覆蓋)...")
    
    statcast_json = {}
    
    def process_to_json(df, p_type):
        for _, row in df.iterrows():
            if pd.isna(row.get('player_name')): continue
                
            p_name = row['player_name']
            p_id = row.get('player_id', 'unknown')
            year = row['year']
            
            # === 修正重點 ===
            # 加入 p_type，確保 "Shohei Ohtani_ID_2023_batter" 
            # 和 "Shohei Ohtani_ID_2023_pitcher" 都能並存
            key = f"{p_name}_{p_id}_{year}_{p_type}"
            
            data = {
                'player_name': p_name,
                'player_id': p_id,
                'year': int(year),
                'type': p_type
            }
            
            for col in df.columns:
                if col not in ['player_name', 'year', 'player_id']:
                    val = row[col]
                    try:
                        if pd.isna(val): continue
                        if isinstance(val, (int, float)):
                            data[col] = float(val)
                        else:
                            data[col] = str(val)
                    except: continue
            
            statcast_json[key] = data

    process_to_json(batters_df, 'batter')
    process_to_json(pitchers_df, 'pitcher')
    
    json_file = os.path.join(OUTPUT_DIR, 'statcast_enhanced.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(statcast_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON 檔案: {json_file}")
    print(f"   總記錄數: {len(statcast_json)} (應該比以前多，因為二刀流不再被覆蓋)")

def main():
    print("=" * 80)
    print("Phase 4: 下載 Statcast/FanGraphs 數據")
    print("=" * 80)
    
    batters, pitchers = download_all_years([2022, 2023, 2024])
    
    if not batters.empty or not pitchers.empty:
        save_data(batters, pitchers)
        print("\n下載完成！")
    else:
        print("\n下載失敗，沒有數據被儲存")

if __name__ == "__main__":
    main()