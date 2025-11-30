"""
一鍵重建所有數據 - 修復版本
自動識別 year/Season 欄位
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """運行命令並顯示進度"""
    print("\n" + "=" * 80)
    print(description)
    print("=" * 80)
    print(f"執行: {command}\n")
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ 錯誤: {description} 失敗")
        sys.exit(1)
    
    print(f"\n✅ {description} 完成")
    return result.returncode


def main():
    """主流程"""
    
    print("\n" + "=" * 80)
    print("一鍵重建所有數據 - 修復版本")
    print("=" * 80)
    
    # 檢查文件
    print("\n檢查必要文件...")
    
    required_files = {
        './src/datapreprocess/step1_generate_text_chunks_FIXED.py': 'Step 1 腳本',
        './src/datapreprocess/step2_build_vector_index.py': 'Step 2 腳本',
        './src/datapreprocess/step3_build_bm25_index.py': 'Step 3 腳本',
        './data/raw/statcast_batters_enhanced.csv': '打者數據',
    }
    
    missing_files = []
    for file_path, name in required_files.items():
        if Path(file_path).exists():
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ 缺少必要文件:")
        for f in missing_files:
            print(f"  - {f}")
        print(f"\n請確保所有必要文件都在正確位置")
        sys.exit(1)
    
    # 執行重建
    print("\n開始重建數據...")
    
    steps = [
        ("python src/datapreprocess/step1_generate_text_chunks_FIXED.py", "Step 1: 生成文本描述（修復版）"),
        ("python src/datapreprocess/step2_build_vector_index.py", "Step 2: 建立 Vector 索引"),
        ("python src/datapreprocess/step3_build_bm25_index.py", "Step 3: 建立 BM25 索引"),
    ]
    
    for command, description in steps:
        run_command(command, description)
    
    # 驗證結果
    print("\n" + "=" * 80)
    print("驗證生成的文件")
    print("=" * 80)
    
    import json
    import pickle
    
    # 檢查 text_chunks.json
    text_chunks_path = './data/mlb_data/text_chunks.json'
    if Path(text_chunks_path).exists():
        with open(text_chunks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n✅ text_chunks.json: {len(data)} 筆記錄")
        
        # 檢查 Aaron Judge
        aaron_records = [k for k in data.keys() if 'Aaron Judge' in k]
        if aaron_records:
            print(f"✅ 找到 Aaron Judge: {len(aaron_records)} 筆")
            for record in aaron_records:
                print(f"   - {record}")
        else:
            print(f"⚠️ 沒有找到 Aaron Judge")
    
    # 檢查其他文件
    output_files = [
        'vector_index.faiss',
        'vector_embeddings.npy',
        'vector_player_ids.pkl',
        'bm25_index.pkl',
        'bm25_corpus.pkl',
        'bm25_player_ids.pkl'
    ]
    
    for filename in output_files:
        path = Path('./data/mlb_data') / filename
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✅ {filename}: {size_mb:.1f} MB")
        else:
            print(f"❌ {filename}: 不存在")
    
    # 總結
    print("\n" + "=" * 80)
    print("重建完成！")
    print("=" * 80)
    
    print(f"\n下一步:")
    print(f"  1. 調試 BM25: python debug_bm25.py")
    print(f"  2. 測試檢索: python debug_search.py")
    print(f"  3. 快速測試: python quick_test.py")
    print(f"  4. 啟動網站: python src/web/app.py")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
