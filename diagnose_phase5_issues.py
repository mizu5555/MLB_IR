"""
診斷 Phase 5 問題
檢查文字描述、embeddings 和索引
"""

import json
import pandas as pd
import numpy as np


def check_data_source():
    """檢查數據來源"""
    
    print("=" * 80)
    print("檢查數據來源")
    print("=" * 80)
    
    # 檢查原始文檔
    print("\n1. 檢查原始文檔...")
    try:
        with open('./mlb_data/week5_mlb_documents_final_enhanced.json', 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        print(f"✅ 文檔數量: {len(documents)}")
        
        # 檢查是否有 2025 的數據
        if isinstance(documents, list):
            seasons = set(doc.get('season') for doc in documents if 'season' in doc)
        else:
            seasons = set(doc.get('season') for doc in documents.values() if 'season' in doc)
        
        print(f"   賽季: {sorted(seasons)}")
        
        # 檢查 Aaron Judge
        if isinstance(documents, list):
            judge_docs = [doc for doc in documents if doc.get('player_name') == 'Aaron Judge']
        else:
            judge_docs = [doc for doc in documents.values() if doc.get('player_name') == 'Aaron Judge']
        
        print(f"\n   Aaron Judge 記錄: {len(judge_docs)}")
        for doc in judge_docs:
            season = doc.get('season')
            player_type = doc.get('type')
            has_statcast = 'statcast' in doc and doc['statcast']
            print(f"     - {season} ({player_type}), Statcast: {has_statcast}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def check_text_chunks():
    """檢查文字描述"""
    
    print("\n" + "=" * 80)
    print("檢查文字描述")
    print("=" * 80)
    
    try:
        # 載入文字描述
        with open('./mlb_data/week5_text_chunks_enhanced.json', 'r', encoding='utf-8') as f:
            text_chunks = json.load(f)
        
        print(f"\n✅ 文字描述數量: {len(text_chunks)}")
        
        # 檢查 Aaron Judge_2022
        if 'Aaron Judge_2022' in text_chunks:
            text = text_chunks['Aaron Judge_2022']
            print(f"\n✅ 找到 Aaron Judge_2022")
            print(f"   長度: {len(text)} 字符")
            print(f"   內容預覽:")
            print(f"   {text[:500]}...")
            
            # 檢查關鍵字
            keywords = ['home run', 'Home Runs', 'HR:', '62', 'exit velocity', 'Exit Velocity']
            print(f"\n   關鍵字檢查:")
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    print(f"     ✅ 包含 '{keyword}'")
                else:
                    print(f"     ❌ 缺少 '{keyword}'")
        else:
            print(f"\n❌ 找不到 Aaron Judge_2022")
            
            # 列出所有 Aaron Judge 的記錄
            judge_keys = [k for k in text_chunks.keys() if 'Aaron Judge' in k]
            print(f"\n   Aaron Judge 相關記錄:")
            for key in judge_keys:
                print(f"     - {key}")
        
        # 檢查是否有 2025 的數據
        keys_2025 = [k for k in text_chunks.keys() if '_2025' in k]
        print(f"\n   2025 賽季記錄數: {len(keys_2025)}")
        if keys_2025:
            print(f"   範例: {keys_2025[:5]}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def check_player_ids():
    """檢查 player IDs"""
    
    print("\n" + "=" * 80)
    print("檢查 Player IDs")
    print("=" * 80)
    
    try:
        with open('./mlb_data/week5_player_ids_enhanced.json', 'r', encoding='utf-8') as f:
            player_ids = json.load(f)
        
        print(f"\n✅ Player IDs 數量: {len(player_ids)}")
        
        # 檢查 Aaron Judge_2022
        if 'Aaron Judge_2022' in player_ids:
            idx = player_ids.index('Aaron Judge_2022')
            print(f"\n✅ Aaron Judge_2022 在索引位置: {idx}")
        else:
            print(f"\n❌ 找不到 Aaron Judge_2022")
            
            # 列出所有 Aaron Judge
            judge_ids = [pid for pid in player_ids if 'Aaron Judge' in pid]
            print(f"\n   Aaron Judge 相關 IDs:")
            for pid in judge_ids:
                print(f"     - {pid}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def test_manual_query():
    """手動測試查詢"""
    
    print("\n" + "=" * 80)
    print("手動測試查詢")
    print("=" * 80)
    
    try:
        # 載入所有必要數據
        import faiss
        from sentence_transformers import SentenceTransformer
        
        print("\n載入數據...")
        index = faiss.read_index('./mlb_data/week5_faiss_index_enhanced.index')
        
        with open('./mlb_data/week5_player_ids_enhanced.json', 'r', encoding='utf-8') as f:
            player_ids = json.load(f)
        
        with open('./mlb_data/week5_text_chunks_enhanced.json', 'r', encoding='utf-8') as f:
            text_chunks = json.load(f)
        
        print("✅ 數據載入完成")
        
        # 載入模型
        print("\n載入 embedding 模型...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 測試查詢
        queries = [
            "Aaron Judge 2022",
            "Aaron Judge home runs",
            "Player: Aaron Judge. Season: 2022"
        ]
        
        for query in queries:
            print(f"\n查詢: '{query}'")
            
            # 編碼查詢
            query_vector = model.encode([query], convert_to_numpy=True)
            query_vector = query_vector / np.linalg.norm(query_vector, axis=1, keepdims=True)
            
            # 搜尋
            distances, indices = index.search(query_vector, 5)
            
            print("  Top 5:")
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
                pid = player_ids[idx]
                print(f"    {i}. {pid:<30s} (分數: {dist:.4f})")
        
        # 直接測試 Aaron Judge_2022 的向量
        print(f"\n" + "=" * 80)
        print("測試 Aaron Judge_2022 自身相似度")
        print("=" * 80)
        
        if 'Aaron Judge_2022' in player_ids:
            idx = player_ids.index('Aaron Judge_2022')
            
            # 取得該向量
            embeddings = np.load('./mlb_data/week5_embeddings_normalized_enhanced.npy')
            test_vector = embeddings[idx:idx+1]
            
            # 搜尋
            distances, indices = index.search(test_vector, 5)
            
            print(f"\n使用 Aaron Judge_2022 的向量查詢:")
            print("  Top 5:")
            for i, (dist, idx_result) in enumerate(zip(distances[0], indices[0]), 1):
                pid = player_ids[idx_result]
                is_self = "← 自己" if idx_result == idx else ""
                print(f"    {i}. {pid:<30s} (分數: {dist:.4f}) {is_self}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主程式"""
    
    print("=" * 80)
    print("Phase 5 問題診斷")
    print("=" * 80)
    
    # 1. 檢查數據來源
    check_data_source()
    
    # 2. 檢查文字描述
    check_text_chunks()
    
    # 3. 檢查 player IDs
    check_player_ids()
    
    # 4. 手動測試查詢
    test_manual_query()
    
    print("\n" + "=" * 80)
    print("診斷完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
