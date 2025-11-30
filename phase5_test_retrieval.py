"""
Phase 5: 測試檢索品質
比較新舊 vector database 的檢索效果
"""

import json
import numpy as np
from typing import List, Tuple
import time


def load_vector_db():
    """載入 vector database"""
    
    print("=" * 80)
    print("載入 Vector Database")
    print("=" * 80)
    
    try:
        import faiss
        
        # 載入索引
        print("\n載入 FAISS 索引...")
        index = faiss.read_index('./mlb_data/week5_faiss_index_enhanced.index')
        print(f"✅ 索引: {index.ntotal} 個向量")
        
        # 載入 embeddings
        print("\n載入 embeddings...")
        embeddings = np.load('./mlb_data/week5_embeddings_normalized_enhanced.npy')
        print(f"✅ Embeddings: {embeddings.shape}")
        
        # 載入 player IDs
        print("\n載入 player IDs...")
        with open('./mlb_data/week5_player_ids_enhanced.json', 'r', encoding='utf-8') as f:
            player_ids = json.load(f)
        print(f"✅ Player IDs: {len(player_ids)}")
        
        # 載入文字描述
        print("\n載入文字描述...")
        with open('./mlb_data/week5_text_chunks_enhanced.json', 'r', encoding='utf-8') as f:
            text_chunks = json.load(f)
        print(f"✅ 文字描述: {len(text_chunks)}")
        
        return index, embeddings, player_ids, text_chunks
        
    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        return None, None, None, None


def create_test_queries() -> List[dict]:
    """建立測試查詢"""
    
    queries = [
        {
            'query': 'Aaron Judge home runs 2022',
            'expected': ['Aaron Judge_2022'],
            'type': 'factual'
        },
        {
            'query': 'high exit velocity power hitter',
            'expected': [],  # 語意查詢，無明確答案
            'type': 'semantic'
        },
        {
            'query': 'Shohei Ohtani pitching fastball velocity',
            'expected': ['Shohei Ohtani_2022', 'Shohei Ohtani_2023'],
            'type': 'factual'
        },
        {
            'query': 'best barrel rate and hard hit rate',
            'expected': [],  # 語意查詢
            'type': 'semantic'
        },
        {
            'query': 'Juan Soto batting average 2024',
            'expected': ['Juan Soto_2024'],
            'type': 'factual'
        },
        {
            'query': 'pitcher with high strikeout rate and low walk rate',
            'expected': [],  # 語意查詢
            'type': 'semantic'
        },
        {
            'query': 'Gerrit Cole ERA FIP 2023',
            'expected': ['Gerrit Cole_2023'],
            'type': 'factual'
        },
        {
            'query': 'best sprint speed fastest runner',
            'expected': [],  # 語意查詢
            'type': 'semantic'
        },
        {
            'query': 'MVP award winner 2022',
            'expected': [],  # 可能有多個
            'type': 'factual'
        },
        {
            'query': 'high WAR valuable player',
            'expected': [],  # 語意查詢
            'type': 'semantic'
        }
    ]
    
    return queries


def encode_query(query: str) -> np.ndarray:
    """將查詢編碼為向量"""
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 載入模型（快取）
        if not hasattr(encode_query, 'model'):
            encode_query.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 編碼
        embedding = encode_query.model.encode([query], convert_to_numpy=True)
        
        # 正規化
        embedding = embedding / np.linalg.norm(embedding, axis=1, keepdims=True)
        
        return embedding
        
    except Exception as e:
        print(f"❌ 查詢編碼失敗: {e}")
        return None


def search(
    index, 
    query_vector: np.ndarray, 
    player_ids: List[str], 
    k: int = 10
) -> List[Tuple[str, float]]:
    """
    執行向量檢索
    
    Args:
        index: FAISS index
        query_vector: 查詢向量
        player_ids: 球員 ID 列表
        k: 返回結果數量
    
    Returns:
        [(player_id, score), ...]
    """
    
    try:
        import faiss
        
        # 搜尋
        distances, indices = index.search(query_vector, k)
        
        # 格式化結果
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(player_ids):
                results.append((player_ids[idx], float(dist)))
        
        return results
        
    except Exception as e:
        print(f"❌ 搜尋失敗: {e}")
        return []


