"""
Phase 5: 步驟 3 - 建立 Vector Index
使用 FAISS 建立高效的向量索引
"""

import json
import numpy as np
import pickle
import time


def load_embeddings():
    """載入 embeddings"""
    
    print("=" * 80)
    print("載入 Embeddings")
    print("=" * 80)
    
    print("\n載入數據...")
    
    # 載入 embeddings
    embeddings = np.load('./mlb_data/week5_embeddings_enhanced.npy')
    print(f"✅ Embeddings: {embeddings.shape}")
    
    # 載入 player IDs
    with open('./mlb_data/week5_player_ids_enhanced.json', 'r', encoding='utf-8') as f:
        player_ids = json.load(f)
    print(f"✅ Player IDs: {len(player_ids)}")
    
    return embeddings, player_ids


def build_faiss_index(embeddings: np.ndarray):
    """
    建立 FAISS 索引
    
    Args:
        embeddings: embeddings array
    
    Returns:
        FAISS index
    """
    
    print("\n" + "=" * 80)
    print("建立 FAISS 索引")
    print("=" * 80)
    
    # 檢查是否安裝 faiss
    try:
        import faiss
    except ImportError:
        print("\n❌ 錯誤: 未安裝 faiss")
        print("\n請執行:")
        print("  pip install faiss-cpu --break-system-packages")
        return None
    
    print("\n索引類型: IndexFlatIP (內積相似度)")
    print(f"向量維度: {embeddings.shape[1]}")
    print(f"向量數量: {len(embeddings)}")
    
    start_time = time.time()
    
    # 建立索引
    dimension = embeddings.shape[1]
    
    # 使用 IndexFlatIP (內積)，適合餘弦相似度
    # 注意：embeddings 需要先正規化
    print("\n正規化向量...")
    embeddings_normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    print("建立索引...")
    index = faiss.IndexFlatIP(dimension)
    
    # 添加向量
    print("添加向量到索引...")
    index.add(embeddings_normalized.astype('float32'))
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ 索引建立完成！")
    print(f"   時間: {elapsed:.2f}s")
    print(f"   索引大小: {index.ntotal} 個向量")
    
    return index, embeddings_normalized


def save_index(index, embeddings_normalized: np.ndarray, player_ids: list):
    """
    儲存索引和相關數據
    
    Args:
        index: FAISS index
        embeddings_normalized: 正規化的 embeddings
        player_ids: 球員 ID 列表
    """
    
    print("\n" + "=" * 80)
    print("儲存索引")
    print("=" * 80)
    
    try:
        import faiss
        
        # 儲存 FAISS 索引
        index_file = './mlb_data/week5_faiss_index_enhanced.index'
        faiss.write_index(index, index_file)
        print(f"✅ FAISS Index: {index_file}")
    except Exception as e:
        print(f"⚠️  FAISS 索引儲存失敗: {e}")
    
    # 儲存正規化的 embeddings（用於後續查詢）
    embeddings_file = './mlb_data/week5_embeddings_normalized_enhanced.npy'
    np.save(embeddings_file, embeddings_normalized)
    print(f"✅ Normalized Embeddings: {embeddings_file}")
    
    # 儲存完整的 vector database metadata
    metadata = {
        'total_vectors': len(player_ids),
        'dimension': embeddings_normalized.shape[1],
        'player_ids': player_ids,
        'index_type': 'IndexFlatIP',
        'normalized': True
    }
    
    metadata_file = './mlb_data/week5_vector_db_metadata_enhanced.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ Metadata: {metadata_file}")


def test_index(index, embeddings_normalized: np.ndarray, player_ids: list):
    """測試索引"""
    
    print("\n" + "=" * 80)
    print("測試索引")
    print("=" * 80)
    
    # 隨機選一個向量進行查詢
    test_idx = np.random.randint(0, len(embeddings_normalized))
    test_vector = embeddings_normalized[test_idx:test_idx+1]
    
    print(f"\n測試查詢: {player_ids[test_idx]}")
    print("查詢 top 5 最相似...")
    
    k = 5
    distances, indices = index.search(test_vector, k)
    
    print("\n結果:")
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
        print(f"  {i}. {player_ids[idx]:<40s} (相似度: {dist:.4f})")
    
    # 驗證：第一個應該是自己（相似度 ~1.0）
    if indices[0][0] == test_idx:
        print("\n✅ 索引驗證通過（第一個結果是查詢本身）")
    else:
        print("\n⚠️  警告: 索引可能有問題")


def compare_with_old_index():
    """與舊索引比較"""
    
    print("\n" + "=" * 80)
    print("與舊索引比較")
    print("=" * 80)
    
    # 檢查舊索引是否存在
    try:
        old_embeddings = np.load('./mlb_data/week5_embeddings.npy')
        print(f"\n舊索引:")
        print(f"  向量數量: {len(old_embeddings)}")
        print(f"  向量維度: {old_embeddings.shape[1]}")
    except FileNotFoundError:
        print("\n舊索引不存在，跳過比較")
        return
    
    # 載入新索引
    new_embeddings = np.load('./mlb_data/week5_embeddings_enhanced.npy')
    print(f"\n新索引:")
    print(f"  向量數量: {len(new_embeddings)}")
    print(f"  向量維度: {new_embeddings.shape[1]}")
    
    # 比較
    print(f"\n比較:")
    print(f"  數量差異: {len(new_embeddings) - len(old_embeddings)}")
    
    # 計算平均向量長度
    old_norm = np.linalg.norm(old_embeddings, axis=1).mean()
    new_norm = np.linalg.norm(new_embeddings, axis=1).mean()
    
    print(f"  舊索引平均向量長度: {old_norm:.4f}")
    print(f"  新索引平均向量長度: {new_norm:.4f}")


def main():
    """主程式"""
    
    print("=" * 80)
    print("Phase 5: Vector Database 重建 - 步驟 3/3")
    print("=" * 80)
    print("\n建立 FAISS 向量索引")
    
    # 1. 載入 embeddings
    embeddings, player_ids = load_embeddings()
    
    # 2. 建立索引
    result = build_faiss_index(embeddings)
    
    if result is None:
        return
    
    index, embeddings_normalized = result
    
    # 3. 儲存
    save_index(index, embeddings_normalized, player_ids)
    
    # 4. 測試
    test_index(index, embeddings_normalized, player_ids)
    
    # 5. 比較
    compare_with_old_index()
    
    print("\n" + "=" * 80)
    print("✨ Phase 5 完成！")
    print("=" * 80)
    print("\n成果:")
    print("  ✅ 包含 Statcast 的文字描述")
    print("  ✅ 新的 embeddings")
    print("  ✅ 新的 FAISS 索引")
    print("\n生成的檔案:")
    print("  • week5_text_chunks_enhanced.csv")
    print("  • week5_embeddings_enhanced.npy")
    print("  • week5_embeddings_normalized_enhanced.npy")
    print("  • week5_faiss_index_enhanced.index")
    print("  • week5_player_ids_enhanced.json")
    print("  • week5_vector_db_metadata_enhanced.json")
    print("\n下一步:")
    print("  python phase5_test_retrieval.py  # 測試檢索品質")


if __name__ == "__main__":
    main()
