"""
主腳本：一鍵重建所有數據
從原始 CSV 到完整索引，自動化執行所有步驟
"""

import sys
import os
from pathlib import Path
import subprocess


def print_header(title):
    """打印標題"""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def check_csv_files(batters_csv, pitchers_csv):
    """檢查 CSV 文件是否存在"""
    print_header("檢查原始數據文件")
    
    files_ok = True
    
    if Path(batters_csv).exists():
        print(f"✅ 找到打者數據: {batters_csv}")
    else:
        print(f"❌ 找不到打者數據: {batters_csv}")
        files_ok = False
    
    if Path(pitchers_csv).exists():
        print(f"✅ 找到投手數據: {pitchers_csv}")
    else:
        print(f"⚠️  找不到投手數據: {pitchers_csv} (可選)")
    
    return files_ok


def run_step(step_name, script_path):
    """運行步驟"""
    print_header(f"執行: {step_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False
        )
        print(f"✅ {step_name} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {step_name} 失敗: {e}")
        return False


def verify_output_files(output_dir):
    """驗證輸出文件"""
    print_header("驗證輸出文件")
    
    required_files = [
        'text_chunks.json',
        'vector_index.faiss',
        'vector_embeddings.npy',
        'vector_player_ids.pkl',
        'bm25_index.pkl',
        'bm25_corpus.pkl',
        'bm25_player_ids.pkl'
    ]
    
    all_ok = True
    
    for filename in required_files:
        filepath = Path(output_dir) / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✅ {filename:35s} ({size_mb:.1f} MB)")
        else:
            print(f"❌ {filename:35s} (不存在)")
            all_ok = False
    
    return all_ok


def main():
    """主函數"""
    
    print()
    print("=" * 80)
    print("  MLB Team Manager Assistant - 數據重建工具")
    print("  從原始 CSV 重建所有索引文件")
    print("=" * 80)
    
    # 配置
    batters_csv = './mlb_data/statcast_batters_enhanced.csv'
    pitchers_csv = './mlb_data/statcast_pitchers_enhanced.csv'
    output_dir = './mlb_datas'
    
    # 檢查原始文件
    if not check_csv_files(batters_csv, pitchers_csv):
        print()
        print("❌ 缺少必要的原始數據文件")
        print()
        print("請確認以下文件存在:")
        print(f"  - {batters_csv}")
        print(f"  - {pitchers_csv} (可選)")
        print()
        print("如果文件名不同，請編輯本腳本修改配置。")
        return
    
    # 創建輸出目錄
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"\n✅ 輸出目錄: {output_dir}\n")
    
    # 執行步驟
    steps = [
        ("步驟 1: 生成文本描述", "step1_generate_text_chunks.py"),
        ("步驟 2: 建立 Vector 索引", "step2_build_vector_index.py"),
        ("步驟 3: 建立 BM25 索引", "step3_build_bm25_index.py"),
    ]
    
    for step_name, script_path in steps:
        if not run_step(step_name, script_path):
            print()
            print(f"❌ 重建過程在 {step_name} 失敗")
            print("請檢查錯誤信息並修復問題後重試")
            return
    
    # 驗證輸出
    if verify_output_files(output_dir):
        print()
        print("=" * 80)
        print("  🎉 所有數據重建完成！")
        print("=" * 80)
        print()
        print("生成的文件:")
        print(f"  📁 {output_dir}/")
        print(f"     ├── text_chunks.json           (文本描述)")
        print(f"     ├── vector_index.faiss         (Vector 索引)")
        print(f"     ├── vector_embeddings.npy      (向量嵌入)")
        print(f"     ├── vector_player_ids.pkl      (Vector Player IDs)")
        print(f"     ├── bm25_index.pkl             (BM25 索引)")
        print(f"     ├── bm25_corpus.pkl            (BM25 語料)")
        print(f"     └── bm25_player_ids.pkl        (BM25 Player IDs)")
        print()
        print("下一步:")
        print("  1. 將這些文件保留在 mlb_datas/ 目錄")
        print("  2. 運行 python src/web/app.py 啟動系統")
        print("  3. 訪問 http://127.0.0.1:5000")
        print()
    else:
        print()
        print("⚠️  部分文件未能成功生成")
        print("請檢查上述錯誤信息")


if __name__ == "__main__":
    main()
