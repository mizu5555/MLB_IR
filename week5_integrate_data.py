"""
Week 5: 數據整合腳本
將獎項、薪資、Statcast 數據整合到現有球員文檔
"""

import json
from typing import Dict, List
import os


def load_json(filepath: str) -> any:
    """載入 JSON 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"❌ JSON 格式錯誤: {filepath}")
        return None


def save_json(data: any, filepath: str):
    """儲存 JSON 文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ 已儲存: {filepath}")


def integrate_awards(documents: List[Dict], awards_data: Dict, mapping: Dict) -> int:
    """
    整合獎項數據到球員文檔
    
    Args:
        documents: 球員文檔列表
        awards_data: 獎項數據 (playerID -> awards)
        mapping: playerID 映射表
    
    Returns:
        整合成功的球員數量
    """
    
    print("\n整合獎項數據...")
    
    integrated_count = 0
    id_to_name = mapping['id_to_name']
    
    for doc in documents:
        player_name = doc['player_name']
        
        # 嘗試找到對應的 playerID
        player_id = None
        for pid, name in id_to_name.items():
            if name == player_name:
                player_id = pid
                break
        
        if player_id and player_id in awards_data:
            doc['awards'] = awards_data[player_id]
            integrated_count += 1
        else:
            # 沒有獎項數據
            doc['awards'] = {'total_count': 0}
    
    print(f"✅ 獎項整合: {integrated_count}/{len(documents)} 位球員")
    return integrated_count


def integrate_salaries(documents: List[Dict], salary_data: Dict, mapping: Dict) -> int:
    """
    整合薪資數據到球員文檔
    
    Args:
        documents: 球員文檔列表
        salary_data: 薪資數據 (playerID -> salary)
        mapping: playerID 映射表
    
    Returns:
        整合成功的球員數量
    """
    
    print("\n整合薪資數據...")
    
    integrated_count = 0
    id_to_name = mapping['id_to_name']
    
    for doc in documents:
        player_name = doc['player_name']
        
        # 嘗試找到對應的 playerID
        player_id = None
        for pid, name in id_to_name.items():
            if name == player_name:
                player_id = pid
                break
        
        if player_id and player_id in salary_data:
            doc['contract'] = salary_data[player_id]
            integrated_count += 1
        else:
            # 沒有薪資數據
            doc['contract'] = None
    
    print(f"✅ 薪資整合: {integrated_count}/{len(documents)} 位球員")
    return integrated_count


def integrate_statcast(documents: List[Dict], statcast_data: Dict) -> int:
    """
    整合 Statcast 數據到球員文檔
    
    注意：Statcast 數據需要另外處理，這裡先建立欄位結構
    
    Args:
        documents: 球員文檔列表
        statcast_data: Statcast 數據結構
    
    Returns:
        整合成功的球員數量
    """
    
    print("\n整合 Statcast 數據結構...")
    
    # 先建立空的 Statcast 欄位
    for doc in documents:
        doc['statcast'] = {
            'note': 'Statcast 數據待補充',
            'years_available': statcast_data['years'],
            'metrics': statcast_data['metrics']
        }
    
    print(f"✅ Statcast 結構已加入所有球員文檔")
    return len(documents)


def main():
    """主整合流程"""
    
    print("=" * 80)
    print("Week 5: 數據整合")
    print("=" * 80)
    
    # 1. 載入現有球員文檔
    print("\n[載入數據]")
    documents = load_json("./mlb_data/mlb_documents.json")
    
    if documents is None:
        print("❌ 無法載入球員文檔，中止")
        return
    
    print(f"✅ 球員文檔: {len(documents)} 筆")
    
    # 2. 載入新收集的數據
    awards_data = load_json("./mlb_data/week5_awards.json")
    salary_data = load_json("./mlb_data/week5_salaries.json")
    statcast_data = load_json("./mlb_data/week5_statcast_structure.json")
    mapping = load_json("./mlb_data/week5_player_mapping.json")
    
    # 檢查必要數據
    if not mapping:
        print("❌ 缺少映射表，請先執行 week5_player_mapping.py")
        return
    
    print(f"✅ 獎項數據: {len(awards_data) if awards_data else 0} 位球員")
    print(f"✅ 薪資數據: {len(salary_data) if salary_data else 0} 位球員")
    print(f"✅ Statcast 結構: 已載入")
    print(f"✅ 映射表: {len(mapping['id_to_name'])} 位球員")
    
    # 3. 整合數據
    print("\n" + "=" * 80)
    print("整合數據")
    print("=" * 80)
    
    awards_count = 0
    salary_count = 0
    statcast_count = 0
    
    if awards_data and mapping:
        awards_count = integrate_awards(documents, awards_data, mapping)
    
    if salary_data and mapping:
        salary_count = integrate_salaries(documents, salary_data, mapping)
    
    if statcast_data:
        statcast_count = integrate_statcast(documents, statcast_data)
    
    # 4. 儲存整合後的文檔
    print("\n" + "=" * 80)
    print("儲存數據")
    print("=" * 80)
    
    output_file = "./mlb_data/week5_mlb_documents_enhanced.json"
    save_json(documents, output_file)
    
    # 5. 統計
    print("\n" + "=" * 80)
    print("整合完成統計")
    print("=" * 80)
    print(f"總文檔數: {len(documents)}")
    print(f"獎項數據: {awards_count} 位球員")
    print(f"薪資數據: {salary_count} 位球員")
    print(f"Statcast 結構: {statcast_count} 位球員")
    
    # 6. 顯示樣本
    print("\n[整合後樣本]")
    sample_count = min(3, len(documents))
    
    for i in range(sample_count):
        doc = documents[i]
        print(f"\n球員: {doc['player_name']} ({doc['season']})")
        
        # 獎項
        if 'awards' in doc and doc['awards'].get('total_count', 0) > 0:
            print(f"  獎項: {doc['awards']['total_count']} 個")
            for award_type, years in doc['awards'].items():
                if award_type != 'total_count':
                    print(f"    {award_type}: {years}")
        else:
            print(f"  獎項: 無")
        
        # 薪資
        if 'contract' in doc and doc['contract']:
            salary = doc['contract']['current_salary']
            print(f"  薪資: ${salary:,} ({doc['contract']['year']})")
        else:
            print(f"  薪資: 無數據")
        
        # Statcast
        if 'statcast' in doc:
            print(f"  Statcast: 結構已建立")
    
    print("\n" + "=" * 80)
    print("✨ Week 5 數據整合完成")
    print("=" * 80)
    print(f"\n整合後文檔: {output_file}")


if __name__ == "__main__":
    main()
