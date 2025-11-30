"""
Week 5: 替代方案 - 從現有數據建立映射表

由於 pybaseball Lahman 模組下載失敗，我們使用現有數據建立映射表
"""

import json
import re
from typing import Dict


def generate_player_id(player_name: str) -> str:
    """
    根據球員名字生成 playerID
    
    規則：姓氏前5字母 + 名字前2字母 + 01
    例如：Aaron Judge -> judgaa01
    
    Args:
        player_name: 球員名字 (e.g., "Aaron Judge")
    
    Returns:
        playerID (e.g., "judgaa01")
    """
    
    # 分割名字
    parts = player_name.strip().split()
    
    if len(parts) < 2:
        # 只有一個名字，使用全名
        name_part = re.sub(r'[^a-zA-Z]', '', parts[0].lower())
        return name_part[:8] + "01"
    
    # 名 + 姓
    first_name = parts[0]
    last_name = parts[-1]  # 取最後一部分作為姓氏
    
    # 移除特殊字符
    first_clean = re.sub(r'[^a-zA-Z]', '', first_name.lower())
    last_clean = re.sub(r'[^a-zA-Z]', '', last_name.lower())
    
    # 組合：姓氏前5字母 + 名字前2字母 + 01
    player_id = last_clean[:5] + first_clean[:2] + "01"
    
    return player_id


def build_mapping_from_documents(documents_path: str) -> Dict:
    """
    從現有球員文檔建立映射表
    
    Args:
        documents_path: 球員文檔路徑
    
    Returns:
        {
            'id_to_name': {...},
            'name_to_id': {...}
        }
    """
    
    print("=" * 80)
    print("從現有數據建立 playerID 映射表")
    print("=" * 80)
    
    try:
        # 載入現有文檔
        with open(documents_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        print(f"\n✅ 載入 {len(documents)} 筆球員文檔")
        
        # 建立映射
        id_to_name = {}
        name_to_id = {}
        
        # 收集所有獨特的球員名字
        unique_players = set()
        for doc in documents:
            player_name = doc['player_name']
            unique_players.add(player_name)
        
        print(f"✅ 找到 {len(unique_players)} 位獨特球員")
        
        # 為每位球員生成 playerID
        for player_name in sorted(unique_players):
            player_id = generate_player_id(player_name)
            
            # 處理重複的 ID（罕見情況）
            original_id = player_id
            counter = 1
            while player_id in id_to_name:
                counter += 1
                player_id = original_id[:-2] + f"{counter:02d}"
            
            id_to_name[player_id] = player_name
            name_to_id[player_name] = player_id
        
        print(f"✅ 映射表建立完成: {len(id_to_name)} 位球員")
        
        # 儲存映射表
        mapping = {
            'id_to_name': id_to_name,
            'name_to_id': name_to_id,
            'note': '從現有球員數據生成的映射表'
        }
        
        output_file = "./mlb_data/week5_player_mapping.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 映射表已儲存: {output_file}")
        
        # 顯示樣本
        print("\n[映射樣本]")
        sample_players = list(name_to_id.items())[:10]
        for player_name, player_id in sample_players:
            print(f"  {player_name:30s} → {player_id}")
        
        return mapping
        
    except Exception as e:
        print(f"❌ 映射表建立失敗: {e}")
        return {'id_to_name': {}, 'name_to_id': {}}


def test_mapping():
    """測試映射生成"""
    
    print("\n" + "=" * 80)
    print("測試 playerID 生成")
    print("=" * 80)
    
    test_cases = [
        "Aaron Judge",
        "Shohei Ohtani",
        "Mike Trout",
        "Ronald Acuna Jr.",
        "Mookie Betts",
        "Juan Soto"
    ]
    
    for name in test_cases:
        player_id = generate_player_id(name)
        print(f"{name:20s} → {player_id}")


if __name__ == "__main__":
    
    # 測試 playerID 生成
    test_mapping()
    
    # 從現有文檔建立映射表
    documents_path = "./mlb_data/mlb_documents.json"
    mapping = build_mapping_from_documents(documents_path)
    
    print("\n" + "=" * 80)
    print("✨ 映射表建立完成")
    print("=" * 80)
    print("\n下一步：執行 week5_data_collection_alternative.py")
