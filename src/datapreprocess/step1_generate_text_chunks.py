"""
Step 1: 生成文本描述 - 修復版本
處理沒有 Season 欄位的情況
"""

import pandas as pd
import json
from pathlib import Path


def generate_text_chunks():
    """生成文本描述"""
    
    print("=" * 80)
    print("Step 1: 生成文本描述")
    print("=" * 80)
    
    batters_csv = './data/raw/statcast_batters_enhanced.csv'
    pitchers_csv = './data/raw/statcast_pitchers_enhanced.csv'
    output_dir = './data/mlb_data'
    
    # 確保輸出目錄存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    text_chunks = {}
    
    # 處理打者數據
    print("\n[1/2] 處理打者數據...")
    
    if Path(batters_csv).exists():
        df = pd.read_csv(batters_csv)
        print(f"✅ 載入打者數據: {len(df)} 筆")
        
        # 檢查欄位
        player_col = 'player_name' if 'player_name' in df.columns else 'Player'
        
        # 檢查賽季欄位（優先使用 year）
        season_col = None
        if 'year' in df.columns:
            season_col = 'year'
        elif 'Year' in df.columns:
            season_col = 'Year'
        elif 'Season' in df.columns:
            season_col = 'Season'
        elif 'season' in df.columns:
            season_col = 'season'
        
        if season_col:
            print(f"✅ 找到賽季欄位: '{season_col}'")
        else:
            print(f"⚠️  沒有找到賽季欄位，將使用 'Unknown' 作為賽季")
            # 嘗試從其他欄位推斷
            # 如果有 team_season 或類似欄位
            for col in df.columns:
                if 'season' in col.lower() or 'year' in col.lower():
                    print(f"   發現可能的賽季欄位: {col}")
        
        # 處理每一筆記錄
        for idx, row in df.iterrows():
            player_name = row[player_col]
            
            # 獲取賽季
            if season_col and not pd.isna(row[season_col]):
                season = int(row[season_col])
            else:
                # 如果沒有賽季，使用索引來區分
                # 假設CSV按賽季排序，或者使用默認值
                season = 2024  # 默認值
            
            # 生成 player_id
            player_id = f"{player_name}_{season}"
            
            # 生成文本描述
            text_parts = [
                f"Player: {player_name}",
                f"Season: {season}",
                "Type: batter"
            ]
            
            # 添加所有可用的統計數據
            for col in df.columns:
                if col not in [player_col, season_col]:
                    value = row[col]
                    if pd.notna(value):
                        text_parts.append(f"{col}: {value}")
            
            text_chunks[player_id] = ". ".join(text_parts) + "."
        
        print(f"✅ 生成打者描述: {len(text_chunks)} 筆")
    
    # 處理投手數據
    print("\n[2/2] 處理投手數據...")
    
    if Path(pitchers_csv).exists():
        df = pd.read_csv(pitchers_csv)
        print(f"✅ 載入投手數據: {len(df)} 筆")
        
        # 使用相同邏輯處理投手
        player_col = 'player_name' if 'player_name' in df.columns else 'Player'
        
        season_col = None
        if 'Season' in df.columns:
            season_col = 'Season'
        elif 'season' in df.columns:
            season_col = 'season'
        elif 'year' in df.columns:
            season_col = 'year'
        elif 'Year' in df.columns:
            season_col = 'Year'
        
        pitcher_count = 0
        for idx, row in df.iterrows():
            player_name = row[player_col]
            
            if season_col and not pd.isna(row[season_col]):
                season = int(row[season_col])
            else:
                season = 2024
            
            player_id = f"{player_name}_{season}"
            
            text_parts = [
                f"Player: {player_name}",
                f"Season: {season}",
                "Type: pitcher"
            ]
            
            for col in df.columns:
                if col not in [player_col, season_col]:
                    value = row[col]
                    if pd.notna(value):
                        text_parts.append(f"{col}: {value}")
            
            text_chunks[player_id] = ". ".join(text_parts) + "."
            pitcher_count += 1
        
        print(f"✅ 生成投手描述: {pitcher_count} 筆")
    
    # 保存
    output_path = Path(output_dir) / 'text_chunks.json'
    
    print(f"\n保存到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(text_chunks, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 成功生成 {len(text_chunks)} 筆文本描述")
    
    # 顯示示例
    print(f"\n示例（前3個）:")
    for i, (player_id, text) in enumerate(list(text_chunks.items())[:3], 1):
        print(f"\n{i}. {player_id}")
        print(f"   {text[:150]}...")
    
    print("\n" + "=" * 80)
    print("Step 1 完成！")
    print("=" * 80)


if __name__ == "__main__":
    generate_text_chunks()
