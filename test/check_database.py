import os
import sys
import json
from pathlib import Path
from collections import Counter

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)


def check_database_fields():
    data_path = Path(project_root) / "data" / "mlb_data_adv" / "training_data.json"
    
    if not data_path.exists():
        print(f"❌ 找不到檔案: {data_path}")
        return
    
    with open(data_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    
    print("=" * 80)
    print(f"資料庫總記錄數: {len(records)}")
    print("=" * 80)
    
    # 統計所有 stats 欄位
    all_fields = Counter()
    batter_fields = Counter()
    pitcher_fields = Counter()
    
    for rec in records:
        stats = rec.get("stats", {})
        ptype = rec.get("type", "unknown")
        
        for field in stats.keys():
            all_fields[field] += 1
            if ptype == "batter":
                batter_fields[field] += 1
            elif ptype == "pitcher":
                pitcher_fields[field] += 1
    
    # 顯示所有欄位
    print("\n【所有 Stats 欄位】（按出現次數排序）")
    print("-" * 80)
    for field, count in all_fields.most_common():
        print(f"{field:20s} : {count:5d} 筆")
    
    # 顯示打者欄位
    print("\n" + "=" * 80)
    print("【打者專屬欄位】")
    print("-" * 80)
    batter_only = set(batter_fields.keys()) - set(pitcher_fields.keys())
    for field in sorted(batter_only):
        print(f"{field:20s} : {batter_fields[field]:5d} 筆")
    
    # 顯示投手欄位
    print("\n" + "=" * 80)
    print("【投手專屬欄位】")
    print("-" * 80)
    pitcher_only = set(pitcher_fields.keys()) - set(batter_fields.keys())
    for field in sorted(pitcher_only):
        print(f"{field:20s} : {pitcher_fields[field]:5d} 筆")
    
    # 顯示共用欄位
    print("\n" + "=" * 80)
    print("【共用欄位】（打者和投手都有）")
    print("-" * 80)
    common = set(batter_fields.keys()) & set(pitcher_fields.keys())
    for field in sorted(common):
        print(f"{field:20s} : 打者 {batter_fields[field]:5d} 筆 | 投手 {pitcher_fields[field]:5d} 筆")
    
    # 範例記錄
    print("\n" + "=" * 80)
    print("【範例記錄】")
    print("-" * 80)
    
    # 打者範例
    for rec in records:
        if rec.get("type") == "batter":
            print(f"\n打者範例：{rec['player_name']} ({rec['season']})")
            print(f"Stats 欄位：{list(rec['stats'].keys())}")
            break
    
    # 投手範例
    for rec in records:
        if rec.get("type") == "pitcher":
            print(f"\n投手範例：{rec['player_name']} ({rec['season']})")
            print(f"Stats 欄位：{list(rec['stats'].keys())}")
            break
    
if __name__ == "__main__":
    check_database_fields()
