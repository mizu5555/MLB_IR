"""
步驟 3: 建立 BM25 索引
從 text_chunks.json 生成 BM25 索引
"""

import json
import pickle
import jieba
from rank_bm25 import BM25Okapi
from pathlib import Path


class BM25IndexBuilder:
    """BM25 索引建立器"""
    
    def __init__(self):
        """初始化"""
        print("=" * 80)
        print("步驟 3: BM25 索引建立")
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
        
        # 英文分詞
        english_tokens = text.split()
        
        # 合併並去重
        tokens = list(set(chinese_tokens + english_tokens))
        
        return tokens
    
    def build_index(self, text_chunks_path, output_dir='./mlb_datas'):
        """
        建立 BM25 索引
        
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
        
        # 儲存
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # BM25 索引
        bm25_path = f'{output_dir}/bm25_index.pkl'
        with open(bm25_path, 'wb') as f:
            pickle.dump(bm25, f)
        print(f"✅ BM25 索引: {bm25_path}")
        
        # 分詞語料
        corpus_path = f'{output_dir}/bm25_corpus.pkl'
        with open(corpus_path, 'wb') as f:
            pickle.dump(corpus, f)
        print(f"✅ 分詞語料: {corpus_path}")
        
        # Player IDs
        player_ids_path = f'{output_dir}/bm25_player_ids.pkl'
        with open(player_ids_path, 'wb') as f:
            pickle.dump(player_ids, f)
        print(f"✅ Player IDs: {player_ids_path}")
        
        print()
        print("=" * 80)
        print("✅ BM25 索引建立完成！")
        print("=" * 80)
        print()


def main():
    """主函數"""
    
    # 初始化
    builder = BM25IndexBuilder()
    
    # 建立索引
    builder.build_index(
        text_chunks_path='./mlb_datas/text_chunks.json',
        output_dir='./mlb_datas'
    )
    
    print("🎉 所有索引建立完成！")


if __name__ == "__main__":
    main()
