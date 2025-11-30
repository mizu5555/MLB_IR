"""
BM25 索引建立模組
使用 rank-bm25 建立關鍵字檢索索引
"""

import json
import pickle
import jieba
from rank_bm25 import BM25Okapi


class BM25IndexBuilder:
    """BM25 索引建立器"""
    
    def __init__(self):
        """初始化"""
        print("=" * 80)
        print("初始化 BM25 索引建立器")
        print("=" * 80)
        print("✅ BM25 索引建立器初始化完成")
        print()
    
    def tokenize(self, text):
        """
        分詞
        
        Args:
            text: 文本
        
        Returns:
            tokens: 分詞結果
        """
        # 中文分詞
        chinese_tokens = jieba.lcut(text)
        
        # 英文分詞（簡單空格分割）
        english_tokens = text.split()
        
        # 合併並去重
        tokens = list(set(chinese_tokens + english_tokens))
        
        return tokens
    
    def build_index(self, text_chunks_path):
        """
        建立 BM25 索引
        
        Args:
            text_chunks_path: 文本描述 JSON 文件路徑
        
        Returns:
            bm25: BM25 索引
            corpus: 分詞語料
            player_ids: Player IDs 列表
        """
        print("=" * 80)
        print("建立 BM25 索引")
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
        
        # 分詞
        print("進行分詞...")
        corpus = []
        for i, text in enumerate(texts):
            if (i + 1) % 1000 == 0:
                print(f"  處理進度: {i + 1}/{len(texts)}")
            tokens = self.tokenize(text)
            corpus.append(tokens)
        
        print(f"✅ 分詞完成，共 {len(corpus)} 個文檔")
        print()
        
        # 建立 BM25 索引
        print("建立 BM25 索引...")
        bm25 = BM25Okapi(corpus)
        
        print(f"✅ BM25 索引建立完成")
        print(f"   索引大小: {len(corpus)} 個文檔")
        print()
        
        return bm25, corpus, player_ids
    
    def save_index(self, bm25, corpus, player_ids, output_dir='./mlb_datas'):
        """
        儲存索引
        
        Args:
            bm25: BM25 索引
            corpus: 分詞語料
            player_ids: Player IDs 列表
            output_dir: 輸出目錄
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print("=" * 80)
        print("儲存索引")
        print("=" * 80)
        
        # 儲存 BM25 索引
        bm25_path = f'{output_dir}/bm25_index.pkl'
        with open(bm25_path, 'wb') as f:
            pickle.dump(bm25, f)
        print(f"✅ BM25 索引: {bm25_path}")
        
        # 儲存語料
        corpus_path = f'{output_dir}/bm25_corpus.pkl'
        with open(corpus_path, 'wb') as f:
            pickle.dump(corpus, f)
        print(f"✅ 分詞語料: {corpus_path}")
        
        # 儲存 Player IDs
        player_ids_path = f'{output_dir}/bm25_player_ids.pkl'
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
    builder = BM25IndexBuilder()
    
    # 建立索引
    bm25, corpus, player_ids = builder.build_index('./mlb_datas/text_chunks.json')
    
    # 儲存索引
    builder.save_index(bm25, corpus, player_ids)


if __name__ == "__main__":
    main()
