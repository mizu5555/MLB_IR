"""
Week 1: MLB 資料收集與處理（完整版）
使用 pybaseball 取得 2023-2024 賽季數據

執行步驟：
1. 取得打者和投手數據
2. 建立 Player ID 映射（解決人名檢索問題）
3. 建立結構化文檔（給 Hybrid Search 用）
4. 儲存為 JSON 格式
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

# 要收集的賽季
SEASONS = [2023, 2024]

print("=" * 80)
print("MLB 資料收集系統 v1.0")
print("=" * 80)
print(f"目標賽季：{SEASONS}")
print(f"輸出目錄：{OUTPUT_DIR}")
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
    print("❌ 請先安裝：pip install pybaseball")
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
        print(f"  ❌ {season} 失敗: {e}")

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
        pitchers = pyb.pitching_stats(season, season, qual=0)
        pitchers['Season'] = season
        
        # 只保留有投球局數的投手
        pitchers = pitchers[pitchers['IP'] > 0]
        
        print(f"  ✅ {season}: {len(pitchers)} 位投手")
        all_pitchers.append(pitchers)
    except Exception as e:
        print(f"  ❌ {season} 失敗: {e}")

if not all_pitchers:
    print("❌ 無法取得任何投手數據")
    exit(1)

# 合併所有賽季
pitchers_df = pd.concat(all_pitchers, ignore_index=True)
print(f"\n✅ 投手數據總計：{len(pitchers_df)} 筆記錄")

# ============================================
# Step 4: 建立 Player ID 映射表
# ============================================
print("\n[Step 4] 建立 Player ID 映射表...")

# 從 pybaseball 取得完整的球員 ID 對照表
print("  正在下載球員 ID 對照表...")
try:
    # 這會取得所有球員的 ID 映射
    # 包含：MLBAM ID, FanGraphs ID, Baseball Reference ID
    player_id_table = pyb.playerid_lookup('', '')  # 空字串會返回所有球員
    print(f"  ✅ 取得 {len(player_id_table)} 位球員的 ID 映射")
    
    # 儲存完整映射表
    player_id_file = os.path.join(OUTPUT_DIR, "player_id_mapping.csv")
    player_id_table.to_csv(player_id_file, index=False)
    print(f"  💾 已儲存：{player_id_file}")
    
except Exception as e:
    print(f"  ⚠️  無法取得完整 ID 映射表: {e}")
    print("  將使用 FanGraphs 的 IDfg 作為 player_id")
    player_id_table = None

# ============================================
# Step 5: 建立檢索文檔
# ============================================
print("\n[Step 5] 建立檢索文檔...")

def create_batter_document(row):
    """將打者數據轉換為檢索文檔"""
    
    # 基本資訊
    player_name = row.get('Name', 'Unknown')
    team = row.get('Team', 'FA')
    season = int(row.get('Season', 2024))
    
    # Player ID（優先使用 FanGraphs ID）
    player_id = str(row.get('IDfg', row.get('playerid', 'unknown')))
    
    # 提取關鍵統計（處理 NaN）
    stats = {
        'PA': int(row.get('PA', 0)) if pd.notna(row.get('PA')) else 0,
        'AB': int(row.get('AB', 0)) if pd.notna(row.get('AB')) else 0,
        'H': int(row.get('H', 0)) if pd.notna(row.get('H')) else 0,
        'HR': int(row.get('HR', 0)) if pd.notna(row.get('HR')) else 0,
        'R': int(row.get('R', 0)) if pd.notna(row.get('R')) else 0,
        'RBI': int(row.get('RBI', 0)) if pd.notna(row.get('RBI')) else 0,
        'SB': int(row.get('SB', 0)) if pd.notna(row.get('SB')) else 0,
        'BB': int(row.get('BB', 0)) if pd.notna(row.get('BB')) else 0,
        'SO': int(row.get('SO', 0)) if pd.notna(row.get('SO')) else 0,
        'AVG': float(row.get('AVG', 0)) if pd.notna(row.get('AVG')) else 0.0,
        'OBP': float(row.get('OBP', 0)) if pd.notna(row.get('OBP')) else 0.0,
        'SLG': float(row.get('SLG', 0)) if pd.notna(row.get('SLG')) else 0.0,
        'OPS': float(row.get('OPS', 0)) if pd.notna(row.get('OPS')) else 0.0,
        'wOBA': float(row.get('wOBA', 0)) if pd.notna(row.get('wOBA')) else 0.0,
        'wRC_plus': float(row.get('wRC+', 0)) if pd.notna(row.get('wRC+')) else 0.0,
        'BB_pct': float(row.get('BB%', 0)) if pd.notna(row.get('BB%')) else 0.0,
        'K_pct': float(row.get('K%', 0)) if pd.notna(row.get('K%')) else 0.0,
        'ISO': float(row.get('ISO', 0)) if pd.notna(row.get('ISO')) else 0.0,
        'BABIP': float(row.get('BABIP', 0)) if pd.notna(row.get('BABIP')) else 0.0,
        'WAR': float(row.get('WAR', 0)) if pd.notna(row.get('WAR')) else 0.0,
    }
    
    # 建立文字描述（給 Vector Embedding 用）
    description = f"{player_name}, batter for {team} in {season} season. "
    description += f"Played {stats['PA']} plate appearances. "
    description += f"Key offensive stats: "
    description += f"wRC+ {stats['wRC_plus']:.1f}, "
    description += f"wOBA {stats['wOBA']:.3f}, "
    description += f"OPS {stats['OPS']:.3f}, "
    description += f"batting average {stats['AVG']:.3f}, "
    description += f"on-base percentage {stats['OBP']:.3f}, "
    description += f"slugging {stats['SLG']:.3f}. "
    description += f"Hit {stats['HR']} home runs, "
    description += f"stole {stats['SB']} bases. "
    description += f"Walk rate {stats['BB_pct']:.1f}%, "
    description += f"strikeout rate {stats['K_pct']:.1f}%. "
    description += f"WAR: {stats['WAR']:.1f}."
    
    return {
        'doc_id': f"batter_{player_id}_{season}",
        'player_id': player_id,
        'player_name': player_name,  # ← 關鍵：獨立欄位給 FTS 用
        'team': team,
        'season': season,
        'position': row.get('Pos', 'Unknown'),
        'age': int(row.get('Age', 0)) if pd.notna(row.get('Age')) else 0,
        'type': 'batter',
        'description': description,  # ← 給 Vector Search 用
        'stats': stats,
        'games': int(row.get('G', 0)) if pd.notna(row.get('G')) else 0,
    }

def create_pitcher_document(row):
    """將投手數據轉換為檢索文檔"""
    
    player_name = row.get('Name', 'Unknown')
    team = row.get('Team', 'FA')
    season = int(row.get('Season', 2024))
    player_id = str(row.get('IDfg', row.get('playerid', 'unknown')))
    
    stats = {
        'IP': float(row.get('IP', 0)) if pd.notna(row.get('IP')) else 0.0,
        'W': int(row.get('W', 0)) if pd.notna(row.get('W')) else 0,
        'L': int(row.get('L', 0)) if pd.notna(row.get('L')) else 0,
        'SV': int(row.get('SV', 0)) if pd.notna(row.get('SV')) else 0,
        'ERA': float(row.get('ERA', 0)) if pd.notna(row.get('ERA')) else 0.0,
        'WHIP': float(row.get('WHIP', 0)) if pd.notna(row.get('WHIP')) else 0.0,
        'FIP': float(row.get('FIP', 0)) if pd.notna(row.get('FIP')) else 0.0,
        'xFIP': float(row.get('xFIP', 0)) if pd.notna(row.get('xFIP')) else 0.0,
        'K_9': float(row.get('K/9', 0)) if pd.notna(row.get('K/9')) else 0.0,
        'BB_9': float(row.get('BB/9', 0)) if pd.notna(row.get('BB/9')) else 0.0,
        'K_pct': float(row.get('K%', 0)) if pd.notna(row.get('K%')) else 0.0,
        'BB_pct': float(row.get('BB%', 0)) if pd.notna(row.get('BB%')) else 0.0,
        'HR_9': float(row.get('HR/9', 0)) if pd.notna(row.get('HR/9')) else 0.0,
        'LOB_pct': float(row.get('LOB%', 0)) if pd.notna(row.get('LOB%')) else 0.0,
        'GB_pct': float(row.get('GB%', 0)) if pd.notna(row.get('GB%')) else 0.0,
        'WAR': float(row.get('WAR', 0)) if pd.notna(row.get('WAR')) else 0.0,
    }
    
    description = f"{player_name}, pitcher for {team} in {season} season. "
    description += f"Pitched {stats['IP']:.1f} innings. "
    description += f"Key pitching stats: "
    description += f"ERA {stats['ERA']:.2f}, "
    description += f"WHIP {stats['WHIP']:.2f}, "
    description += f"FIP {stats['FIP']:.2f}. "
    description += f"Strikeout rate {stats['K_9']:.1f} per 9 innings, "
    description += f"walk rate {stats['BB_9']:.1f} per 9 innings. "
    description += f"K% {stats['K_pct']:.1f}%, "
    description += f"BB% {stats['BB_pct']:.1f}%. "
    description += f"Record {stats['W']}-{stats['L']}, "
    description += f"{stats['SV']} saves. "
    description += f"WAR: {stats['WAR']:.1f}."
    
    return {
        'doc_id': f"pitcher_{player_id}_{season}",
        'player_id': player_id,
        'player_name': player_name,
        'team': team,
        'season': season,
        'position': 'Pitcher',
        'age': int(row.get('Age', 0)) if pd.notna(row.get('Age')) else 0,
        'type': 'pitcher',
        'description': description,
        'stats': stats,
        'games': int(row.get('G', 0)) if pd.notna(row.get('G')) else 0,
    }

# 建立所有文檔
print("  正在建立打者文檔...")
batter_docs = [create_batter_document(row) for _, row in batters_df.iterrows()]
print(f"  ✅ {len(batter_docs)} 個打者文檔")

print("  正在建立投手文檔...")
pitcher_docs = [create_pitcher_document(row) for _, row in pitchers_df.iterrows()]
print(f"  ✅ {len(pitcher_docs)} 個投手文檔")

all_documents = batter_docs + pitcher_docs
print(f"\n✅ 總計：{len(all_documents)} 個文檔")

# ============================================
# Step 6: 儲存文檔
# ============================================
print("\n[Step 6] 儲存文檔...")

# 儲存為 JSON
docs_file = os.path.join(OUTPUT_DIR, "mlb_documents.json")
with open(docs_file, 'w', encoding='utf-8') as f:
    json.dump(all_documents, f, ensure_ascii=False, indent=2)
print(f"  💾 已儲存：{docs_file}")

# 另外儲存為 CSV（方便檢視）
docs_df = pd.DataFrame(all_documents)
csv_file = os.path.join(OUTPUT_DIR, "mlb_documents.csv")
docs_df.to_csv(csv_file, index=False)
print(f"  💾 已儲存：{csv_file}")

# 儲存原始數據
batters_raw_file = os.path.join(OUTPUT_DIR, "batters_raw.csv")
batters_df.to_csv(batters_raw_file, index=False)
print(f"  💾 已儲存：{batters_raw_file}")

pitchers_raw_file = os.path.join(OUTPUT_DIR, "pitchers_raw.csv")
pitchers_df.to_csv(pitchers_raw_file, index=False)
print(f"  💾 已儲存：{pitchers_raw_file}")

# ============================================
# Step 7: 生成統計報告
# ============================================
print("\n[Step 7] 生成統計報告...")

report = {
    'generated_at': datetime.now().isoformat(),
    'seasons': SEASONS,
    'total_documents': len(all_documents),
    'batters': len(batter_docs),
    'pitchers': len(pitcher_docs),
    'teams': list(docs_df['team'].unique()),
    'sample_document': all_documents[0] if all_documents else None,
}

report_file = os.path.join(OUTPUT_DIR, "data_report.json")
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"  💾 已儲存：{report_file}")

# ============================================
# 完成
# ============================================
print("\n" + "=" * 80)
print("✨ 資料收集完成！")
print("=" * 80)
print(f"📊 統計摘要：")
print(f"   - 賽季：{SEASONS}")
print(f"   - 打者記錄：{len(batter_docs)}")
print(f"   - 投手記錄：{len(pitcher_docs)}")
print(f"   - 總文檔數：{len(all_documents)}")
print(f"   - 球隊數：{len(docs_df['team'].unique())}")
print(f"\n📁 輸出檔案：")
print(f"   - {docs_file}")
print(f"   - {csv_file}")
print(f"   - {batters_raw_file}")
print(f"   - {pitchers_raw_file}")
if player_id_table is not None:
    print(f"   - {player_id_file}")
print(f"   - {report_file}")

print(f"\n🎯 下一步：執行 week1_build_hybrid_search.py 建立 Hybrid Search 系統")
print("=" * 80)