"""
Step 1: 生成文本描述 (雙模式版)
功能: 支援從 CSV (raw) 或 JSON (raw_adv) 生成文本塊
"""

import pandas as pd
import json
import os
from pathlib import Path

# === 設定區 ===
BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / 'data' / 'mlb_data_adv'   # 最終輸出資料夾

def get_column_mapping(player_type):
    base_mapping = {
        'player_name': 'Player Name', 'Team': 'Team', 'year': 'Season', 'WAR': 'WAR',
        'player_id': 'Player ID', 'Age': 'Age', 'Season': 'Season'
    }
    
    if player_type == 'batter':
        return {
            **base_mapping,
            'PA': 'Plate Appearances', 'AB': 'At Bats', 'H': 'Hits',
            'HR': 'Home Runs', 'R': 'Runs', 'RBI': 'Runs Batted In',
            'AVG': 'Batting Average', 'OBP': 'On-Base Percentage', 'SLG': 'Slugging Percentage', 'OPS': 'On-Base Plus Slugging',
            'wOBA': 'wOBA', 'wRC+': 'wRC+', 
            'EV': 'Exit Velocity', 'LA': 'Launch Angle', 'Barrel%': 'Barrel Rate', 'HardHit%': 'Hard-Hit Rate',
            'BB%': 'Walk Rate', 'K%': 'Strikeout Rate', 'Spd': 'Speed Score', 'WPA': 'Win Probability Added',
            'Clutch': 'Clutch Score', 'CSW%': 'CSW%',
        }
    else: # pitcher
        return {
            **base_mapping,
            'W': 'Wins', 'L': 'Losses', 'SV': 'Saves', 'IP': 'Innings Pitched',
            'G': 'Games Played', 'GS': 'Games Started',
            'ERA': 'ERA', 'WHIP': 'WHIP', 'SO': 'Strikeouts', 
            'K%': 'Strikeout Rate', 'BB%': 'Walk Rate',
            'HR': 'Home Runs Allowed', 'FIP': 'FIP', 'xFIP': 'xFIP', 'SIERA': 'SIERA',
            'EV': 'Avg Exit Velocity Against', 'Barrel%': 'Barrel Rate Against', 'HardHit%': 'Hard-Hit Rate Against',
            'CSW%': 'CSW%', 'Stuff+': 'Stuff+', 'Location+': 'Location+',
        }

def format_value(value):
    if pd.isna(value) or value == "": return None
    if isinstance(value, float):
        if value.is_integer(): return int(value)
        return round(value, 3)
    return value

def generate_text_line(data_dict, mapping_dict, exclude_keys, is_secondary=False):
    text_parts = []
    
    if not is_secondary:
        if 'year' in data_dict:
            text_parts.append(f"Season: {data_dict['year']}")
        if 'player_name' in data_dict:
            text_parts.append(f"Player: {data_dict['player_name']}")
    
    if 'type' in data_dict:
        text_parts.append(f"Type: {data_dict['type']}")
        
    for key, val in data_dict.items():
        if key in exclude_keys: continue
        
        formatted_val = format_value(val)
        if formatted_val is None: continue
        
        friendly_name = mapping_dict.get(key, key)
        
        val_str = ""
        if 'Velocity' in friendly_name and 'Rate' not in friendly_name and 'Against' not in friendly_name:
            val_str = f"{formatted_val} mph"
        elif 'Angle' in friendly_name:
            val_str = f"{formatted_val} degrees"
        elif '%' in key or 'Rate' in friendly_name or 'Percentage' in friendly_name:
            try:
                if isinstance(formatted_val, (int, float)) and -1.0 <= formatted_val <= 1.0 and formatted_val != 0:
                    val_str = f"{formatted_val * 100:.1f}%"
                else:
                    val_str = f"{formatted_val}%" if '%' in key else f"{formatted_val}"
            except:
                val_str = f"{formatted_val}"
        else:
            val_str = f"{formatted_val}"
            
        text_parts.append(f"{friendly_name}: {val_str}")
            
    return "; ".join(text_parts) + "."

