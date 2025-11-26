"""
快速驗證：檢查資料庫中實際有哪些年份的數據
"""

import lancedb
import pandas as pd

print("=" * 80)
print("資料庫內容驗證")
print("=" * 80)

# 連接資料庫
db = lancedb.connect("./mlb_data/lancedb")
table = db.open_table("mlb_players")

print("\n[檢查 1] 資料庫統計...")

# 轉換為 DataFrame
df = table.to_pandas()

print(f"總記錄數：{len(df)}")

# 統計每個賽季的數據量
season_counts = df['season'].value_counts().sort_index()

print("\n[檢查 2] 各賽季數據分布：")
for season, count in season_counts.items():
    print(f"  {season}: {count} 筆")

print(f"\n[檢查 3] 賽季範圍：{df['season'].min()} - {df['season'].max()}")

# 測試每個賽季是否都能搜尋到 Aaron Judge
print("\n[檢查 4] 測試 Aaron Judge 各賽季數據...")

from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

for season in sorted(season_counts.index):
    # 搜尋 Aaron Judge 在該賽季的數據
    query_vector = model.encode("Aaron Judge")
    results = table.search(query_vector).limit(20).to_list()
    
    # 找該賽季的 Aaron Judge
    found = False
    for r in results:
        if r['player_name'] == 'Aaron Judge' and r['season'] == season:
            hr = r.get('stat_HR', 0)
            print(f"  ✅ {season}: Aaron Judge (HR: {hr:.0f})")
            found = True
            break
    
    if not found:
        print(f"  ❌ {season}: Aaron Judge 找不到")

print("\n" + "=" * 80)
print("驗證完成")
print("=" * 80)

# 額外檢查：看看 2022 和 2025 的數據是否正常
print("\n[額外檢查] 2022 年樣本數據（前 3 筆）：")
df_2022 = df[df['season'] == 2022].head(3)
for idx, row in df_2022.iterrows():
    print(f"  {row['player_name']} ({row['team']}) - {row['type']}")

if 2025 in season_counts.index:
    print("\n[額外檢查] 2025 年樣本數據（前 3 筆）：")
    df_2025 = df[df['season'] == 2025].head(3)
    for idx, row in df_2025.iterrows():
        print(f"  {row['player_name']} ({row['team']}) - {row['type']}")
