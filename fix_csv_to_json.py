"""
快速修復：從現有 CSV 轉換為 JSON
不需要重新下載數據
"""

import pandas as pd
import json


def convert_csv_to_json():
    """從 CSV 轉換為 JSON"""
    
    print("=" * 80)
    print("從 CSV 轉換為 JSON")
    print("=" * 80)
    
    # 讀取 CSV
    print("\n讀取 CSV...")
    batters_df = pd.read_csv('./mlb_data/statcast_batters_enhanced.csv')
    pitchers_df = pd.read_csv('./mlb_data/statcast_pitchers_enhanced.csv')
    
    print(f"✅ 打者: {len(batters_df)} 筆，{len(batters_df.columns)} 欄位")
    print(f"✅ 投手: {len(pitchers_df)} 筆，{len(pitchers_df.columns)} 欄位")
    
    # 轉換為 JSON
    print("\n轉換為 JSON 格式...")
    
    statcast_json = {}
    
    # 處理打者
    print("處理打者數據...")
    for idx, row in batters_df.iterrows():
        player_name = row['player_name']
        year = row['year']
        key = f"{player_name}_{year}"
        
        data = {
            'player_name': player_name,
            'year': int(year),
            'type': 'batter'
        }
        
        for col in batters_df.columns:
            if col not in ['player_name', 'year']:
                val = row[col]
                
                # 安全檢查：跳過 NaN
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
    
    # 處理投手
    print("處理投手數據...")
    for idx, row in pitchers_df.iterrows():
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
                
                try:
                    if pd.isna(val):
                        continue
                    
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
    print("\n儲存 JSON...")
    json_file = './mlb_data/week5_statcast_enhanced.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(statcast_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已儲存: {json_file}")
    print(f"   總球員數: {len(statcast_json)}")
    
    # 統計
    print("\n數據統計:")
    print(f"  打者記錄: {len(batters_df)}")
    print(f"  投手記錄: {len(pitchers_df)}")
    print(f"  總記錄: {len(statcast_json)}")
    
    # 顯示範例
    print("\n範例數據:")
    sample_keys = list(statcast_json.keys())[:3]
    for key in sample_keys:
        data = statcast_json[key]
        print(f"\n{key}:")
        print(f"  類型: {data['type']}")
        print(f"  欄位數: {len(data) - 3}")  # 扣除 player_name, year, type
    
    print("\n" + "=" * 80)
    print("✨ 轉換完成！")
    print("=" * 80)
    print("\n下一步:")
    print("  python phase4_integrate_statcast_enhanced.py")


if __name__ == "__main__":
    convert_csv_to_json()
