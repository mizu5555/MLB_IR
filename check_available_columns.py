"""
檢查 pybaseball 所有可用的 Statcast 欄位
"""

import pandas as pd
from pybaseball import batting_stats, pitching_stats

print("=" * 80)
print("檢查 pybaseball 可用欄位")
print("=" * 80)

# 檢查打者欄位
print("\n下載 2024 年打者數據樣本...")
df_batters = batting_stats(2024, qual=100)
print(f"✅ 下載 {len(df_batters)} 位打者")

print("\n打者可用欄位 (共 {} 個):".format(len(df_batters.columns)))
print("-" * 80)
for i, col in enumerate(df_batters.columns, 1):
    print(f"{i:3d}. {col}")

# 檢查投手欄位
print("\n" + "=" * 80)
print("\n下載 2024 年投手數據樣本...")
df_pitchers = pitching_stats(2024, qual=50)
print(f"✅ 下載 {len(df_pitchers)} 位投手")

print("\n投手可用欄位 (共 {} 個):".format(len(df_pitchers.columns)))
print("-" * 80)
for i, col in enumerate(df_pitchers.columns, 1):
    print(f"{i:3d}. {col}")

# 儲存欄位清單
print("\n" + "=" * 80)
print("儲存欄位清單...")

with open('./mlb_data/available_columns.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("打者可用欄位 (共 {} 個)\n".format(len(df_batters.columns)))
    f.write("=" * 80 + "\n\n")
    
    for i, col in enumerate(df_batters.columns, 1):
        # 顯示欄位名稱和樣本值
        sample_val = df_batters[col].iloc[0] if len(df_batters) > 0 else None
        f.write(f"{i:3d}. {col:30s} (範例: {sample_val})\n")
    
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("投手可用欄位 (共 {} 個)\n".format(len(df_pitchers.columns)))
    f.write("=" * 80 + "\n\n")
    
    for i, col in enumerate(df_pitchers.columns, 1):
        sample_val = df_pitchers[col].iloc[0] if len(df_pitchers) > 0 else None
        f.write(f"{i:3d}. {col:30s} (範例: {sample_val})\n")

print("✅ 已儲存: ./mlb_data/available_columns.txt")

# 顯示一些重要的 Statcast 欄位
print("\n" + "=" * 80)
print("重要的 Statcast 欄位")
print("=" * 80)

statcast_keywords = ['xwOBA', 'xBA', 'xSLG', 'EV', 'LA', 'Barrel', 'HardHit', 
                     'Whiff', 'Chase', 'FB%', 'FBv', 'Sprint', 'Swing%', 
                     'Contact%', 'Zone%', 'O-Swing%', 'Z-Swing%', 'O-Contact%', 'Z-Contact%',
                     'Pull%', 'Cent%', 'Oppo%', 'Soft%', 'Med%', 'Hard%',
                     'GB%', 'FB%', 'LD%', 'IFFB%', 'HR/FB']

print("\n打者 Statcast 欄位:")
for col in df_batters.columns:
    for keyword in statcast_keywords:
        if keyword.lower() in col.lower():
            print(f"  ✅ {col}")
            break

print("\n投手 Statcast 欄位:")
for col in df_pitchers.columns:
    for keyword in statcast_keywords:
        if keyword.lower() in col.lower():
            print(f"  ✅ {col}")
            break

print("\n" + "=" * 80)
print("✨ 完成！檢查 available_columns.txt 查看完整清單")
print("=" * 80)
