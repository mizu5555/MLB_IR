"""
Phase 6: 建立 BM25 索引
結合傳統關鍵字檢索與向量檢索
"""

import json
import pickle
import time
from typing import List
import re


def load_text_chunks():
    """載入文字描述"""
    
    print("=" * 80)
    print("載入文字描述")
    print("=" * 80)
    
    with open('./mlb_data/week5_text_chunks_enhanced.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查數據結構
    if isinstance(data, list):
        # 已經是列表格式
        text_chunks = data
        print(f"✅ 載入 {len(text_chunks)} 個文字描述（列表格式）")
    elif isinstance(data, dict):
        # 字典格式，轉換為列表
        print(f"⚠️ 檢測到字典格式，正在轉換...")
        text_chunks = []
        for key, value in data.items():
            if isinstance(value, dict):
                # 確保包含必要的欄位
                if 'text_chunk' not in value:
                    value['text_chunk'] = value.get('text', '')
                if 'player_id' not in value:
                    value['player_id'] = key
                text_chunks.append(value)
            elif isinstance(value, str):
                # 如果值是字串，創建標準格式
                text_chunks.append({
                    'player_id': key,
                    'text_chunk': value
                })
        print(f"✅ 轉換完成：{len(text_chunks)} 個文字描述")
    else:
        raise ValueError(f"未知的數據格式: {type(data)}")
    
    # 驗證數據
    if text_chunks and len(text_chunks) > 0:
        sample = text_chunks[0]
        print(f"\n數據格式驗證:")
        print(f"  第一筆數據類型: {type(sample)}")
        if isinstance(sample, dict):
            print(f"  包含的鍵: {list(sample.keys())[:5]}")
        else:
            print(f"  ⚠️ 警告：數據不是字典格式")
    
    return text_chunks


def tokenize(text: str) -> List[str]:
    """
    文字分詞
    
    策略：
    1. 轉小寫
    2. 保留數字和字母
    3. 分割成 tokens
    4. 移除停用詞（可選）
    """
    
    # 轉小寫
    text = text.lower()
    
    # 分詞（保留數字）
    tokens = re.findall(r'\b\w+\b', text)
    
    # 移除太短的詞（可選）
    tokens = [t for t in tokens if len(t) > 1]
    
    return tokens


def build_bm25_index(text_chunks):
    """建立 BM25 索引"""
    
    print("\n" + "=" * 80)
    print("建立 BM25 索引")
    print("=" * 80)
    
    print("\n安裝 rank-bm25...")
    import subprocess
    result = subprocess.run(
        ['pip', 'install', 'rank-bm25', '--break-system-packages', '-q'],
        capture_output=True
    )
    
    if result.returncode == 0:
        print("✅ rank-bm25 安裝成功")
    else:
        print("⚠️ rank-bm25 可能已安裝")
    
    from rank_bm25 import BM25Okapi
    
    print("\n分詞處理...")
    start_time = time.time()
    
    tokenized_corpus = []
    player_ids = []
    
    for i, chunk in enumerate(text_chunks):
        if i % 500 == 0:
            print(f"  進度: {i}/{len(text_chunks)}")
        
        # 確保 chunk 是字典
        if not isinstance(chunk, dict):
            print(f"  ⚠️ 警告：第 {i} 筆數據不是字典格式，跳過")
            continue
        
        # 提取文字
        text = chunk.get('text_chunk', chunk.get('text', ''))
        if not text:
            print(f"  ⚠️ 警告：第 {i} 筆數據沒有文字內容，跳過")
            continue
        
        # 分詞
        tokens = tokenize(text)
        tokenized_corpus.append(tokens)
        
        # 提取 player_id
        player_id = chunk.get('player_id', f'unknown_{i}')
        player_ids.append(player_id)
    
    elapsed = time.time() - start_time
    print(f"✅ 分詞完成 ({elapsed:.1f}s)")
    print(f"   平均 token 數: {sum(len(t) for t in tokenized_corpus) / len(tokenized_corpus):.0f}")
    
    print("\n建立 BM25 索引...")
    start_time = time.time()
    
    bm25 = BM25Okapi(tokenized_corpus)
    
    elapsed = time.time() - start_time
    print(f"✅ BM25 索引建立完成 ({elapsed:.1f}s)")
    
    # 儲存索引
    print("\n儲存索引...")
    
    with open('./mlb_data/week5_bm25_index.pkl', 'wb') as f:
        pickle.dump(bm25, f)
    print("✅ BM25 索引: ./mlb_data/week5_bm25_index.pkl")
    
    with open('./mlb_data/week5_bm25_corpus.pkl', 'wb') as f:
        pickle.dump(tokenized_corpus, f)
    print("✅ 分詞語料: ./mlb_data/week5_bm25_corpus.pkl")
    
    with open('./mlb_data/week5_bm25_player_ids.json', 'w', encoding='utf-8') as f:
        json.dump(player_ids, f, ensure_ascii=False, indent=2)
    print("✅ Player IDs: ./mlb_data/week5_bm25_player_ids.json")
    
    # 測試索引
    print("\n" + "=" * 80)
    print("測試 BM25 索引")
    print("=" * 80)
    
    test_queries = [
        "Aaron Judge home runs",
        "high exit velocity",
        "pitcher strikeout rate"
    ]
    
    for query in test_queries:
        print(f"\n查詢: '{query}'")
        query_tokens = tokenize(query)
        scores = bm25.get_scores(query_tokens)
        
        # 取前 3 名
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
        
        print("  Top 3:")
        for rank, idx in enumerate(top_indices, 1):
            print(f"    {rank}. {player_ids[idx]} (分數: {scores[idx]:.4f})")
    
    print("\n" + "=" * 80)
    print("✅ BM25 索引建立完成！")
    print("=" * 80)
    
    return bm25, tokenized_corpus, player_ids


def main():
    print("\n" + "=" * 80)
    print("Phase 6: 建立 BM25 索引")
    print("=" * 80)
    
    # 載入數據
    text_chunks = load_text_chunks()
    
    # 建立索引
    bm25, tokenized_corpus, player_ids = build_bm25_index(text_chunks)
    
    print("\n完成！")
    print("\n下一步：執行 phase6_hybrid_search.py 進行混合檢索測試")


if __name__ == "__main__":
    main()
