"""
Ollama 診斷工具
用於檢測和診斷 Ollama 連接問題
"""

import json


def diagnose_ollama():
    """診斷 Ollama 連接"""
    
    print("\n" + "=" * 80)
    print("Ollama 診斷工具")
    print("=" * 80)
    
    # 步驟 1: 檢查 ollama 套件
    print("\n步驟 1: 檢查 ollama 套件")
    print("-" * 80)
    
    try:
        import ollama
        print("✅ ollama 套件已安裝")
        print(f"   版本: {ollama.__version__ if hasattr(ollama, '__version__') else '未知'}")
    except ImportError:
        print("❌ ollama 套件未安裝")
        print("\n解決方案:")
        print("   pip install ollama --break-system-packages")
        return
    
    # 步驟 2: 測試 Ollama 連接
    print("\n步驟 2: 測試 Ollama 連接")
    print("-" * 80)
    
    try:
        models_response = ollama.list()
        print("✅ Ollama 連接成功")
        
        # 顯示原始響應結構
        print("\n原始響應:")
        print(json.dumps(models_response, indent=2, default=str)[:500])
        
    except Exception as e:
        print(f"❌ Ollama 連接失敗: {e}")
        print("\n可能的原因:")
        print("  1. Ollama 服務未啟動")
        print("  2. Ollama 未正確安裝")
        print("\n解決方案:")
        print("  1. 在開始選單搜尋 'Ollama' 並啟動")
        print("  2. 確認系統托盤有 Ollama 圖示")
        print("  3. 重新安裝 Ollama (https://ollama.com)")
        return
    
    # 步驟 3: 檢查可用模型
    print("\n步驟 3: 檢查可用模型")
    print("-" * 80)
    
    try:
        models = models_response.get('models', [])
        
        if not models:
            print("⚠️ 沒有找到任何模型")
            print("\n解決方案:")
            print("   ollama pull llama3.2")
            return
        
        print(f"✅ 找到 {len(models)} 個模型\n")
        
        # 顯示每個模型的詳細信息
        for i, model in enumerate(models, 1):
            print(f"模型 {i}:")
            
            # 嘗試不同的鍵名
            model_name = None
            for key in ['name', 'model', 'id']:
                if key in model:
                    model_name = model[key]
                    break
            
            if model_name:
                print(f"  名稱: {model_name}")
            else:
                print(f"  ⚠️ 無法找到模型名稱")
                print(f"  模型對象: {model}")
            
            # 顯示大小
            if 'size' in model:
                size_gb = model['size'] / (1024**3)
                print(f"  大小: {size_gb:.2f} GB")
            
            print()
        
    except Exception as e:
        print(f"❌ 檢查模型失敗: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 步驟 4: 測試模型調用
    print("\n步驟 4: 測試模型調用")
    print("-" * 80)
    
    # 獲取第一個模型名稱
    first_model = models[0]
    test_model_name = None
    
    for key in ['name', 'model', 'id']:
        if key in first_model:
            test_model_name = first_model[key]
            break
    
    if not test_model_name:
        print("❌ 無法確定模型名稱")
        return
    
    print(f"測試模型: {test_model_name}")
    
    try:
        print("\n發送測試訊息: 'Hello, say hi in one word'")
        
        response = ollama.chat(
            model=test_model_name,
            messages=[
                {'role': 'user', 'content': 'Hello, say hi in one word'}
            ]
        )
        
        print("✅ 模型調用成功")
        print(f"\n回答: {response['message']['content']}")
        
    except Exception as e:
        print(f"❌ 模型調用失敗: {e}")
        print("\n可能的原因:")
        print("  1. 模型未完全下載")
        print("  2. 模型名稱錯誤")
        print("\n解決方案:")
        print(f"   ollama pull {test_model_name}")
        return
    
    # 成功總結
    print("\n" + "=" * 80)
    print("✅ Ollama 診斷完成 - 一切正常！")
    print("=" * 80)
    
    print(f"\n可用的模型名稱: {test_model_name}")
    print("\n你現在可以運行:")
    print(f"   python test_rag_ollama.py")
    
    return test_model_name


if __name__ == "__main__":
    diagnose_ollama()
