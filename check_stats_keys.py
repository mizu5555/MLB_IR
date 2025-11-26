"""
檢查 stats 字典中的實際鍵名
"""

import json

print("=" * 80)
print("檢查 stats 鍵名")
print("=" * 80)

# 載入數據
with open('./mlb_data/mlb_players_2022_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 找一個 2023 年的打者
print("\n尋找 2023 年的打者...")
batter_2023 = None
for doc in data:
    if doc['type'] == 'batter' and doc['season'] == 2023:
        batter_2023 = doc
        break

if batter_2023:
    print(f"✅ 找到：{batter_2023['player_name']} ({batter_2023['team']}, {batter_2023['season']})")
    
    print("\n[檢查 1] stats 類型：")
    print(f"  類型：{type(batter_2023['stats'])}")
    
    if isinstance(batter_2023['stats'], dict):
        print("\n[檢查 2] stats 所有鍵名（前 30 個）：")
        keys = list(batter_2023['stats'].keys())
        for i, key in enumerate(keys[:30], 1):
            value = batter_2023['stats'][key]
            print(f"  {i:2d}. '{key}' = {value}")
        
        print(f"\n  總共 {len(keys)} 個鍵")
        
        # 尋找 wRC 相關的鍵
        print("\n[檢查 3] 尋找 wRC 相關的鍵：")
        wrc_keys = [k for k in keys if 'wrc' in k.lower() or 'wRC' in k]
        if wrc_keys:
            for key in wrc_keys:
                print(f"  ✅ 找到：'{key}' = {batter_2023['stats'][key]}")
        else:
            print("  ❌ 找不到任何 wRC 相關的鍵")
        
        # 尋找其他關鍵統計
        print("\n[檢查 4] 其他關鍵統計：")
        key_stats = ['HR', 'AVG', 'OPS', 'PA', 'AB', 'wOBA']
        for stat in key_stats:
            if stat in batter_2023['stats']:
                print(f"  ✅ '{stat}' = {batter_2023['stats'][stat]}")
            else:
                # 嘗試其他可能的名稱
                alternatives = [stat.lower(), stat.upper(), f"stat_{stat}"]
                found = False
                for alt in alternatives:
                    if alt in batter_2023['stats']:
                        print(f"  ✅ '{stat}' (as '{alt}') = {batter_2023['stats'][alt]}")
                        found = True
                        break
                if not found:
                    print(f"  ❌ '{stat}' 找不到")
    else:
        print(f"  ❌ stats 不是字典！類型：{type(batter_2023['stats'])}")
        print(f"  內容：{batter_2023['stats']}")
else:
    print("❌ 找不到 2023 年的打者！")

print("\n" + "=" * 80)
print("檢查完成")
print("=" * 80)
