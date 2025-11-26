"""
Week 5: 測試腳本
測試獎項、薪資、Statcast 數據整合
"""

import json
import os


def test_file_exists(filepath: str) -> bool:
    """測試文件是否存在"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {filepath}")
    return exists


def test_json_valid(filepath: str) -> bool:
    """測試 JSON 文件是否有效"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   📊 {len(data)} 筆記錄")
        return True
    except Exception as e:
        print(f"   ❌ JSON 格式錯誤: {e}")
        return False


def test_data_integration(documents_path: str) -> dict:
    """測試數據整合"""
    
    print("\n" + "=" * 80)
    print("測試數據整合")
    print("=" * 80)
    
    try:
        with open(documents_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        stats = {
            'total_documents': len(documents),
            'with_awards': 0,
            'with_contract': 0,
            'with_statcast': 0,
            'sample_player': None
        }
        
        for doc in documents:
            # 檢查獎項
            if 'awards' in doc and doc['awards'].get('total_count', 0) > 0:
                stats['with_awards'] += 1
                if not stats['sample_player']:
                    stats['sample_player'] = doc
            
            # 檢查合約
            if 'contract' in doc and doc['contract']:
                stats['with_contract'] += 1
            
            # 檢查 Statcast
            if 'statcast' in doc:
                stats['with_statcast'] += 1
        
        return stats
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return None


def main():
    """主測試流程"""
    
    print("=" * 80)
    print("Week 5: 數據收集與整合測試")
    print("=" * 80)
    
    # 測試文件存在性
    print("\n[測試 1: 檢查文件]")
    files_to_check = [
        "./mlb_data/week5_player_mapping.json",
        "./mlb_data/week5_awards.json",
        "./mlb_data/week5_salaries.json",
        "./mlb_data/week5_statcast_structure.json",
        "./mlb_data/week5_mlb_documents_enhanced.json"
    ]
    
    all_exists = True
    for filepath in files_to_check:
        if not test_file_exists(filepath):
            all_exists = False
    
    if not all_exists:
        print("\n❌ 某些文件缺失，請先執行 week5_run_all.bat")
        return
    
    # 測試 JSON 有效性
    print("\n[測試 2: 驗證 JSON 格式]")
    for filepath in files_to_check:
        test_json_valid(filepath)
    
    # 測試數據整合
    stats = test_data_integration("./mlb_data/week5_mlb_documents_enhanced.json")
    
    if stats:
        print(f"\n總文檔數: {stats['total_documents']}")
        print(f"有獎項數據: {stats['with_awards']} 位球員")
        print(f"有合約數據: {stats['with_contract']} 位球員")
        print(f"有 Statcast 結構: {stats['with_statcast']} 位球員")
        
        # 顯示樣本
        if stats['sample_player']:
            print("\n[樣本球員]")
            player = stats['sample_player']
            print(f"球員: {player['player_name']} ({player['season']})")
            
            if 'awards' in player:
                print(f"\n獎項: {player['awards']['total_count']} 個")
                for award_type, years in player['awards'].items():
                    if award_type != 'total_count':
                        print(f"  {award_type}: {years}")
            
            if 'contract' in player and player['contract']:
                print(f"\n合約:")
                print(f"  薪資: ${player['contract']['current_salary']:,}")
                print(f"  年份: {player['contract']['year']}")
                print(f"  球隊: {player['contract']['team']}")
            
            if 'statcast' in player:
                print(f"\nStatcast: {player['statcast'].get('note', '已建立')}")
    
    # 總結
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)
    
    if all_exists and stats:
        print("✅ 所有測試通過")
        print("\n下一步：")
        print("  1. 執行 week5_enhanced_classifier.py 測試查詢分類")
        print("  2. 執行 week5_enhanced_router.py 測試智能路由")
        print("  3. 整合進 Streamlit UI")
    else:
        print("❌ 某些測試失敗，請檢查錯誤訊息")


if __name__ == "__main__":
    main()
