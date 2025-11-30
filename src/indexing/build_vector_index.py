"""
Vector 索引建立模組
使用 sentence-transformers 生成向量嵌入並建立 FAISS 索引
"""

import json
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


class VectorIndexBuilder:
    """Vector 索引建立器"""
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        """
        初始化
        
        Args:
            model_name: sentence-transformers 模型名稱
        """
        print("=" * 80)
        print("初始化 Vector 索引建立器")
        print("=" * 80)
        print(f"載入模型: {model_name}")
        
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # all-MiniLM-L6-v2 的維度
        
        print(f"✅ 模型載入完成，向量維度: {self.dimension}")
        print()
    
    def build_index(self, text_chunks_path):
        """
        建立 FAISS 索引
        
        Args:
            text_chunks_path: 文本描述 JSON 文件路徑
        
        Returns:
            index: FAISS 索引
            embeddings: 向量嵌入
            player_ids: Player IDs 列表
        """
        print("=" * 80)
        print("建立 Vector 索引")
        print("=" * 80)
        
        # 載入文本描述
        print(f"載入文本描述: {text_chunks_path}")
        with open(text_chunks_path, 'r', encoding='utf-8') as f:
            text_chunks = json.load(f)
        
        # 提取文本和 IDs
        if isinstance(text_chunks, dict):
            player_ids = list(text_chunks.keys())
            texts = list(text_chunks.values())
        else:
            player_ids = [item['player_id'] for item in text_chunks]
            texts = [item.get('text_chunk', item.get('text', '')) for item in text_chunks]
        
        print(f"✅ 載入 {len(texts)} 個文本描述")
        print()
        
        # 生成向量嵌入
        print("生成向量嵌入...")
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            batch_size=32
        )
        
        print(f"✅ 生成 {embeddings.shape[0]} 個向量，維度: {embeddings.shape[1]}")
        print()
        
        # 建立 FAISS 索引
        print("建立 FAISS 索引...")
        index = faiss.IndexFlatL2(self.dimension)
        index.add(embeddings)
        
        print(f"✅ FAISS 索引建立完成")
        print(f"   索引大小: {index.ntotal} 個向量")
        print()
        
        return index, embeddings, player_ids
    
    def save_index(self, index, embeddings, player_ids, output_dir='./mlb_datas'):
        """
        儲存索引
        
        Args:
            index: FAISS 索引
            embeddings: 向量嵌入
            player_ids: Player IDs 列表
            output_dir: 輸出目錄
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print("=" * 80)
        print("儲存索引")
        print("=" * 80)
        
        # 儲存 FAISS 索引
        index_path = f'{output_dir}/vector_index.faiss'
        faiss.write_index(index, index_path)
        print(f"✅ FAISS 索引: {index_path}")
        
        # 儲存向量嵌入
        embeddings_path = f'{output_dir}/vector_embeddings.npy'
        np.save(embeddings_path, embeddings)
        print(f"✅ 向量嵌入: {embeddings_path}")
        
        # 儲存 Player IDs
        player_ids_path = f'{output_dir}/vector_player_ids.pkl'
        with open(player_ids_path, 'wb') as f:
            pickle.dump(player_ids, f)
        print(f"✅ Player IDs: {player_ids_path}")
        
        print()
        print("=" * 80)
        print("索引建立完成！")
        print("=" * 80)


def main():
    """主函數"""
    
    # 初始化建立器
    builder = VectorIndexBuilder()
    
    # 建立索引
    index, embeddings, player_ids = builder.build_index('./mlb_datas/text_chunks.json')
    
    # 儲存索引
    builder.save_index(index, embeddings, player_ids)


if __name__ == "__main__":
    main()
