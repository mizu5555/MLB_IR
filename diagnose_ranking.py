"""
診斷 Ranking 查詢問題
測試：Who has the highest wRC+ in 2023?
"""

import pandas as pd
import json
import os

print("=" * 80)
print("Ranking 查詢診斷")
print("=" * 80)

# 載入數據
DATA_DIR = "./mlb_data"

# 檢查哪個文件存在
docs_file_new = os.path.join(DATA_DIR, "mlb_players_2022_2025.json")
docs_file_old = os.path.join(DATA_DIR, "mlb_documents.json")

if os.path.exists(docs_file_new):
    docs_file = docs_file_new
    print(f"✅ 使用新數據文件：{docs_file_new}")
elif os.path.exists(docs_file_old):
    docs_file = docs_file_old
    print(f"⚠️  使用舊數據文件：{docs_file_old}")
else:
    print("❌ 找不到數據文件！")
    exit(1)

with open(docs_file, 'r', encoding='utf-8') as f:
    all_documents = json.load(f)

docs_df = pd.DataFrame(all_documents)

print(f"\n[檢查 1] 數據基本資訊")
print(f"總記錄數：{len(docs_df)}")
print(f"賽季範圍：{docs_df['season'].min()} - {docs_df['season'].max()}")

# 模擬 ranking 查詢
query = "Who has the highest wRC+ in 2023?"
print(f"\n[檢查 2] 模擬查詢：{query}")

# 提取年份
import re
year_pattern = r'\b(202[0-9])\b'
match = re.search(year_pattern, query)
target_year = int(match.group(1)) if match else None
print(f"提取年份：{target_year}")

# 過濾打者
player_type = 'batter'
filtered_df = docs_df[docs_df['type'] == player_type].copy()
print(f"打者總數：{len(filtered_df)}")

# 過濾年份
if target_year:
    filtered_df = filtered_df[filtered_df['season'] == target_year]
    print(f"過濾到 {target_year} 年：{len(filtered_df)} 位打者")
else:
    max_season = filtered_df['season'].max()
    filtered_df = filtered_df[filtered_df['season'] == max_season]
    print(f"使用最新賽季 {max_season}：{len(filtered_df)} 位打者")

# 提取 wRC+ 數據
stat_col = 'wRC_plus'
filtered_df['sort_stat'] = filtered_df['stats'].apply(
    lambda x: x.get(stat_col, 0) if isinstance(x, dict) else 0
)

print(f"\n[檢查 3] wRC+ 數據統計")
print(f"有 wRC+ 數據的球員：{(filtered_df['sort_stat'] > 0).sum()}")
print(f"wRC+ 最高值：{filtered_df['sort_stat'].max()}")
print(f"wRC+ 最低值：{filtered_df['sort_stat'].min()}")

# 過濾掉 0 值
filtered_df = filtered_df[filtered_df['sort_stat'] > 0]
print(f"過濾掉 0 值後：{len(filtered_df)} 位")

# 樣本門檻
filtered_df['pa'] = filtered_df['stats'].apply(
    lambda x: x.get('PA', 0) if isinstance(x, dict) else 0
)
print(f"\n[檢查 4] 打席數統計")
print(f"有打席數據的球員：{(filtered_df['pa'] > 0).sum()}")
print(f"打席數 >= 100 的球員：{(filtered_df['pa'] >= 100).sum()}")

filtered_df = filtered_df[filtered_df['pa'] >= 100]
print(f"套用門檻後：{len(filtered_df)} 位")

# 排序
sorted_df = filtered_df.sort_values('sort_stat', ascending=False)
top_5 = sorted_df.head(5)

print(f"\n[檢查 5] Top 5 結果：")
for idx, row in top_5.iterrows():
    print(f"  {row['player_name']} ({row['team']}) - wRC+: {row['sort_stat']:.1f} (PA: {row['pa']:.0f})")

# 檢查數據結構
print(f"\n[檢查 6] 數據結構檢查")
if len(top_5) > 0:
    first_player = top_5.iloc[0]
    print(f"第一名球員：{first_player['player_name']}")
    print(f"stats 類型：{type(first_player['stats'])}")
    print(f"stats 內容樣本：{list(first_player['stats'].keys())[:10] if isinstance(first_player['stats'], dict) else 'Not a dict!'}")
else:
    print("❌ 沒有找到任何符合條件的球員！")

print("\n" + "=" * 80)
print("診斷完成")
print("=" * 80)
