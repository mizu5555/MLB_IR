"""
快速測試 Ollama 連接
用於驗證修復是否成功
"""

def quick_test():
    """快速測試 Ollama"""
    
    print("\n" + "=" * 80)
    print("Ollama 快速測試")
    print("=" * 80)
    
    # 測試 1: 導入
    print("\n1. 測試導入...")
    try:
        import ollama
        print("   ✅ ollama 套件已安裝")
    except ImportError:
        print("   ❌ ollama 套件未安裝")
        print("   請運行: pip install ollama --break-system-packages")
        return False
    
    # 測試 2: 連接
    print("\n2. 測試連接...")
    try:
        models = ollama.list()
        print("   ✅ Ollama 連接成功")
    except Exception as e:
        print(f"   ❌ 連接失敗: {e}")
        return False
    
    # 測試 3: 獲取模型列表
    print("\n3. 獲取模型列表...")
    try:
        # 處理對象和字典兩種情況
        if hasattr(models, 'models'):
            models_list = models.models
            print("   ✅ API 返回對象格式")
        elif isinstance(models, dict):
            models_list = models.get('models', [])
            print("   ✅ API 返回字典格式")
        else:
            print("   ⚠️ 未知格式")
            models_list = []
        
        print(f"   ✅ 找到 {len(models_list)} 個模型")
    except Exception as e:
        print(f"   ❌ 獲取模型失敗: {e}")
        return False
    
    # 測試 4: 顯示模型
    print("\n4. 顯示模型信息...")
    if not models_list:
        print("   ⚠️ 沒有可用模型")
        print("   請運行: ollama pull llama3.2")
        return False
    
    for i, model in enumerate(models_list[:3], 1):
        try:
            # 處理對象和字典
            if hasattr(model, 'model'):
                name = model.model
                size = model.size / (1024**3) if hasattr(model, 'size') else 0
            elif isinstance(model, dict):
                name = model.get('name', model.get('model', 'Unknown'))
                size = model.get('size', 0) / (1024**3)
            else:
                name = str(model)
                size = 0
            
            print(f"   {i}. {name:30s} ({size:.1f} GB)")
        except Exception as e:
            print(f"   ⚠️ 模型 {i} 處理失敗: {e}")
    
    # 測試 5: 獲取第一個模型名稱
    print("\n5. 獲取第一個模型名稱...")
    try:
        first_model = models_list[0]
        
        if hasattr(first_model, 'model'):
            model_name = first_model.model
        elif isinstance(first_model, dict):
            model_name = first_model.get('name', first_model.get('model', 'Unknown'))
        else:
            model_name = str(first_model)
        
        # 移除版本標籤
        if ':' in model_name:
            base_name = model_name.split(':')[0]
        else:
            base_name = model_name
        
        print(f"   ✅ 完整名稱: {model_name}")
        print(f"   ✅ 基礎名稱: {base_name}")
    except Exception as e:
        print(f"   ❌ 獲取模型名稱失敗: {e}")
        return False
    
    # 測試 6: 嘗試調用模型
    print("\n6. 測試模型調用...")
    try:
        print(f"   正在調用 {model_name}...")
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': 'Say hi in one word'}]
        )
        answer = response['message']['content']
        print(f"   ✅ 模型調用成功")
        print(f"   回答: {answer}")
    except Exception as e:
        print(f"   ❌ 模型調用失敗: {e}")
        return False
    
    # 成功
    print("\n" + "=" * 80)
    print("✅ 所有測試通過！Ollama 工作正常！")
    print("=" * 80)
    print(f"\n可用模型: {model_name}")
    print("\n你現在可以運行:")
    print("   python test_rag_ollama.py")
    print("\n" + "=" * 80)
    
    return True


if __name__ == "__main__":
    success = quick_test()
    
    if not success:
        print("\n" + "=" * 80)
        print("⚠️ 測試失敗")
        print("=" * 80)
        print("\n解決方案:")
        print("  1. 確認 Ollama 已安裝並啟動")
        print("  2. 下載模型: ollama pull llama3.2")
        print("  3. 重新運行此測試")
        print("\n或使用模擬模式:")
        print("   python test_rag.py")
        print("=" * 80)
