"""
混合檢索實作
結合 Vector Search (語意) 與 BM25 (關鍵字)
"""

import json
import pickle
import numpy as np
from typing import List, Tuple, Dict
import re
import os

class HybridSearch:
    """混合檢索系統"""

    def __init__(self):
        """初始化混合檢索系統"""
        FILE_DIR = os.path.dirname(os.path.abspath(__file__))
        DATA_PATH = os.path.join(FILE_DIR, '../../data/mlb_data')
        with open(os.path.join(DATA_PATH, 'text_chunks.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        print("=" * 80)
        print("初始化混合檢索系統")
        print("=" * 80)
        
        # 載入 Vector Search 組件
        print("\n載入 Vector Search 組件...")
        self._load_vector_search(DATA_PATH)
        
        # 載入 BM25 組件
        print("\n載入 BM25 組件...")
        self._load_bm25(DATA_PATH)
        
        # 載入文字描述
        print("\n載入文字描述...")
        with open(os.path.join(DATA_PATH, 'text_chunks.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 處理不同的數據格式並驗證
        self.text_chunks = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # 確保有必要的欄位
                    if 'text_chunk' in item or 'text' in item:
                        if 'text_chunk' not in item:
                            item['text_chunk'] = item.get('text', '')
                        if 'player_id' not in item:
                            item['player_id'] = f"unknown_{len(self.text_chunks)}"
                        self.text_chunks.append(item)
                else:
                    print(f"  ⚠️ 跳過非字典項: {type(item)}")
        
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    if 'text_chunk' not in value:
                        value['text_chunk'] = value.get('text', '')
                    if 'player_id' not in value:
                        value['player_id'] = key
                    self.text_chunks.append(value)
                elif isinstance(value, str):
                    self.text_chunks.append({
                        'player_id': key,
                        'text_chunk': value
                    })
                else:
                    print(f"  ⚠️ 跳過未知格式項: {key} -> {type(value)}")
        
        print(f"✅ 文字描述: {len(self.text_chunks)}")
        
        # 驗證數據
        if self.text_chunks:
            sample = self.text_chunks[0]
            if not isinstance(sample, dict):
                raise ValueError(f"數據驗證失敗: text_chunks 包含非字典元素 {type(sample)}")
            if 'player_id' not in sample or 'text_chunk' not in sample:
                raise ValueError(f"數據驗證失敗: 缺少必要欄位 {list(sample.keys())}")
            
        self.term_mapping = {
            # --- 基礎打擊 ---
            'batting average': 'AVG',
            'average': 'AVG',
            'avg': 'AVG',
            '打擊率': 'AVG',
            
            'home runs': 'HR',
            'hr': 'HR',
            '全壘打': 'HR',
            
            'rbi': 'RBI',
            '打點': 'RBI',
            
            'hits': 'H',
            '安打': 'H',
            
            'obp': 'OBP',
            '上壘率': 'OBP',
            'slg': 'SLG',
            '長打率': 'SLG',
            'ops': 'OPS',
            
            # --- 進階打擊 ---
            'woba': 'wOBA',
            'xwoba': 'xwOBA',
            'wrc+': 'wRC+',
            'wrc': 'wRC+',
            'iso': 'ISO',
            'babip': 'BABIP',
            'war': 'WAR',
            
            # --- Statcast (擊球品質) ---
            'exit velocity': 'EV',
            'exit velo': 'EV',
            'ev': 'EV',
            '出棒速度': 'EV',
            '初速': 'EV',
            'max ev': 'maxEV',
            '極速': 'maxEV',
            
            'launch angle': 'LA',
            'la': 'LA',
            '仰角': 'LA',
            '擊球仰角': 'LA',
            
            'barrel': 'Barrel%',
            'barrel rate': 'Barrel%',
            'barrel%': 'Barrel%',
            '強勁擊球': 'Barrel%',
            
            'hard hit': 'HardHit%',
            'hard hit rate': 'HardHit%',
            'hardhit%': 'HardHit%',
            '強擊球': 'HardHit%',
            
            # --- 投手/三振/保送/跑壘 ---
            'strikeout': 'K%',
            'strikeout rate': 'K%',
            'k%': 'K%',
            '三振': 'K%',
            '三振率': 'K%',
            
            'walk': 'BB%',
            'walk rate': 'BB%',
            'bb%': 'BB%',
            '保送': 'BB%',
            
            'speed': 'Spd',
            'spd': 'Spd',
            '速度': 'Spd',
            '跑速': 'Spd',
            
            'off': 'Off',
            'def': 'Def',
        }
        print("關鍵字映射表已加載 (基於原始 CSV 欄位)")
        print("\n混合檢索系統初始化完成！")
        print("=" * 80)

    def _expand_query(self, query: str) -> str:
        """
        擴展查詢：將自然語言關鍵字轉換為 CSV 欄位名稱
        例如："Judge 三振率" -> "Judge 三振率 K%"
        """
        query_lower = query.lower()
        expanded_terms = []
        
        for key, value in self.term_mapping.items():
            if key in query_lower:
                expanded_terms.append(value)
        
        if expanded_terms:
            # 去重並添加到查詢中
            new_terms = " ".join(set(expanded_terms))
            print(f"  🔍 查詢擴展: '{query}' -> 加上 '{new_terms}'")
            return f"{query} {new_terms}"
        return query
    
    def _load_vector_search(self, data_path: str):
        """載入向量檢索組件"""
        
        import faiss
        from sentence_transformers import SentenceTransformer
        
        # 載入 FAISS 索引
        self.faiss_index = faiss.read_index(os.path.join(data_path, 'vector_index.faiss'))
        print(f"  ✅ FAISS 索引: {self.faiss_index.ntotal} 個向量")
        
        # 載入 embeddings
        self.embeddings = np.load(os.path.join(data_path, 'vector_embeddings.npy'))
        print(f"  ✅ Embeddings: {self.embeddings.shape}")
        
        # 載入 player IDs
        with open(os.path.join(data_path, 'vector_player_ids.json'), 'r', encoding='utf-8') as f:
            self.vector_player_ids = json.load(f)

        print(f"  ✅ Vector Player IDs: {len(self.vector_player_ids)}")
        
        # 載入 embedding 模型
        self.encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print(f"  ✅ Encoder 模型載入")
    
    def _load_bm25(self, data_path: str):
        """載入 BM25 組件"""
        
        # 載入 BM25 索引
        with open(os.path.join(data_path, 'bm25_index.pkl'), 'rb') as f:
            self.bm25 = pickle.load(f)
        print(f"  ✅ BM25 索引載入")
        
        # 載入分詞語料
        with open(os.path.join(data_path, 'bm25_corpus.pkl'), 'rb') as f:
            self.tokenized_corpus = pickle.load(f)
        print(f"  ✅ 分詞語料: {len(self.tokenized_corpus)} 文檔")
        
        # 載入 player IDs
        with open(os.path.join(data_path, 'bm25_player_ids.pkl'), 'rb') as f:
            self.bm25_player_ids = pickle.load(f)
        print(f"  ✅ BM25 Player IDs: {len(self.bm25_player_ids)}")
    
    def tokenize(self, text: str) -> List[str]:
        """分詞（與建立索引時相同）"""
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        tokens = [t for t in tokens if len(t) > 1]
        return tokens
    
    def vector_search(self, query: str, k: int = 100) -> Tuple[List[str], List[float]]:
        """向量檢索"""
        
        # 編碼查詢
        query_embedding = self.encoder.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # 搜尋
        distances, indices = self.faiss_index.search(query_embedding.astype('float32'), k)
        
        # 提取結果
        player_ids = [self.vector_player_ids[idx] for idx in indices[0]]
        scores = distances[0].tolist()
        
        return player_ids, scores
    
    def bm25_search(self, query: str, k: int = 100) -> Tuple[List[str], List[float]]:
        """BM25 檢索"""
        
        # 分詞
        query_tokens = self.tokenize(query)
        
        # 計算分數
        scores = self.bm25.get_scores(query_tokens)
        
        # 排序
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        player_ids = [self.bm25_player_ids[idx] for idx in top_indices]
        top_scores = [scores[idx] for idx in top_indices]
        
        return player_ids, top_scores
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """標準化分數到 [0, 1]"""
        
        if not scores or max(scores) == min(scores):
            return [0.0] * len(scores)
        
        min_score = min(scores)
        max_score = max(scores)
        
        normalized = [(s - min_score) / (max_score - min_score) for s in scores]
        return normalized
    
    def hybrid_search(
        self, 
        query: str, 
        k: int = 5, 
        alpha: float = 0.5,
        player_type: str = None
    ) -> List[Dict]:
        """
        混合檢索
        
        Args:
            query: 查詢字串
            k: 返回結果數量
            alpha: 混合權重 (0=純BM25, 1=純Vector)
            player_type: 過濾球員類型 ('batter' or 'pitcher')
        
        Returns:
            結果列表
        """
        # 擴展查詢
        expanded_query = self._expand_query(query)
        
        # Vector Search
        vector_ids, vector_scores = self.vector_search(expanded_query, k=100)
        vector_scores_norm = self.normalize_scores(vector_scores)
        
        # BM25 Search
        bm25_ids, bm25_scores = self.bm25_search(query, k=100)
        bm25_scores_norm = self.normalize_scores(bm25_scores)
        
        # 合併分數
        combined_scores = {}
        
        # 添加 vector 分數
        for player_id, score in zip(vector_ids, vector_scores_norm):
            combined_scores[player_id] = alpha * score
        
        # 添加 BM25 分數
        for player_id, score in zip(bm25_ids, bm25_scores_norm):
            if player_id in combined_scores:
                combined_scores[player_id] += (1 - alpha) * score
            else:
                combined_scores[player_id] = (1 - alpha) * score
        
        # 球員類型過濾
        if player_type:
            filtered_scores = {}
            for player_id, score in combined_scores.items():
                # 從文字描述中獲取類型
                chunk = None
                for c in self.text_chunks:
                    # 確保 c 是字典且有 player_id
                    if isinstance(c, dict) and c.get('player_id') == player_id:
                        chunk = c
                        break
                
                if chunk:
                    text = chunk.get('text_chunk', chunk.get('text', ''))
                    if player_type == 'batter' and 'Type: batter' in text:
                        filtered_scores[player_id] = score
                    elif player_type == 'pitcher' and 'Type: pitcher' in text:
                        filtered_scores[player_id] = score
            combined_scores = filtered_scores
        
        # 排序
        sorted_results = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:k]
        
        # 構建結果
        results = []
        for player_id, score in sorted_results:
            # 獲取詳細資訊
            chunk = None
            for c in self.text_chunks:
                if isinstance(c, dict) and c.get('player_id') == player_id:
                    chunk = c
                    break
            
            if chunk:
                text_chunk = chunk.get('text_chunk', chunk.get('text', ''))
                results.append({
                    'player_id': player_id,
                    'score': score,
                    'text_preview': text_chunk[:150] + '...' if len(text_chunk) > 150 else text_chunk,
                    'full_text': text_chunk
                })
        
        return results
    
    def auto_search(self, query: str, k: int = 5) -> List[Dict]:
        """
        自動混合檢索
        根據查詢類型自動調整權重
        
        策略：
        1. 如果包含球員全名 → 更多 BM25 權重
        2. 如果是語意描述 → 更多 Vector 權重
        3. 如果包含統計術語 → 混合
        """
        
        query_lower = query.lower()
        
        # 檢測球員類型關鍵字（擴展版 - Phase 6.1）
        batter_keywords = [
            # 基本
            'hitter', 'batter', 'batting', 'hitting',
            # 統計
            'home runs', 'rbi', 'hits', 'doubles', 'triples', 'average',
            # 進階指標
            'exit velocity', 'barrel rate', 'hard hit', 'launch angle',
            'sprint speed', 'runner', 'baserunner', 'stolen bases', 'steal',
            'on base', 'slugging', 'ops', 'woba', 'wrc',
            # 位置
            'outfield', 'infield', 'first base', 'second base', 'shortstop', 'third base',
            'catcher', 'dh', 'designated hitter'
        ]
        
        pitcher_keywords = [
            # 基本
            'pitcher', 'pitching',
            # 統計
            'era', 'whip', 'strikeout', 'walk', 'saves', 'wins', 'losses',
            # 進階指標
            'fip', 'xfip', 'k%', 'bb%', 'hr/9', 'k/9', 'bb/9',
            # 球種
            'fastball', 'slider', 'curveball', 'changeup', 'cutter', 'sinker', 'splitter',
            'velocity', 'spin rate', 'movement',
            # 角色
            'starter', 'reliever', 'closer', 'setup'
        ]
        
        player_type = None
        if any(kw in query_lower for kw in batter_keywords):
            player_type = 'batter'
        elif any(kw in query_lower for kw in pitcher_keywords):
            player_type = 'pitcher'
        
        # 檢測是否包含人名（首字母大寫的連續詞）
        has_proper_name = bool(re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query))
        
        # 檢測是否包含年份
        has_year = bool(re.search(r'\b(2022|2023|2024)\b', query))
        
        # 檢測語意關鍵字（擴展版）
        semantic_keywords = ['high', 'low', 'best', 'good', 'bad', 'fast', 'slow', 'top', 'elite', 'worst', 'fastest', 'highest', 'lowest']
        has_semantic = any(kw in query_lower for kw in semantic_keywords)
        
        # 決定權重（Phase 6.1 優化）
        if has_proper_name and has_year:
            # 精確查詢：Aaron Judge 2022
            # 優化：提高 BM25 權重（0.3 → 0.2）
            alpha = 0.2  # 80% BM25, 20% Vector
        elif has_proper_name:
            # 球員查詢：Aaron Judge
            # 優化：略微提高 BM25 權重（0.4 → 0.35）
            alpha = 0.35  # 65% BM25, 35% Vector
        elif has_semantic:
            # 語意查詢：high exit velocity
            alpha = 0.7  # 30% BM25, 70% Vector
        else:
            # 混合查詢
            alpha = 0.5  # 50-50
        
        print(f"  查詢類型: alpha={alpha:.2f}, player_type={player_type}")
        
        return self.hybrid_search(query, k=k, alpha=alpha, player_type=player_type)


def main():
    """測試混合檢索"""
    
    print("\n" + "=" * 80)
    print("Phase 6: 混合檢索測試")
    print("=" * 80)
    
    # 初始化
    searcher = HybridSearch()
    
    # 測試查詢
    test_queries = [
        ("Aaron Judge home runs 2022", "factual"),
        ("high exit velocity power hitter", "semantic"),
        ("pitcher with high strikeout rate", "semantic"),
        ("Juan Soto batting average", "factual"),
    ]
    
    print("\n" + "=" * 80)
    print("測試查詢")
    print("=" * 80)
    
    for query, query_type in test_queries:
        print(f"\n查詢: '{query}' ({query_type})")
        print("-" * 80)
        
        results = searcher.auto_search(query, k=5)
        
        print("\n  Top 5 結果:")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result['player_id']:30s} (分數: {result['score']:.4f})")
            print(f"       {result['text_preview']}")
    
    print("\n" + "=" * 80)
    print("✅ 測試完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
