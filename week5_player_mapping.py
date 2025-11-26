"""
Week 5: playerID 映射系統

問題：Lahman 使用 playerID (judgeaa01)，我們使用名字 (Aaron Judge)
解決：建立雙向映射表
"""

import pandas as pd
import json
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

try:
    from pybaseball.lahman import people
    print("✅ pybaseball 已載入")
except ImportError:
    print("❌ 請先安裝 pybaseball: pip install pybaseball")
    exit(1)


def create_player_mapping() -> Dict:
    """
    建立 playerID <-> 球員名字映射表
    
    Returns:
        {
            'id_to_name': {'judgeaa01': 'Aaron Judge', ...},
            'name_to_id': {'Aaron Judge': 'judgeaa01', ...}
        }
    """
    
    print("=" * 80)
    print("建立 playerID 映射表")
    print("=" * 80)
    
    try:
        # 下載球員基本資料
        print("正在下載球員資料...")
        people_df = people()
        
        print(f"✅ 成功下載 {len(people_df)} 位球員資料")
        
        # 建立映射
        id_to_name = {}
        name_to_id = {}
        
        for _, row in people_df.iterrows():
            player_id = row['playerID']
            
            # 組合名字：名 + 姓
            first_name = row.get('nameFirst', '')
            last_name = row.get('nameLast', '')
            full_name = f"{first_name} {last_name}".strip()
            
            if full_name:
                id_to_name[player_id] = full_name
                name_to_id[full_name] = player_id
        
        print(f"✅ 映射表建立完成: {len(id_to_name)} 位球員")
        
        # 儲存映射表
        mapping = {
            'id_to_name': id_to_name,
            'name_to_id': name_to_id
        }
        
        output_file = "./mlb_data/week5_player_mapping.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 映射表已儲存: {output_file}")
        
        # 顯示樣本
        print("\n[映射樣本]")
        sample_ids = list(id_to_name.items())[:5]
        for player_id, name in sample_ids:
            print(f"  {player_id} → {name}")
        
        return mapping
        
    except Exception as e:
        print(f"❌ 映射表建立失敗: {e}")
        return {'id_to_name': {}, 'name_to_id': {}}


def load_player_mapping() -> Dict:
    """載入已存在的映射表"""
    
    try:
        with open("./mlb_data/week5_player_mapping.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  映射表不存在，建立新的...")
        return create_player_mapping()


def find_player_name(player_id: str, mapping: Dict) -> str:
    """
    根據 playerID 查找球員名字
    
    Args:
        player_id: Lahman playerID (e.g., 'judgeaa01')
        mapping: 映射表
    
    Returns:
        球員名字 (e.g., 'Aaron Judge')
    """
    return mapping['id_to_name'].get(player_id, player_id)


def find_player_id(player_name: str, mapping: Dict) -> str:
    """
    根據球員名字查找 playerID
    
    Args:
        player_name: 球員名字 (e.g., 'Aaron Judge')
        mapping: 映射表
    
    Returns:
        Lahman playerID (e.g., 'judgeaa01')
    """
    return mapping['name_to_id'].get(player_name, None)


if __name__ == "__main__":
    # 建立映射表
    mapping = create_player_mapping()
    
    # 測試
    print("\n" + "=" * 80)
    print("測試映射")
    print("=" * 80)
    
    test_cases = [
        ('judgeaa01', 'Aaron Judge'),
        ('ohtansh01', 'Shohei Ohtani'),
        ('troutmi01', 'Mike Trout')
    ]
    
    for player_id, expected_name in test_cases:
        found_name = find_player_name(player_id, mapping)
        found_id = find_player_id(expected_name, mapping)
        
        print(f"\n測試: {player_id}")
        print(f"  ID → 名字: {found_name} {'✅' if found_name == expected_name else '❌'}")
        print(f"  名字 → ID: {found_id} {'✅' if found_id == player_id else '❌'}")
