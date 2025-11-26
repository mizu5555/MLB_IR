"""
Week 4: MLB 資料收集（擴充版）
擴充數據範圍：2022-2025 賽季

改動說明：
- 從 2023-2024 擴充到 2022-2025
- 資料量預估：3000+ → 6000-8000 筆
- 其他邏輯保持不變（系統已支援多年份）
"""

import pandas as pd
import json
import os
from datetime import datetime

# ============================================
# 配置
# ============================================
OUTPUT_DIR = "./mlb_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 要收集的賽季（擴充版）
SEASONS = [2022, 2023, 2024, 2025]  # ← 主要改動

print("=" * 80)
print("MLB 資料收集系統 v2.0 (Week 4 擴充版)")
print("=" * 80)
print(f"目標賽季：{SEASONS}")
print(f"輸出目錄：{OUTPUT_DIR}")
print(f"預估資料量：6000-8000 筆")
print()

# ============================================
# Step 1: 安裝和導入 pybaseball
# ============================================
print("[Step 1] 導入 pybaseball...")
try:
    import pybaseball as pyb
    pyb.cache.enable()  # 啟用快取
    print("✅ pybaseball 已就緒")
except ImportError:
    print("❌ 請先安裝：pip install pybaseball --break-system-packages")
    exit(1)

# ============================================
# Step 2: 取得打者數據
# ============================================
print("\n[Step 2] 取得打者數據...")
all_batters = []

for season in SEASONS:
    print(f"  正在取得 {season} 賽季打者數據...")
    try:
        # qual=0 取得所有球員，不設門檻
        batters = pyb.batting_stats(season, season, qual=0)
        batters['Season'] = season
        
        # 只保留有打席的球員
        batters = batters[batters['PA'] > 0]
        
        print(f"  ✅ {season}: {len(batters)} 位打者")
        all_batters.append(batters)
    except Exception as e:
        print(f"  ⚠️  {season} 失敗: {e}")
        print(f"      （如果是 2025，可能賽季尚未開始或數據未完整）")

if not all_batters:
    print("❌ 無法取得任何打者數據")
    exit(1)

# 合併所有賽季
batters_df = pd.concat(all_batters, ignore_index=True)
print(f"\n✅ 打者數據總計：{len(batters_df)} 筆記錄")

# ============================================
# Step 3: 取得投手數據
# ============================================
print("\n[Step 3] 取得投手數據...")
all_pitchers = []

for season in SEASONS:
    print(f"  正在取得 {season} 賽季投手數據...")
    try:
        # qual=0 取得所有投手
        pitchers = pyb.pitching_stats(season, season, qual=0)
        pitchers['Season'] = season
        
        # 只保留有投球的投手
        pitchers = pitchers[pitchers['IP'] > 0]
        
        print(f"  ✅ {season}: {len(pitchers)} 位投手")
        all_pitchers.append(pitchers)
    except Exception as e:
        print(f"  ⚠️  {season} 失敗: {e}")
        print(f"      （如果是 2025，可能賽季尚未開始或數據未完整）")

if not all_pitchers:
    print("❌ 無法取得任何投手數據")
    exit(1)

# 合併所有賽季
pitchers_df = pd.concat(all_pitchers, ignore_index=True)
print(f"\n✅ 投手數據總計：{len(pitchers_df)} 筆記錄")

# ============================================
# Step 4: 數據清理與標準化
# ============================================
print("\n[Step 4] 數據清理與標準化...")

def standardize_dataframe(df, player_type):
    """標準化欄位名稱和數據類型"""
    
    # 標準化欄位名稱
    df = df.rename(columns={
        'Name': 'player_name',
        'Season': 'season',
        'Team': 'team',
        'Age': 'age'
    })
    
    # 確保必要欄位存在
    required_cols = ['player_name', 'season', 'team']
    for col in required_cols:
        if col not in df.columns:
            print(f"  ⚠️  缺少必要欄位：{col}")
            df[col] = None
    
    # 填充缺失值
    df = df.fillna(0)
    
    # 加入球員類型
    df['type'] = player_type
    
    return df

