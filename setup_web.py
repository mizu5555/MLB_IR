"""
設置 MLB Web Assistant 項目結構
"""

import os
import shutil

def setup_project():
    """設置項目結構"""
    
    print("\n" + "=" * 80)
    print("MLB Team Manager Assistant - 項目設置")
    print("=" * 80)
    
    # 創建 static 目錄
    print("\n創建目錄結構...")
    if not os.path.exists('static'):
        os.makedirs('static')
        print("  ✅ 創建 static/ 目錄")
    else:
        print("  ℹ️  static/ 目錄已存在")
    
    # 檢查必要文件
    print("\n檢查必要文件...")
    
    required_files = {
        'app.py': 'Flask 後端服務器',
        'static/index.html': '網頁界面',
        'query_router.py': '查詢路由器',
        'prompt_templates.py': '提示詞模板',
        'phase6_hybrid_search.py': '混合檢索系統'
    }
    
    missing_files = []
    for file, desc in required_files.items():
        if os.path.exists(file):
            print(f"  ✅ {file:30s} - {desc}")
        else:
            print(f"  ❌ {file:30s} - {desc} (缺失)")
            missing_files.append(file)
    
    if missing_files:
        print("\n⚠️  缺少以下文件:")
        for file in missing_files:
            print(f"     - {file}")
        print("\n請從 /mnt/user-data/outputs/ 下載這些文件。")
        return False
    
    # 檢查數據文件
    print("\n檢查數據文件...")
    data_dir = 'mlb_data'
    
    if not os.path.exists(data_dir):
        print(f"  ❌ {data_dir}/ 目錄不存在")
        return False
    
    data_files = {
        'week5_vector_index.faiss': 'Vector 索引',
        'week5_bm25_index.pkl': 'BM25 索引',
        'week5_text_chunks_enhanced.json': '文字描述'
    }
    
    for file, desc in data_files.items():
        file_path = os.path.join(data_dir, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"  ✅ {file:35s} - {desc} ({size:.1f} MB)")
        else:
            print(f"  ❌ {file:35s} - {desc} (缺失)")
    
    # 檢查依賴
    print("\n檢查 Python 套件...")
    
    packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'numpy': 'NumPy',
        'faiss': 'FAISS',
        'sentence_transformers': 'Sentence Transformers',
        'rank_bm25': 'BM25'
    }
    
    missing_packages = []
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} (未安裝)")
            missing_packages.append(name)
    
    if missing_packages:
        print("\n⚠️  請安裝缺少的套件:")
        print("     pip install flask flask-cors --break-system-packages")
    
    # 檢查 Ollama
    print("\n檢查 Ollama...")
    try:
        import ollama
        models = ollama.list()
        if hasattr(models, 'models') and models.models:
            model = models.models[0]
            model_name = model.model if hasattr(model, 'model') else 'Unknown'
            print(f"  ✅ Ollama 可用")
            print(f"  ✅ 模型: {model_name}")
        else:
            print("  ⚠️  Ollama 已安裝但沒有模型")
            print("     請運行: ollama pull llama3.2")
    except:
        print("  ⚠️  Ollama 不可用（純 RAG 模式仍可使用）")
    
    # 總結
    print("\n" + "=" * 80)
    if not missing_files and not missing_packages:
        print("✅ 所有文件和套件都已就緒！")
        print("=" * 80)
        print("\n準備啟動:")
        print("  python app.py")
        print("\n然後訪問:")
        print("  http://127.0.0.1:5000")
        print("\n" + "=" * 80)
        return True
    else:
        print("⚠️  請解決上述問題後再啟動")
        print("=" * 80)
        return False


if __name__ == "__main__":
    setup_project()
