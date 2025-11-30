"""
Phase 5: Vector Database 重建
將包含完整 Statcast 數據的球員文檔重新索引到 vector database
"""

import json
import pandas as pd
from typing import List, Dict
import time


def load_enhanced_documents():
    """載入包含 Statcast 的完整球員文檔"""
    
    print("=" * 80)
    print("載入增強球員文檔")
    print("=" * 80)
    
    print("\n載入數據...")
    with open('./mlb_data/week5_mlb_documents_final_enhanced.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"✅ 載入 {len(documents)} 筆記錄")
    
    # 過濾 2025 數據
    print("\n過濾 2025 數據...")
    if isinstance(documents, list):
        original_count = len(documents)
        documents = [doc for doc in documents if doc.get('season', 0) <= 2024]
        filtered_count = len(documents)
    else:
        original_count = len(documents)
        documents = {k: v for k, v in documents.items() if v.get('season', 0) <= 2024}
        filtered_count = len(documents)
    
    removed = original_count - filtered_count
    print(f"   移除 {removed} 筆 2025 記錄")
    print(f"   剩餘 {filtered_count} 筆記錄")
    
    # 統計 Statcast 覆蓋率
    if isinstance(documents, list):
        with_statcast = sum(1 for doc in documents 
                           if 'statcast' in doc and doc['statcast'] 
                           and isinstance(doc['statcast'], dict)
                           and len(doc['statcast']) > 3)
    else:
        with_statcast = sum(1 for doc in documents.values() 
                           if 'statcast' in doc and doc['statcast']
                           and isinstance(doc['statcast'], dict)
                           and len(doc['statcast']) > 3)
    
    print(f"   有完整 Statcast: {with_statcast} ({(with_statcast/len(documents))*100:.1f}%)")
    
    return documents


def generate_text_chunk(doc: Dict) -> str:
    """
    為球員生成完整的文字描述（包含 Statcast）
    
    Args:
        doc: 球員文檔
    
    Returns:
        文字描述
    """
    
    player_name = doc.get('player_name', 'Unknown')
    season = doc.get('season', 0)
    player_type = doc.get('type', 'Unknown')
    
    # 基本信息（重複球員名字以增強匹配權重）
    text_parts = [f"Player: {player_name}"]
    text_parts.append(f"Full Name: {player_name}")  # 重複名字
    text_parts.append(f"Season: {season}")
    text_parts.append(f"Type: {player_type}")
    
    # 打者數據
    if player_type == 'batter':
        # 基礎打擊數據（從 doc 層級，不是 statcast）
        basic_stats = ['PA', 'AB', 'H', '1B', '2B', '3B', 'HR', 'R', 'RBI', 
                       'AVG', 'OBP', 'SLG', 'OPS']
        
        for stat in basic_stats:
            if stat in doc:
                val = doc[stat]
                if stat == 'PA':
                    text_parts.append(f"Plate Appearances: {val}")
                elif stat == 'AB':
                    text_parts.append(f"At Bats: {val}")
                elif stat == 'H':
                    text_parts.append(f"Hits: {val}")
                elif stat == '1B':
                    text_parts.append(f"Singles: {val}")
                elif stat == '2B':
                    text_parts.append(f"Doubles: {val}")
                elif stat == '3B':
                    text_parts.append(f"Triples: {val}")
                elif stat == 'HR':
                    text_parts.append(f"Home Runs: {val}")
                elif stat == 'R':
                    text_parts.append(f"Runs: {val}")
                elif stat == 'RBI':
                    text_parts.append(f"RBI: {val}")
                elif stat == 'AVG':
                    text_parts.append(f"Batting Average: {val}")
                elif stat == 'OBP':
                    text_parts.append(f"On-Base Percentage: {val}")
                elif stat == 'SLG':
                    text_parts.append(f"Slugging Percentage: {val}")
                elif stat == 'OPS':
                    text_parts.append(f"OPS: {val}")
        
        # Statcast 數據
        if 'statcast' in doc and doc['statcast'] and isinstance(doc['statcast'], dict):
            statcast = doc['statcast']
            
            # 跳過只有 note 的空 Statcast
            if len(statcast) <= 3 and 'note' in statcast:
                pass  # 跳過空的 Statcast
            else:
                # Helper function to format percentage
                def format_pct(val):
                    return val * 100 if val < 1 else val
                
                # 擊球質量
                if 'EV' in statcast:
                    text_parts.append(f"Exit Velocity: {statcast['EV']} mph")
                if 'LA' in statcast:
                    text_parts.append(f"Launch Angle: {statcast['LA']} degrees")
                if 'Barrel%' in statcast:
                    text_parts.append(f"Barrel Rate: {format_pct(statcast['Barrel%']):.1f}%")
                if 'HardHit%' in statcast:
                    text_parts.append(f"Hard-Hit Rate: {format_pct(statcast['HardHit%']):.1f}%")
                
                # 擊球分布
                if 'GB%' in statcast:
                    text_parts.append(f"Ground Ball Rate: {format_pct(statcast['GB%']):.1f}%")
                if 'FB%' in statcast:
                    text_parts.append(f"Fly Ball Rate: {format_pct(statcast['FB%']):.1f}%")
                if 'LD%' in statcast:
                    text_parts.append(f"Line Drive Rate: {format_pct(statcast['LD%']):.1f}%")
                
                # 預期數據
                if 'xwOBA' in statcast:
                    text_parts.append(f"Expected wOBA: {statcast['xwOBA']}")
                if 'xBA' in statcast:
                    text_parts.append(f"Expected Batting Average: {statcast['xBA']}")
                if 'xSLG' in statcast:
                    text_parts.append(f"Expected Slugging: {statcast['xSLG']}")
                
                # 紀律性
                if 'K%' in statcast:
                    text_parts.append(f"Strikeout Rate: {format_pct(statcast['K%']):.1f}%")
                if 'BB%' in statcast:
                    text_parts.append(f"Walk Rate: {format_pct(statcast['BB%']):.1f}%")
                if 'O-Swing%' in statcast:
                    text_parts.append(f"Outside Swing Rate: {format_pct(statcast['O-Swing%']):.1f}%")
                if 'Z-Swing%' in statcast:
                    text_parts.append(f"Zone Swing Rate: {format_pct(statcast['Z-Swing%']):.1f}%")
                if 'Whiff%' in statcast:
                    text_parts.append(f"Whiff Rate: {format_pct(statcast['Whiff%']):.1f}%")
                
                # 跑壘
                if 'Sprint Speed' in statcast:
                    text_parts.append(f"Sprint Speed: {statcast['Sprint Speed']} ft/s")
                
                # 進階指標
                if 'wOBA' in statcast:
                    text_parts.append(f"wOBA: {statcast['wOBA']}")
                if 'wRC+' in statcast:
                    text_parts.append(f"wRC+: {statcast['wRC+']:.0f}")
                if 'WAR' in statcast:
                    text_parts.append(f"WAR: {statcast['WAR']:.1f}")
            if 'Whiff%' in statcast:
                text_parts.append(f"Whiff Rate: {statcast['Whiff%']}%")
            
            # 跑壘
            if 'Sprint Speed' in statcast:
                text_parts.append(f"Sprint Speed: {statcast['Sprint Speed']} ft/s")
            
            # 進階指標
            if 'wOBA' in statcast:
                text_parts.append(f"wOBA: {statcast['wOBA']}")
            if 'wRC+' in statcast:
                text_parts.append(f"wRC+: {statcast['wRC+']}")
            if 'WAR' in statcast:
                text_parts.append(f"WAR: {statcast['WAR']}")
    
    # 投手數據
    elif player_type == 'pitcher':
        # 基礎投球數據
        if 'IP' in doc:
            text_parts.append(f"Innings Pitched: {doc['IP']}")
        if 'W' in doc:
            text_parts.append(f"Wins: {doc['W']}")
        if 'L' in doc:
            text_parts.append(f"Losses: {doc['L']}")
        if 'ERA' in doc:
            text_parts.append(f"ERA: {doc['ERA']}")
        if 'WHIP' in doc:
            text_parts.append(f"WHIP: {doc['WHIP']}")
        if 'SO' in doc:
            text_parts.append(f"Strikeouts: {doc['SO']}")
        
        # Statcast 數據
        if 'statcast' in doc and doc['statcast'] and isinstance(doc['statcast'], dict):
            statcast = doc['statcast']
            
            # 跳過只有 note 的空 Statcast
            if len(statcast) <= 3 and 'note' in statcast:
                pass  # 跳過空的 Statcast
            else:
                # Helper function to format percentage
                def format_pct(val):
                    return val * 100 if val < 1 else val
                
                # 球速
                if 'FAv' in statcast:
                    text_parts.append(f"Fastball Velocity: {statcast['FAv']} mph")
                if 'FTv' in statcast:
                    text_parts.append(f"Two-Seam Velocity: {statcast['FTv']} mph")
                if 'SLv' in statcast:
                    text_parts.append(f"Slider Velocity: {statcast['SLv']} mph")
                if 'CUv' in statcast:
                    text_parts.append(f"Curveball Velocity: {statcast['CUv']} mph")
                if 'CHv' in statcast:
                    text_parts.append(f"Changeup Velocity: {statcast['CHv']} mph")
                
                # 球種分布
                if 'FA%' in statcast:
                    text_parts.append(f"Fastball Usage: {format_pct(statcast['FA%']):.1f}%")
                if 'SL%' in statcast:
                    text_parts.append(f"Slider Usage: {format_pct(statcast['SL%']):.1f}%")
                if 'CU%' in statcast:
                    text_parts.append(f"Curveball Usage: {format_pct(statcast['CU%']):.1f}%")
                if 'CH%' in statcast:
                    text_parts.append(f"Changeup Usage: {format_pct(statcast['CH%']):.1f}%")
                
                # 控球
                if 'K%' in statcast:
                    text_parts.append(f"Strikeout Rate: {format_pct(statcast['K%']):.1f}%")
                if 'BB%' in statcast:
                    text_parts.append(f"Walk Rate: {format_pct(statcast['BB%']):.1f}%")
                if 'Whiff%' in statcast:
                    text_parts.append(f"Whiff Rate: {format_pct(statcast['Whiff%']):.1f}%")
                if 'Chase%' in statcast:
                    text_parts.append(f"Chase Rate: {format_pct(statcast['Chase%']):.1f}%")
                if 'CSW%' in statcast:
                    text_parts.append(f"Called Strike + Whiff Rate: {format_pct(statcast['CSW%']):.1f}%")
                
                # 投球質量
                if 'Barrel%' in statcast:
                    text_parts.append(f"Barrel Rate Against: {format_pct(statcast['Barrel%']):.1f}%")
                if 'HardHit%' in statcast:
                    text_parts.append(f"Hard-Hit Rate Against: {format_pct(statcast['HardHit%']):.1f}%")
                if 'EV' in statcast:
                    text_parts.append(f"Exit Velocity Against: {statcast['EV']} mph")
            
            # 預期數據
            if 'xERA' in statcast:
                text_parts.append(f"Expected ERA: {statcast['xERA']}")
            if 'xwOBA' in statcast:
                text_parts.append(f"Expected wOBA Against: {statcast['xwOBA']}")
            
            # 進階指標
            if 'FIP' in statcast:
                text_parts.append(f"FIP: {statcast['FIP']}")
            if 'xFIP' in statcast:
                text_parts.append(f"xFIP: {statcast['xFIP']}")
            if 'SIERA' in statcast:
                text_parts.append(f"SIERA: {statcast['SIERA']}")
            if 'WAR' in statcast:
                text_parts.append(f"WAR: {statcast['WAR']}")
    
    # 獎項
    if 'awards' in doc and doc['awards']:
        awards = doc['awards']
        if awards.get('MVP'):
            text_parts.append(f"MVP: {awards['MVP']}")
        if awards.get('Silver Slugger'):
            text_parts.append(f"Silver Slugger: {awards['Silver Slugger']}")
        if awards.get('Gold Glove'):
            text_parts.append(f"Gold Glove: {awards['Gold Glove']}")
        if awards.get('Cy Young'):
            text_parts.append(f"Cy Young: {awards['Cy Young']}")
    
    # 合約
    if 'contract' in doc and doc['contract']:
        contract = doc['contract']
        if 'current_salary' in contract:
            text_parts.append(f"Salary: ${contract['current_salary']:,}")
        if 'contract_years' in contract:
            text_parts.append(f"Contract Years: {contract['contract_years']}")
    
    # 在結尾重複球員名字以增強匹配
    text_parts.append(f"Player Name: {player_name}")
    
    return ". ".join(text_parts) + "."


def generate_all_text_chunks(documents) -> pd.DataFrame:
    """
    為所有文檔生成文字描述
    
    Args:
        documents: 球員文檔 (list 或 dict)
    
    Returns:
        DataFrame with columns: player_id, text_chunk
    """
    
    print("\n" + "=" * 80)
    print("生成文字描述")
    print("=" * 80)
    
    chunks = []
    
    # 支援 list 和 dict 格式
    if isinstance(documents, list):
        doc_iterator = enumerate(documents)
        total = len(documents)
    else:
        doc_iterator = documents.items()
        total = len(documents)
    
    print(f"\n處理 {total} 個文檔...")
    
    start_time = time.time()
    
    for i, doc_info in enumerate(doc_iterator):
        if isinstance(documents, list):
            idx = doc_info[0]
            doc = doc_info[1]
            # 使用 player_name + season 作為 ID
            player_name = doc.get('player_name', '')
            season = doc.get('season', 0)
            player_id = f"{player_name}_{season}" if player_name and season else str(idx)
        else:
            player_id = doc_info[0]
            doc = doc_info[1]
        
        # 生成文字描述
        text_chunk = generate_text_chunk(doc)
        
        chunks.append({
            'player_id': player_id,
            'text_chunk': text_chunk
        })
        
        # 進度顯示
        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate
            print(f"  進度: {i+1}/{total} ({(i+1)/total*100:.1f}%) - "
                  f"速度: {rate:.1f} docs/s - "
                  f"剩餘時間: {remaining:.0f}s")
    
    elapsed = time.time() - start_time
    print(f"\n✅ 完成！總時間: {elapsed:.1f}s")
    
    df = pd.DataFrame(chunks)
    
    # 統計
    avg_length = df['text_chunk'].str.len().mean()
    print(f"\n文字描述統計:")
    print(f"  總數量: {len(df)}")
    print(f"  平均長度: {avg_length:.0f} 字符")
    
    return df


def save_text_chunks(df: pd.DataFrame):
    """儲存文字描述"""
    
    print("\n" + "=" * 80)
    print("儲存文字描述")
    print("=" * 80)
    
    # 儲存 CSV
    csv_file = './mlb_data/week5_text_chunks_enhanced.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"✅ CSV: {csv_file}")
    
    # 儲存 JSON
    json_file = './mlb_data/week5_text_chunks_enhanced.json'
    chunks_dict = df.set_index('player_id')['text_chunk'].to_dict()
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_dict, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON: {json_file}")


def show_examples(df: pd.DataFrame):
    """顯示範例文字描述"""
    
    print("\n" + "=" * 80)
    print("範例文字描述")
    print("=" * 80)
    
    # 顯示 3 個範例
    for i in range(min(3, len(df))):
        row = df.iloc[i]
        print(f"\n範例 {i+1}:")
        print(f"ID: {row['player_id']}")
        print(f"長度: {len(row['text_chunk'])} 字符")
        print(f"內容預覽:")
        print(row['text_chunk'][:500] + "..." if len(row['text_chunk']) > 500 else row['text_chunk'])


def main():
    """主程式"""
    
    print("=" * 80)
    print("Phase 5: Vector Database 重建 - 步驟 1/3")
    print("=" * 80)
    print("\n生成增強的文字描述（包含 Statcast）")
    
    # 1. 載入文檔
    documents = load_enhanced_documents()
    
    # 2. 生成文字描述
    df = generate_all_text_chunks(documents)
    
    # 3. 儲存
    save_text_chunks(df)
    
    # 4. 顯示範例
    show_examples(df)
    
    print("\n" + "=" * 80)
    print("✨ 步驟 1 完成！")
    print("=" * 80)
    print("\n下一步:")
    print("  python phase5_compute_embeddings.py  # 計算 embeddings")


if __name__ == "__main__":
    main()