batters_df = standardize_dataframe(batters_df, 'batter')
pitchers_df = standardize_dataframe(pitchers_df, 'pitcher')

print("✅ 數據標準化完成")

# ============================================
# Step 5: 建立結構化文檔
# ============================================
print("\n[Step 5] 建立結構化文檔...")

def create_document(row, player_type):
    """建立單一球員文檔"""
    
    # 基本資訊
    doc = {
        'player_name': str(row.get('player_name', 'Unknown')),
        'season': int(row.get('season', 0)),
        'team': str(row.get('team', 'Unknown')),
        'age': int(row.get('age', 0)) if pd.notna(row.get('age')) else 0,
        'type': player_type
    }
    
    # 守備位置（打者專用）
    if player_type == 'batter':
        # pybaseball 可能沒有位置欄位，需要另外處理
        doc['position'] = str(row.get('Pos', 'N/A'))
    else:
        doc['position'] = 'P'
    
    # 統計數據
    stats = {}
    for col, value in row.items():
        # 跳過已處理的欄位
        if col in ['player_name', 'season', 'team', 'age', 'type', 'position', 'Pos', 'Name', 'Team', 'Age', 'Season']:
            continue
        
        # 只保留數值欄位
        if pd.api.types.is_numeric_dtype(type(value)):
            try:
                stats[col] = float(value) if pd.notna(value) else 0.0
            except:
                stats[col] = 0.0
    
    doc['stats'] = stats
    
    # 建立文字描述（給 Vector Search 用）
    if player_type == 'batter':
        text = f"{doc['player_name']} ({doc['team']}, {doc['season']}) - Batter"
        if 'HR' in stats:
            text += f", HR: {stats['HR']}"
        if 'AVG' in stats:
            text += f", AVG: {stats['AVG']:.3f}"
        if 'OPS' in stats:
            text += f", OPS: {stats['OPS']:.3f}"
    else:
        text = f"{doc['player_name']} ({doc['team']}, {doc['season']}) - Pitcher"
        if 'ERA' in stats:
            text += f", ERA: {stats['ERA']:.2f}"
        if 'WHIP' in stats:
            text += f", WHIP: {stats['WHIP']:.2f}"
        if 'SO' in stats:
            text += f", SO: {stats['SO']}"
    
    doc['text'] = text
    
    return doc

# 建立所有文檔
documents = []

# 打者文檔
for idx, row in batters_df.iterrows():
    doc = create_document(row, 'batter')
    documents.append(doc)

# 投手文檔
for idx, row in pitchers_df.iterrows():
    doc = create_document(row, 'pitcher')
    documents.append(doc)

print(f"✅ 建立文檔完成：{len(documents)} 筆")

# 依賽季統計
season_counts = {}
for doc in documents:
    season = doc['season']
    season_counts[season] = season_counts.get(season, 0) + 1

print("\n📊 各賽季統計：")
for season in sorted(season_counts.keys()):
    print(f"  {season}: {season_counts[season]} 筆")

# ============================================
# Step 6: 儲存為 JSON
# ============================================
print("\n[Step 6] 儲存數據...")

output_file = os.path.join(OUTPUT_DIR, "mlb_players_2022_2025.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)

print(f"✅ 數據已儲存：{output_file}")

# 儲存元數據
metadata = {
    'version': '2.0',
    'created_at': datetime.now().isoformat(),
    'seasons': SEASONS,
    'total_documents': len(documents),
    'season_counts': season_counts,
    'batters': len(batters_df),
    'pitchers': len(pitchers_df)
}

metadata_file = os.path.join(OUTPUT_DIR, "metadata_2022_2025.json")
with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"✅ 元數據已儲存：{metadata_file}")

# ============================================
# 完成
# ============================================
print("\n" + "=" * 80)
print("✨ 數據收集完成！")
print("=" * 80)
print(f"總計：{len(documents)} 筆文檔")
print(f"賽季範圍：{min(SEASONS)} - {max(SEASONS)}")
print(f"打者：{len(batters_df)} 筆")
print(f"投手：{len(pitchers_df)} 筆")
print("\n🎯 下一步：執行 week4_build_vector_db.py 建立向量資料庫")
print("=" * 80)