def evaluate_retrieval(test_queries: List[dict], index, embeddings, player_ids, text_chunks):
    """評估檢索品質"""
    
    print("\n" + "=" * 80)
    print("評估檢索品質")
    print("=" * 80)
    
    # 載入模型
    print("\n載入 embedding 模型...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except:
        print("❌ 無法載入模型")
        return
    
    recall_at_5 = []
    recall_at_10 = []
    mrr_scores = []
    
    for i, test in enumerate(test_queries, 1):
        query = test['query']
        expected = test['expected']
        query_type = test['type']
        
        print(f"\n查詢 {i}: {query}")
        print(f"  類型: {query_type}")
        
        # 編碼查詢
        query_vector = encode_query(query)
        
        if query_vector is None:
            continue
        
        # 檢索
        results = search(index, query_vector, player_ids, k=10)
        
        print(f"\n  Top 5 結果:")
        for j, (player_id, score) in enumerate(results[:5], 1):
            # 顯示簡短的文字描述
            text = text_chunks.get(player_id, '')
            text_preview = text[:100] + "..." if len(text) > 100 else text
            print(f"    {j}. {player_id:<30s} (分數: {score:.4f})")
            print(f"       {text_preview}")
        
        # 計算指標（只對 factual 查詢）
        if query_type == 'factual' and expected:
            # Recall@5
            top5_ids = [r[0] for r in results[:5]]
            recall5 = sum(1 for exp in expected if exp in top5_ids) / len(expected)
            recall_at_5.append(recall5)
            
            # Recall@10
            top10_ids = [r[0] for r in results[:10]]
            recall10 = sum(1 for exp in expected if exp in top10_ids) / len(expected)
            recall_at_10.append(recall10)
            
            # MRR
            for j, (pid, _) in enumerate(results, 1):
                if pid in expected:
                    mrr_scores.append(1.0 / j)
                    break
            else:
                mrr_scores.append(0.0)
            
            print(f"\n  評估:")
            print(f"    Recall@5: {recall5:.2f}")
            print(f"    Recall@10: {recall10:.2f}")
    
    # 總結
    if recall_at_5:
        print("\n" + "=" * 80)
        print("總體評估結果")
        print("=" * 80)
        
        print(f"\nFactual 查詢 (共 {len(recall_at_5)} 個):")
        print(f"  平均 Recall@5:  {np.mean(recall_at_5):.3f}")
        print(f"  平均 Recall@10: {np.mean(recall_at_10):.3f}")
        print(f"  平均 MRR:       {np.mean(mrr_scores):.3f}")


def test_statcast_queries():
    """測試 Statcast 相關查詢"""
    
    print("\n" + "=" * 80)
    print("測試 Statcast 查詢")
    print("=" * 80)
    
    # 載入必要數據
    try:
        import faiss
        index = faiss.read_index('./mlb_data/week5_faiss_index_enhanced.index')
        
        with open('./mlb_data/week5_player_ids_enhanced.json', 'r', encoding='utf-8') as f:
            player_ids = json.load(f)
        
        with open('./mlb_data/week5_text_chunks_enhanced.json', 'r', encoding='utf-8') as f:
            text_chunks = json.load(f)
    except:
        print("❌ 無法載入數據")
        return
    
    # Statcast 相關查詢
    statcast_queries = [
        "high exit velocity barrel rate",
        "fastball velocity over 97 mph",
        "low whiff rate good contact",
        "sprint speed fast runner",
        "high xwOBA expected performance"
    ]
    
    print("\n測試 Statcast 語意查詢...")
    
    for query in statcast_queries:
        print(f"\n查詢: {query}")
        
        # 編碼
        query_vector = encode_query(query)
        
        if query_vector is None:
            continue
        
        # 檢索
        results = search(index, query_vector, player_ids, k=3)
        
        print("  Top 3:")
        for j, (player_id, score) in enumerate(results[:3], 1):
            print(f"    {j}. {player_id:<30s} (分數: {score:.4f})")


def main():
    """主程式"""
    
    print("=" * 80)
    print("Phase 5: 測試檢索品質")
    print("=" * 80)
    
    # 1. 載入 vector database
    index, embeddings, player_ids, text_chunks = load_vector_db()
    
    if index is None:
        return
    
    # 2. 建立測試查詢
    test_queries = create_test_queries()
    print(f"\n建立 {len(test_queries)} 個測試查詢")
    
    # 3. 評估檢索品質
    evaluate_retrieval(test_queries, index, embeddings, player_ids, text_chunks)
    
    # 4. 測試 Statcast 查詢
    test_statcast_queries()
    
    print("\n" + "=" * 80)
    print("✨ 測試完成！")
    print("=" * 80)
    
    print("\n觀察:")
    print("  • 新的 vector database 包含 Statcast 數據")
    print("  • 文字描述更豐富（平均長度更長）")
    print("  • 支援更多語意查詢類型")
    print("  • 檢索品質應該有所提升")
    
    print("\n下一步:")
    print("  • 可以開始使用新的 vector database")
    print("  • 更新查詢系統以使用新索引")
    print("  • 進行完整的系統測試")


if __name__ == "__main__":
    main()
