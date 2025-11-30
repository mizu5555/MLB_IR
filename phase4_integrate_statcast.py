"""
Phase 4: Statcast 數據整合
將 Statcast 數據整合到球員文檔
"""

import json
from typing import Dict


def load_data():
    """載入所有必要數據"""
    
    print("=" * 80)
    print("載入數據")
    print("=" * 80)
    
    # 載入現有球員文檔
    print("\n載入球員文檔...")
    with open('./mlb_data/week5_mlb_documents_enhanced.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    print(f"✅ {len(documents)} 筆記錄")
    
    # 載入 Statcast 數據
    print("\n載入 Statcast 數據...")
    try:
        with open('./mlb_data/week5_statcast.json', 'r', encoding='utf-8') as f:
            statcast_data = json.load(f)
        print(f"✅ {len(statcast_data)} 筆記錄")
    except FileNotFoundError:
        print("❌ Statcast 數據未找到")
        print("   請先執行: python phase4_download_statcast.py")
        return None, None
    
    return documents, statcast_data


def match_player_name(doc_name: str, statcast_name: str) -> bool:
    """
    匹配球員名字
    
    處理名字變體：
    - "Aaron Judge" vs "Judge, Aaron"
    - "Ronald Acuña Jr." vs "Ronald Acuna"
    """
    
    # 移除特殊字符
    def normalize(name):
        return name.lower().replace('jr.', '').replace('sr.', '').replace('.', '').replace(',', '').strip()
    
    doc_normalized = normalize(doc_name)
    statcast_normalized = normalize(statcast_name)
    
    # 直接匹配
    if doc_normalized == statcast_normalized:
        return True
    
    # 姓氏匹配（如果 Statcast 名字包含文檔姓氏）
    doc_parts = doc_normalized.split()
    statcast_parts = statcast_normalized.split()
    
    if doc_parts and statcast_parts:
        # 比較姓氏（通常是最後一個詞）
        if doc_parts[-1] == statcast_parts[-1]:
            # 再檢查名字首字母
            if len(doc_parts) > 1 and len(statcast_parts) > 1:
                if doc_parts[0][0] == statcast_parts[0][0]:
                    return True
    
    return False


def integrate_statcast(documents, statcast_data: Dict):
    """
    整合 Statcast 數據到球員文檔
    
    Args:
        documents: 球員文檔 (list 或 dict)
        statcast_data: Statcast 數據
    
    Returns:
        整合後的文檔 (與輸入格式相同)
    """
    
    print("\n" + "=" * 80)
    print("整合 Statcast 數據")
    print("=" * 80)
    
    # 判斷 documents 格式並轉換為統一格式
    is_list_format = isinstance(documents, list)
    
    if is_list_format:
        print("檢測到 list 格式，轉換中...")
        # 轉換 list 為 dict 以便處理
        documents_dict = {}
        for i, doc in enumerate(documents):
            # 使用 player_name + season 作為 key
            player_name = doc.get('player_name', '')
            season = doc.get('season', 0)
            doc_id = f"{player_name}_{season}" if player_name and season else str(i)
            documents_dict[doc_id] = doc
        working_docs = documents_dict
    else:
        working_docs = documents
    
    match_count = 0
    total_docs = len(working_docs)
    
    # 建立 Statcast 快速查找索引
    print("\n建立 Statcast 索引...")
    statcast_by_player = {}
    
    for key, data in statcast_data.items():
        player_name = data['player_name']
        year = data['year']
        
        if player_name not in statcast_by_player:
            statcast_by_player[player_name] = {}
        
        statcast_by_player[player_name][year] = data
    
    print(f"✅ {len(statcast_by_player)} 位球員的 Statcast 數據")
    
    # 整合到文檔
    print("\n開始整合...")
    
    for doc_id, doc in working_docs.items():
        player_name = doc.get('player_name', '')
        season = doc.get('season', 0)
        
        if not player_name or not season:
            continue
        
        # 尋找匹配的 Statcast 數據
        matched_statcast = None
        
        # 方法 1: 直接名字匹配
        if player_name in statcast_by_player:
            if season in statcast_by_player[player_name]:
                matched_statcast = statcast_by_player[player_name][season]
        
        # 方法 2: 模糊匹配
        if not matched_statcast:
            for statcast_player, years_data in statcast_by_player.items():
                if match_player_name(player_name, statcast_player):
                    if season in years_data:
                        matched_statcast = years_data[season]
                        break
        
        # 整合數據
        if matched_statcast:
            # 移除不需要的欄位
            statcast_clean = {k: v for k, v in matched_statcast.items() 
                            if k not in ['player_name', 'year', 'type']}
            
            # 更新文檔
            if 'statcast' not in doc:
                doc['statcast'] = {}
            
            doc['statcast'].update(statcast_clean)
            match_count += 1
    
    match_rate = (match_count / total_docs) * 100 if total_docs > 0 else 0
    
    print(f"\n✅ 整合完成")
    print(f"   匹配成功: {match_count}/{total_docs} ({match_rate:.1f}%)")
    
    # 根據原始格式返回
    if is_list_format:
        print("轉換回 list 格式...")
        result = list(working_docs.values())
        return result
    else:
        return working_docs


def save_integrated_data(documents):
    """儲存整合後的數據"""
    
    print("\n" + "=" * 80)
    print("儲存數據")
    print("=" * 80)
    
    output_file = './mlb_data/week5_mlb_documents_final.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已儲存: {output_file}")
    
    # 統計
    total_docs = len(documents)
    
    # 判斷格式
    if isinstance(documents, list):
        with_statcast = sum(1 for doc in documents 
                           if 'statcast' in doc and any(v is not None for v in doc['statcast'].values() if isinstance(v, (int, float))))
    else:
        with_statcast = sum(1 for doc in documents.values() 
                           if 'statcast' in doc and any(v is not None for v in doc['statcast'].values() if isinstance(v, (int, float))))
    
    print(f"\n數據統計:")
    print(f"  總文檔數: {total_docs}")
    print(f"  有 Statcast: {with_statcast} ({(with_statcast/total_docs)*100:.1f}%)")



def show_examples(documents):
    """顯示範例"""
    
    print("\n" + "=" * 80)
    print("範例球員")
    print("=" * 80)
    
    # 找出有 Statcast 數據的球員
    players_with_statcast = []
    
    # 判斷格式並統一處理
    if isinstance(documents, list):
        doc_iterator = enumerate(documents)
    else:
        doc_iterator = documents.items()
    
    for doc_id, doc in doc_iterator:
        if 'statcast' in doc:
            statcast = doc['statcast']
            # 檢查是否有實際數據（不是空的或全是 None）
            has_data = any(v is not None for v in statcast.values() if isinstance(v, (int, float)))
            if has_data:
                players_with_statcast.append((doc_id, doc))
                if len(players_with_statcast) >= 3:
                    break
    
    # 顯示範例
    for i, (doc_id, doc) in enumerate(players_with_statcast[:3], 1):
        print(f"\n範例 {i}: {doc['player_name']} ({doc['season']})")
        print(f"類型: {doc.get('type', 'N/A')}")
        
        statcast = doc.get('statcast', {})
        
        if doc.get('type') == 'batter':
            print("打者 Statcast:")
            print(f"  Exit Velocity: {statcast.get('exit_velocity', 'N/A')}")
            print(f"  Launch Angle: {statcast.get('launch_angle', 'N/A')}")
            print(f"  Barrel Rate: {statcast.get('barrel_rate', 'N/A')}%")
            print(f"  Hard-Hit Rate: {statcast.get('hard_hit_rate', 'N/A')}%")
            print(f"  xwOBA: {statcast.get('xwoba', 'N/A')}")
        elif doc.get('type') == 'pitcher':
            print("投手 Statcast:")
            print(f"  Fastball Velocity: {statcast.get('fastball_velocity', 'N/A')}")
            print(f"  Fastball Spin: {statcast.get('fastball_spin', 'N/A')}")
            print(f"  Whiff Rate: {statcast.get('whiff_rate', 'N/A')}%")
            print(f"  Chase Rate: {statcast.get('chase_rate', 'N/A')}%")


def main():
    """主程式"""
    
    print("\n" + "=" * 80)
    print("Phase 4: Statcast 數據整合")
    print("=" * 80)
    
    try:
        # 載入數據
        documents, statcast_data = load_data()
        
        if documents is None or statcast_data is None:
            return
        
        # 整合數據
        integrated_docs = integrate_statcast(documents, statcast_data)
        
        # 儲存
        save_integrated_data(integrated_docs)
        
        # 顯示範例
        show_examples(integrated_docs)
        
        print("\n" + "=" * 80)
        print("✨ Phase 4 完成！")
        print("=" * 80)
        print("\n系統現在支援:")
        print("  ✅ 基礎統計查詢")
        print("  ✅ 排名查詢")
        print("  ✅ 獎項查詢")
        print("  ✅ 合約查詢")
        print("  ✅ Statcast 查詢 ← 新增！")
        print("\n下一步:")
        print("  1. 測試 Statcast 查詢功能")
        print("  2. 建立 Phase 4 總結報告")
        
    except Exception as e:
        print(f"\n❌ 整合失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