def process_from_json(target_dir):
    """從指定的資料夾讀取 JSON"""
    print(f"正在讀取 JSON，來源: {target_dir}")
    
    json_path = target_dir / 'statcast_enhanced.json'
    text_chunks = {}
    
    if not json_path.exists():
        print(f"找不到 JSON 檔案: {json_path}")
        return {}
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"  ✅ 載入 JSON: {len(data)} 筆記錄")
    
    exclude_base = ['player_name', 'year', 'type', 'player_id', 'Season']
    
    for key, item in data.items():
        p_name = item.get('player_name', 'Unknown')
        p_id = str(item.get('player_id', '0'))
        season = item.get('year', 2024)
        p_type = item.get('type', 'batter')
        
        unique_key = f"{p_name}_{p_id}_{season}"
        mapping = get_column_mapping(p_type)
        
        if unique_key in text_chunks:
            # 二刀流合併
            full_text = generate_text_line(item, mapping, exclude_base, is_secondary=True)
            text_chunks[unique_key] += " ||| " + full_text
        else:
            full_text = generate_text_line(item, mapping, exclude_base, is_secondary=False)
            text_chunks[unique_key] = full_text
            
    return text_chunks

def process_from_csv(target_dir):
    """從指定的資料夾讀取 CSV"""
    print(f"📂 正在讀取 CSV，來源: {target_dir}")
    
    batters_csv = target_dir / 'statcast_batters_enhanced.csv'
    pitchers_csv = target_dir / 'statcast_pitchers_enhanced.csv'
    text_chunks = {}

    def process_file(csv_path, player_type):
        if not csv_path.exists():
            print(f"  ❌ 找不到檔案: {csv_path}")
            return
            
        df = pd.read_csv(csv_path)
        print(f"  ✅ 載入 {player_type}: {len(df)} 筆")
        
        if 'player_id' in df.columns:
            id_col = 'player_id'
        elif 'IDfg' in df.columns:
            id_col = 'IDfg'
        else:
            id_col = None

        mapping = get_column_mapping(player_type)
        
        player_col = 'player_name' if 'player_name' in df.columns else 'Player'
        season_col = 'year'
        
        exclude_keys = [player_col, season_col, 'type', 'player_id', 'IDfg', 'Season']
        if id_col: exclude_keys.append(id_col)
        
        for _, row in df.iterrows():
            p_name = row.get(player_col, 'Unknown')
            season = row.get(season_col, 2024)
            
            # ID 處理
            if id_col and pd.notna(row[id_col]):
                p_id = str(row[id_col]).replace('.0', '')
            else:
                p_id = '0' # 如果是舊版 raw，ID 就會是 0
            
            unique_key = f"{p_name}_{p_id}_{season}"
            
            data_dict = row.to_dict()
            data_dict['year'] = season
            data_dict['player_name'] = p_name
            data_dict['type'] = player_type
            
            if unique_key in text_chunks:
                full_text = generate_text_line(data_dict, mapping, exclude_keys, is_secondary=True)
                text_chunks[unique_key] += " ||| " + full_text
            else:
                full_text = generate_text_line(data_dict, mapping, exclude_keys, is_secondary=False)
                text_chunks[unique_key] = full_text

    process_file(batters_csv, 'batter')
    process_file(pitchers_csv, 'pitcher')
    return text_chunks

def main():
    print("=" * 80)
    print("Step 1: 生成文本描述 (Rebuild Data Final)")
    print("=" * 80)
    
    # 1. 選擇資料夾
    print("\n[Step 1] 請選擇資料來源資料夾:")
    print("  1. raw      (舊版資料，無 ID)")
    print("  2. raw_adv  (新版資料，有 ID)")
    dir_choice = input("  請輸入選項 (預設 2): ").strip()
    
    if dir_choice == "1":
        target_dir = BASE_DIR / 'data' / 'raw'
    else:
        target_dir = BASE_DIR / 'data' / 'raw_adv'
        
    print(f"已選擇路徑: {target_dir}")

    # 2. 選擇格式
    print("\n[Step 2] 請選擇讀取格式:")
    print("  1. csv")
    print("  2. json")
    fmt_choice = input("  請輸入選項 (預設 2): ").strip()
    
    text_chunks = {}
    if fmt_choice == "1":
        text_chunks = process_from_csv(target_dir)
    else:
        text_chunks = process_from_json(target_dir)
        
    # 儲存結果
    if text_chunks:
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / 'text_chunks.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(text_chunks, f, ensure_ascii=False, indent=2)
            
        print(f"\n✅ 保存完成: {len(text_chunks)} 筆球員資料")
        print(f"   輸出位置: {output_path}")
    else:
        print("\n⚠️ 沒有生成任何資料")
if __name__ == "__main__":
    main()