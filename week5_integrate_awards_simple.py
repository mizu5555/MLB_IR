"""
Week 5: 簡化獎項整合（不使用 Lahman）

直接基於球員名字匹配
"""

import json
from typing import Dict, List


def integrate_awards_simple() -> int:
    """
    整合獎項數據到球員文檔（簡化版）
    
    Returns:
        整合成功的球員數量
    """
    
    print("=" * 80)
    print("整合獎項數據（簡化版）")
    print("=" * 80)
    
    # 1. 載入球員文檔
    print("\n[載入數據]")
    
    try:
        with open('./mlb_data/mlb_documents.json', 'r', encoding='utf-8') as f:
            documents = json.load(f)
        print(f"✅ 球員文檔: {len(documents)} 筆")
    except FileNotFoundError:
        print("❌ 找不到 mlb_documents.json")
        return 0
    
    # 2. 載入獎項數據
    try:
        with open('./mlb_data/week5_awards.json', 'r', encoding='utf-8') as f:
            awards_data = json.load(f)
        print(f"✅ 獎項數據: {len(awards_data)} 位球員")
    except FileNotFoundError:
        print("❌ 找不到 week5_awards.json")
        print("   請先執行: python week5_awards_simple.py")
        return 0
    
    # 3. 整合獎項
    print("\n[整合獎項]")
    
    integrated_count = 0
    
    for doc in documents:
        player_name = doc['player_name']
        
        if player_name in awards_data:
            # 有獎項數據
            doc['awards'] = awards_data[player_name]
            integrated_count += 1
        else:
            # 沒有獎項數據
            doc['awards'] = {'total_count': 0}
    
    print(f"✅ 整合完成: {integrated_count}/{len(documents)} 位球員有獎項")
    
    # 4. 加入薪資和 Statcast 欄位（空的）
    print("\n[加入其他欄位]")
    
    for doc in documents:
        # 薪資欄位
        doc['contract'] = None
        
        # Statcast 欄位
        doc['statcast'] = {
            'note': 'Statcast 數據待補充',
            'years_available': [2020, 2021, 2022, 2023, 2024, 2025]
        }
    
    print("✅ 已加入 contract 和 statcast 欄位")
    
    # 5. 儲存整合後的文檔
    print("\n[儲存數據]")
    
    output_file = "./mlb_data/week5_mlb_documents_enhanced.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已儲存: {output_file}")
    
    # 6. 顯示樣本
    print("\n[樣本球員]")
    
    # 找出有獎項的球員樣本
    players_with_awards = [doc for doc in documents if doc['awards']['total_count'] > 0]
    
    if players_with_awards:
        sample = players_with_awards[0]
        print(f"\n球員: {sample['player_name']} ({sample['season']})")
        print(f"獎項: {sample['awards']['total_count']} 個")
        
        for award_type, years in sample['awards'].items():
            if award_type != 'total_count':
                print(f"  {award_type}: {years}")
    
    return integrated_count


if __name__ == "__main__":
    
    integrated = integrate_awards_simple()
    
    print("\n" + "=" * 80)
    print("✨ 獎項整合完成")
    print("=" * 80)
    
    if integrated > 0:
        print(f"\n✅ 成功整合 {integrated} 位球員的獎項數據")
        print("\n整合後的文檔: ./mlb_data/week5_mlb_documents_enhanced.json")
        print("\n下一步：")
        print("  python week5_test.py  # 測試整合結果")
    else:
        print("\n❌ 整合失敗，請檢查錯誤訊息")
