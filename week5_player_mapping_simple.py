"""
Week 5: 基於現有資料的 playerID 映射表生成器

策略：不使用 Lahman 資料庫，而是基於 FanGraphs/MLB Stats API 的球員資料
建立自己的映射表
"""

import json
import requests
from typing import Dict, Optional
import time


def create_mapping_from_existing_data() -> Dict:
    """
    從現有球員文檔建立映射表
    
    策略：使用球員名字作為主鍵，不需要 Lahman playerID
    """
    
    print("=" * 80)
    print("建立球員名字映射表（基於現有資料）")
    print("=" * 80)
    
    try:
        # 載入現有球員資料
        print("正在載入現有球員資料...")
        with open('./mlb_data/mlb_documents.json', 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        print(f"✅ 成功載入 {len(documents)} 筆球員資料")
        
        # 收集所有唯一球員名字
        unique_players = set()
        for doc in documents:
            unique_players.add(doc['player_name'])
        
        print(f"✅ 發現 {len(unique_players)} 位唯一球員")
        
        # 建立簡化的映射表（名字 -> 名字，因為我們不使用 Lahman ID）
        name_to_name = {name: name for name in unique_players}
        
        # 儲存映射表
        mapping = {
            'source': 'existing_documents',
            'note': '基於現有 mlb_documents.json 建立，不使用 Lahman playerID',
            'player_count': len(unique_players),
            'players': list(unique_players)
        }
        
        output_file = "./mlb_data/week5_player_mapping.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 映射表已儲存: {output_file}")
        
        # 顯示樣本
        print("\n[球員樣本]")
        sample_players = sorted(list(unique_players))[:10]
        for i, name in enumerate(sample_players, 1):
            print(f"  {i}. {name}")
        
        return mapping
        
    except Exception as e:
        print(f"❌ 映射表建立失敗: {e}")
        return {}


def fetch_mlb_player_id(player_name: str) -> Optional[str]:
    """
    使用 MLB Stats API 查找球員 ID
    
    這個 ID 可以用於後續的 API 查詢
    """
    
    try:
        # MLB Stats API search endpoint
        url = f"http://lookup-service-prod.mlb.com/json/named.search_player_all.bam"
        params = {
            'sport_code': "'mlb'",
            'active_sw': "'Y'",
            'name_part': f"'{player_name}'"
        }
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # 解析回應
            results = data.get('search_player_all', {}).get('queryResults', {})
            if results.get('totalSize') == '1':
                player = results['row']
                return player.get('player_id')
        
        return None
        
    except Exception as e:
        print(f"  ⚠️  查找 {player_name} 失敗: {e}")
        return None


def enhance_mapping_with_mlb_ids() -> Dict:
    """
    增強映射表：加入 MLB Stats API 的 player ID
    
    這是可選步驟，只有在需要使用 MLB Stats API 時才需要
    """
    
    print("\n" + "=" * 80)
    print("增強映射表：加入 MLB Stats API IDs")
    print("=" * 80)
    
    try:
        # 載入球員列表
        with open('./mlb_data/week5_player_mapping.json', 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        players = mapping.get('players', [])
        print(f"正在查找 {len(players)} 位球員的 MLB ID...")
        print("（這可能需要幾分鐘）")
        
        # 建立 name -> MLB ID 映射
        name_to_mlb_id = {}
        
        for i, player_name in enumerate(players[:10], 1):  # 先測試前 10 位
            print(f"[{i}/10] 查找 {player_name}...")
            mlb_id = fetch_mlb_player_id(player_name)
            
            if mlb_id:
                name_to_mlb_id[player_name] = mlb_id
                print(f"  ✅ MLB ID: {mlb_id}")
            else:
                print(f"  ⚠️  未找到 MLB ID")
            
            time.sleep(0.5)  # 避免請求太頻繁
        
        # 更新映射表
        mapping['mlb_ids'] = name_to_mlb_id
        mapping['mlb_id_count'] = len(name_to_mlb_id)
        
        # 儲存
        output_file = "./mlb_data/week5_player_mapping_enhanced.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 增強映射表已儲存: {output_file}")
        print(f"   成功獲取 {len(name_to_mlb_id)} 位球員的 MLB ID")
        
        return mapping
        
    except Exception as e:
        print(f"❌ 增強映射表失敗: {e}")
        return {}


if __name__ == "__main__":
    
    # 步驟 1: 建立基本映射表
    mapping = create_mapping_from_existing_data()
    
    if mapping:
        print("\n✅ 基本映射表建立完成")
        
        # 步驟 2: （可選）增強映射表
        choice = input("\n是否要增強映射表（加入 MLB API IDs）？(y/n): ")
        
        if choice.lower() == 'y':
            enhanced_mapping = enhance_mapping_with_mlb_ids()
    
    print("\n" + "=" * 80)
    print("✨ 映射表生成完成")
    print("=" * 80)
