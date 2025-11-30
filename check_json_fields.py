"""
簡單檢查 Statcast JSON 的欄位名稱
"""

import json

print("=" * 80)
print("檢查 Statcast JSON 欄位")
print("=" * 80)

# 載入 Statcast JSON
print("\n載入 Statcast 數據...")
try:
    with open('./mlb_data/week5_statcast_enhanced.json', 'r', encoding='utf-8') as f:
        statcast_data = json.load(f)
    print(f"✅ 載入 {len(statcast_data)} 筆記錄")
except FileNotFoundError:
    print("❌ 文件未找到")
    exit(1)

# 找一個打者範例
print("\n尋找打者範例...")
batter_sample = None
for key, data in statcast_data.items():
    if data.get('type') == 'batter' and 'Aaron Judge' in data.get('player_name', ''):
        batter_sample = data
        print(f"✅ 找到: {data['player_name']} ({data['year']})")
        break

if batter_sample:
    print("\n打者欄位:")
    print("-" * 80)
    
    # 顯示所有欄位
    for key, val in list(batter_sample.items())[:30]:
        if key not in ['player_name', 'year', 'type']:
            val_str = f"{val:.3f}" if isinstance(val, float) else str(val)
            print(f"  {key:25s} = {val_str}")
    
    # 檢查關鍵的百分比欄位
    print("\n關鍵百分比欄位:")
    percent_fields = ['Barrel%', 'HardHit%', 'Hard%', 'K%', 'BB%']
    for field in percent_fields:
        if field in batter_sample:
            val = batter_sample[field]
            print(f"  {field:15s} = {val}")

# 找一個投手範例
print("\n" + "=" * 80)
print("尋找投手範例...")
pitcher_sample = None
for key, data in statcast_data.items():
    if data.get('type') == 'pitcher' and 'Gerrit Cole' in data.get('player_name', ''):
        pitcher_sample = data
        print(f"✅ 找到: {data['player_name']} ({data['year']})")
        break

if pitcher_sample:
    print("\n投手欄位:")
    print("-" * 80)
    
    # 顯示部分欄位
    for key, val in list(pitcher_sample.items())[:30]:
        if key not in ['player_name', 'year', 'type']:
            val_str = f"{val:.3f}" if isinstance(val, float) else str(val)
            print(f"  {key:25s} = {val_str}")

print("\n" + "=" * 80)
print("完成")
print("=" * 80)
