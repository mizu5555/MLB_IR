"""
Week 4: 重建向量資料庫
使用擴充後的數據（2022-2025）重建 Hybrid Search 系統

注意：這會刪除舊的向量資料庫並重新建立
"""

import json
import os
import pandas as pd
import shutil

print("=" * 80)
print("Week 4: 向量資料庫重建")
print("=" * 80)

# ============================================
# Step 1: 載入擴充後的數據
# ============================================
print("\n[Step 1] 載入數據...")

DATA_FILE = "./mlb_data/mlb_players_2022_2025.json"

if not os.path.exists(DATA_FILE):
    print(f"❌ 找不到數據文件：{DATA_FILE}")
    print("請先執行：python week4_data_collection.py")
    exit(1)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    documents = json.load(f)

print(f"✅ 載入 {len(documents)} 筆文檔")

# 統計
season_counts = {}
for doc in documents:
    season = doc['season']
    season_counts[season] = season_counts.get(season, 0) + 1

print("\n📊 數據分布：")
for season in sorted(season_counts.keys()):
    print(f"  {season}: {season_counts[season]} 筆")

# ============================================
# Step 2: 刪除舊的向量資料庫
# ============================================
print("\n[Step 2] 刪除舊的向量資料庫...")

OLD_DB_PATH = "./mlb_data/lancedb"
if os.path.exists(OLD_DB_PATH):
    try:
        shutil.rmtree(OLD_DB_PATH)
        print(f"✅ 已刪除舊資料庫：{OLD_DB_PATH}")
    except Exception as e:
        print(f"⚠️  刪除失敗：{e}")
        print("請手動刪除資料夾並重試")
else:
    print("  （舊資料庫不存在，跳過）")

# ============================================
# Step 3: 導入必要的套件
# ============================================
print("\n[Step 3] 導入套件...")

try:
    import lancedb
    print("✅ lancedb")
except ImportError:
    print("❌ 請安裝：pip install lancedb --break-system-packages")
    exit(1)

try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers")
except ImportError:
    print("❌ 請安裝：pip install sentence-transformers --break-system-packages")
    exit(1)

# ============================================
# Step 4: 準備數據
# ============================================
print("\n[Step 4] 準備數據結構...")

# 轉換為 DataFrame
df = pd.DataFrame(documents)

# 確保所有欄位類型正確
df['season'] = df['season'].astype(int)
df['player_name'] = df['player_name'].astype(str)
df['team'] = df['team'].astype(str)
df['type'] = df['type'].astype(str)
df['text'] = df['text'].astype(str)

# 將 stats 字典轉換為個別欄位
print("  處理統計數據欄位...")

# 先收集所有可能的統計項目
all_stat_keys = set()
for idx, row in df.iterrows():
    stats = row['stats']
    for key in stats.keys():
        all_stat_keys.add(key)

print(f"  發現 {len(all_stat_keys)} 個統計項目")

# 為每個統計項目建立完整的列表（每個球員都有值，沒有的填 0）
for stat_key in all_stat_keys:
    col_name = f"stat_{stat_key}"
    values = []
    
    for idx, row in df.iterrows():
        stats = row['stats']
        value = stats.get(stat_key, 0.0)  # 如果不存在，用 0
        values.append(float(value) if pd.notna(value) else 0.0)
    
    df[col_name] = values

# 移除原始 stats 欄位
df = df.drop(columns=['stats'])

print(f"✅ 數據準備完成：{len(df)} 筆記錄，{len(df.columns)} 個欄位")

# ============================================
# Step 5: 建立 Embeddings
# ============================================
print("\n[Step 5] 建立 Embeddings...")
print("  （這可能需要 5-10 分鐘，取決於資料量）")

# 載入 embedding 模型
print("  載入 embedding 模型...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("  ✅ 模型已載入")

# 生成 embeddings
print("  生成 embeddings...")
embeddings = model.encode(df['text'].tolist(), show_progress_bar=True)
df['vector'] = embeddings.tolist()

print(f"✅ Embeddings 生成完成：{len(embeddings)} 個向量")

# ============================================
# Step 6: 建立 LanceDB 向量資料庫
# ============================================
print("\n[Step 6] 建立 LanceDB 向量資料庫...")

# 連接到 LanceDB
db = lancedb.connect("./mlb_data/lancedb")
print("✅ LanceDB 連接成功")

# 建立表格
table = db.create_table("mlb_players", data=df)
print(f"✅ 表格建立完成：mlb_players")

# ============================================
# Step 7: 建立 FTS 索引
# ============================================
print("\n[Step 7] 建立 Full-Text Search 索引...")

try:
    table.create_fts_index("player_name")
    print("✅ FTS 索引建立完成")
except Exception as e:
    print(f"⚠️  FTS 索引建立失敗：{e}")
    print("  （可能已存在，繼續執行）")

# ============================================
# Step 8: 驗證
# ============================================
print("\n[Step 8] 驗證資料庫...")

# 測試查詢
test_queries = [
    "Aaron Judge",
    "Shohei Ohtani",
    "Juan Soto"
]

print("  測試 Vector Search...")
for query in test_queries:
    query_vector = model.encode(query)
    results = table.search(query_vector).limit(1).to_list()
    
    if results:
        player = results[0]
        print(f"  ✅ '{query}' → {player['player_name']} ({player['team']}, {player['season']})")
    else:
        print(f"  ❌ '{query}' → 找不到")

# 測試 FTS
print("\n  測試 Full-Text Search...")
for query in test_queries:
    try:
        results = table.search(query, query_type="fts").limit(1).to_list()
        if results:
            player = results[0]
            print(f"  ✅ '{query}' → {player['player_name']} ({player['team']}, {player['season']})")
        else:
            print(f"  ⚠️  '{query}' → FTS 找不到")
    except Exception as e:
        print(f"  ⚠️  '{query}' → FTS 錯誤: {e}")

# ============================================
# 完成
# ============================================
print("\n" + "=" * 80)
print("✨ 向量資料庫重建完成！")
print("=" * 80)
print(f"資料庫位置：./mlb_data/lancedb")
print(f"文檔總數：{len(df)}")
print(f"賽季範圍：{df['season'].min()} - {df['season'].max()}")
print(f"Embedding 維度：{len(df['vector'].iloc[0])}")
print("\n🎯 下一步：")
print("  1. 測試系統：python week2_mlb_assistant.py")
print("  2. 啟動 Demo：streamlit run week2_streamlit_demo.py")
print("  3. 開始 Week 4 功能擴充（獎項、合約數據）")
print("=" * 80)
