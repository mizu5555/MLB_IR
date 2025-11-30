"""
步驟 2: 建立 Vector 索引
從 text_chunks.json 生成 Vector 索引
"""

import json
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from pathlib import Path


class VectorIndexBuilder:
    """Vector 索引建立器"""
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        """初始化"""
        print("=" * 80)
        print("步驟 2: Vector 索引建立")
        print("=" * 80)
        print(f"載入模型: {model_name}")
        
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # all-MiniLM-L6-v2 的維度
        
        print(f"✅ 模型載入完成，向量維度: {self.dimension}")
        print()
    
    def build_index(self, text_chunks_path, output_dir='./mlb_datas'):
        """
        建立 FAISS 索引
        
        Args:
            text_chunks_path: text_chunks.json 路徑
            output_dir: 輸出目錄
        """
        print(f"載入文本描述: {text_chunks_path}")
        
        # 載入文本
        with open(text_chunks_path, 'r', encoding='utf-8') as f:
            text_chunks = json.load(f)
        
        player_ids = list(text_chunks.keys())
        texts = list(text_chunks.values())
        
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
        
        # 儲存
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # FAISS 索引
        index_path = f'{output_dir}/vector_index.faiss'
        faiss.write_index(index, index_path)
        print(f"✅ FAISS 索引: {index_path}")
        
        # 向量嵌入
        embeddings_path = f'{output_dir}/vector_embeddings.npy'
        np.save(embeddings_path, embeddings)
        print(f"✅ 向量嵌入: {embeddings_path}")
        
        # Player IDs
        player_ids_path = f'{output_dir}/vector_player_ids.pkl'
        with open(player_ids_path, 'wb') as f:
            pickle.dump(player_ids, f)
        print(f"✅ Player IDs: {player_ids_path}")
        
        print()
        print("=" * 80)
        print("✅ Vector 索引建立完成！")
        print("=" * 80)
        print()


def main():
    """主函數"""
    
    # 初始化
    builder = VectorIndexBuilder()
    
    # 建立索引
    builder.build_index(
        text_chunks_path='./mlb_datas/text_chunks.json',
        output_dir='./mlb_datas'
    )
    
    print(f"下一步: 運行 step3_build_bm25_index.py")


if __name__ == "__main__":
    main()
