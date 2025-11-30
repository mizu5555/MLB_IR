"""
Phase 5: 步驟 2 - 計算 Embeddings
使用 sentence-transformers 為文字描述生成向量
"""

import json
import pandas as pd
import numpy as np
from typing import List
import time


def load_text_chunks():
    """載入文字描述"""
    
    print("=" * 80)
    print("載入文字描述")
    print("=" * 80)
    
    print("\n載入數據...")
    df = pd.read_csv('./mlb_data/week5_text_chunks_enhanced.csv')
    
    print(f"✅ 載入 {len(df)} 個文字描述")
    print(f"   平均長度: {df['text_chunk'].str.len().mean():.0f} 字符")
    
    return df


def compute_embeddings(df: pd.DataFrame, batch_size: int = 32) -> np.ndarray:
    """
    計算文字描述的 embeddings
    
    Args:
        df: 包含文字描述的 DataFrame
        batch_size: 批次大小
    
    Returns:
        embeddings array
    """
    
    print("\n" + "=" * 80)
    print("計算 Embeddings")
    print("=" * 80)
    
    # 檢查是否安裝 sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("\n❌ 錯誤: 未安裝 sentence-transformers")
        print("\n請執行:")
        print("  pip install sentence-transformers --break-system-packages")
        return None
    
    # 載入模型
    print("\n載入 embedding 模型...")
    print("  模型: all-MiniLM-L6-v2")
    
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ 模型載入成功")
    except Exception as e:
        print(f"❌ 模型載入失敗: {e}")
        return None
    
    # 準備文字
    texts = df['text_chunk'].tolist()
    total = len(texts)
    
    print(f"\n開始計算 embeddings...")
    print(f"  總數量: {total}")
    print(f"  批次大小: {batch_size}")
    print(f"  預計批次數: {(total + batch_size - 1) // batch_size}")
    
    start_time = time.time()
    
    # 計算 embeddings（批次處理）
    try:
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
    except Exception as e:
        print(f"❌ Embedding 計算失敗: {e}")
        return None
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ 完成！")
    print(f"   總時間: {elapsed:.1f}s")
    print(f"   速度: {total/elapsed:.1f} docs/s")
    print(f"   Embedding 維度: {embeddings.shape[1]}")
    
    return embeddings


def save_embeddings(embeddings: np.ndarray, player_ids: List[str]):
    """
    儲存 embeddings
    
    Args:
        embeddings: embeddings array
        player_ids: 球員 ID 列表
    """
    
    print("\n" + "=" * 80)
    print("儲存 Embeddings")
    print("=" * 80)
    
    # 儲存為 numpy array
    npy_file = './mlb_data/week5_embeddings_enhanced.npy'
    np.save(npy_file, embeddings)
    print(f"✅ Embeddings: {npy_file}")
    
    # 儲存 player_ids
    ids_file = './mlb_data/week5_player_ids_enhanced.json'
    with open(ids_file, 'w', encoding='utf-8') as f:
        json.dump(player_ids, f, indent=2, ensure_ascii=False)
    print(f"✅ Player IDs: {ids_file}")
    
    # 統計
    print(f"\n統計:")
    print(f"  數量: {len(embeddings)}")
    print(f"  維度: {embeddings.shape[1]}")
    print(f"  大小: {embeddings.nbytes / 1024 / 1024:.1f} MB")


def verify_embeddings(embeddings: np.ndarray):
    """驗證 embeddings 品質"""
    
    print("\n" + "=" * 80)
    print("驗證 Embeddings")
    print("=" * 80)
    
    # 檢查是否有 NaN 或 Inf
    has_nan = np.isnan(embeddings).any()
    has_inf = np.isinf(embeddings).any()
    
    if has_nan:
        print("⚠️  警告: 發現 NaN 值")
    if has_inf:
        print("⚠️  警告: 發現 Inf 值")
    
    if not has_nan and not has_inf:
        print("✅ 無異常值")
    
    # 統計
    print(f"\n數值統計:")
    print(f"  最小值: {embeddings.min():.4f}")
    print(f"  最大值: {embeddings.max():.4f}")
    print(f"  平均值: {embeddings.mean():.4f}")
    print(f"  標準差: {embeddings.std():.4f}")
    
    # 計算一些相似度範例
    print(f"\n相似度範例:")
    
    # 隨機選 3 對
    n = len(embeddings)
    for i in range(3):
        idx1 = np.random.randint(0, n)
        idx2 = np.random.randint(0, n)
        
        # 計算餘弦相似度
        sim = np.dot(embeddings[idx1], embeddings[idx2]) / (
            np.linalg.norm(embeddings[idx1]) * np.linalg.norm(embeddings[idx2])
        )
        
        print(f"  文檔 {idx1} vs 文檔 {idx2}: {sim:.4f}")


def main():
    """主程式"""
    
    print("=" * 80)
    print("Phase 5: Vector Database 重建 - 步驟 2/3")
    print("=" * 80)
    print("\n計算文字描述的 Embeddings")
    
    # 1. 載入文字描述
    df = load_text_chunks()
    
    if df is None:
        return
    
    # 2. 計算 embeddings
    embeddings = compute_embeddings(df, batch_size=32)
    
    if embeddings is None:
        return
    
    # 3. 儲存
    save_embeddings(embeddings, df['player_id'].tolist())
    
    # 4. 驗證
    verify_embeddings(embeddings)
    
    print("\n" + "=" * 80)
    print("✨ 步驟 2 完成！")
    print("=" * 80)
    print("\n下一步:")
    print("  python phase5_build_index.py  # 建立索引")


if __name__ == "__main__":
    main()
