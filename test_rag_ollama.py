"""
Phase 7: Ollama RAG 測試腳本
使用本地 Ollama 進行完整測試
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system_ollama import RAGSystemOllama
import json


def test_ollama_rag():
    """測試 Ollama RAG 系統"""
    
    print("\n" + "=" * 80)
    print("Phase 7: Ollama RAG 完整測試")
    print("=" * 80)
    
    # 檢查 Ollama
    print("\n檢查 Ollama 環境...")
    print("-" * 80)
    
    try:
        import ollama
        print("✅ ollama 套件已安裝")
        
        # 測試連接
        models = ollama.list()
        print(f"✅ Ollama 連接成功")
        
        # 處理對象和字典兩種情況
        if hasattr(models, 'models'):
            models_list = models.models
        elif isinstance(models, dict):
            models_list = models.get('models', [])
        else:
            models_list = []
        
        print(f"✅ 找到 {len(models_list)} 個模型")
        
        if not models_list:
            print("\n⚠️ 沒有可用模型！")
            print("\n請下載模型:")
            print("  ollama pull llama3.2        # 小模型 (3B, 快速)")
            print("  ollama pull llama3.1:8b     # 中型模型 (8B, 質量更好)")
            return
        
        print("\n可用模型:")
        for i, model in enumerate(models_list[:5], 1):
            # 處理對象和字典兩種情況
            if hasattr(model, 'model'):
                name = model.model
                size = model.size / (1024**3) if hasattr(model, 'size') else 0
            elif isinstance(model, dict):
                name = model.get('name', model.get('model', 'Unknown'))
                size = model.get('size', 0) / (1024**3)
            else:
                name = str(model)
                size = 0
            print(f"  {i}. {name:30s} ({size:.1f} GB)")
        
        # 選擇模型
        first_model = models_list[0]
        if hasattr(first_model, 'model'):
            model_name = first_model.model
        elif isinstance(first_model, dict):
            model_name = first_model.get('name', first_model.get('model', 'llama3.2'))
        else:
            model_name = str(first_model)
        
        # 移除版本標籤（如果有）
        if ':' in model_name:
            model_name = model_name.split(':')[0]
        
        print(f"\n將使用模型: {model_name}")
        
    except ImportError:
        print("❌ ollama 套件未安裝")
        print("\n請安裝:")
        print("  pip install ollama --break-system-packages")
        return
    
    except Exception as e:
        print(f"❌ Ollama 連接失敗: {e}")
        print("\n請確認:")
        print("  1. Ollama 已安裝 (https://ollama.com)")
        print("  2. Ollama 服務已啟動")
        print("  3. 已下載至少一個模型 (ollama pull llama3.2)")
        return
    
    # 初始化 RAG 系統
    print("\n" + "=" * 80)
    print("初始化 RAG 系統")
    print("=" * 80)
    
    rag = RAGSystemOllama(llm_mode="ollama", ollama_model=model_name)
    
    # 測試查詢（精選幾個代表性的）
    test_queries = [
        # Factual - 中文
        {
            'query': "Aaron Judge 2022年打了幾支全壘打？",
            'type': 'factual',
            'language': 'zh',
            'expected': '應該回答 62 支全壘打'
        },
        
        # Factual - 英文
        {
            'query': "What was Juan Soto's batting average in 2024?",
            'type': 'factual',
            'language': 'en',
            'expected': '應該包含具體的打擊率數值'
        },
        
        # Ranking - 中文
        {
            'query': "誰是2024年跑最快的5位球員？",
            'type': 'ranking',
            'language': 'zh',
            'expected': '應該列出排名和 sprint speed 數據'
        },
        
        # Comparison - 英文
        {
            'query': "Compare Aaron Judge 2022 and 2023 performance",
            'type': 'comparison',
            'language': 'en',
            'expected': '應該比較兩個賽季的關鍵指標'
        },
    ]
    
    print(f"\n將測試 {len(test_queries)} 個查詢")
    print("涵蓋類型: Factual, Ranking, Comparison")
    print("語言: 中文、英文\n")
    
    # 執行測試
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case['query']
        expected_type = test_case['type']
        
        print(f"\n{'=' * 80}")
        print(f"測試 {i}/{len(test_queries)}")
        print(f"查詢: \"{query}\"")
        print(f"預期類型: {expected_type}")
        print(f"預期回答: {test_case['expected']}")
        print("=" * 80)
        
        # 執行查詢
        result = rag.answer_query(query)
        
        # 檢查分類
        actual_type = result['classification']['query_type']
        type_correct = (actual_type == expected_type)
        
        print(f"\n分類結果: {actual_type} {'✅' if type_correct else '❌ (預期: ' + expected_type + ')'}")
        
        # 顯示最終回答
        print(f"\n" + "=" * 80)
        print("最終回答 (來自 Ollama)")
        print("=" * 80)
        answer = result['answer']
        print(answer)
        print("=" * 80)
        
        # 顯示驗證結果
        validation = result['validation']
        print(f"\n驗證結果:")
        print(f"  事實一致性: {'✅ 通過' if validation['is_consistent'] else '❌ 失敗'}")
        print(f"  包含具體數據: {'✅' if validation['has_data'] else '⚠️ 無'}")
        print(f"  引用來源: {'✅' if validation['has_citation'] else '⚠️ 無'}")
        
        # 記錄結果
        results.append({
            'query': query,
            'expected_type': expected_type,
            'actual_type': actual_type,
            'type_correct': type_correct,
            'answer': answer,
            'validation': validation,
            'answer_length': len(answer)
        })
    
    # 測試總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    
    type_accuracy = sum(r['type_correct'] for r in results) / len(results)
    consistent_answers = sum(r['validation']['is_consistent'] for r in results)
    answers_with_data = sum(r['validation']['has_data'] for r in results)
    answers_with_citation = sum(r['validation']['has_citation'] for r in results)
    avg_length = sum(r['answer_length'] for r in results) / len(results)
    
    print(f"\n查詢分類準確率: {type_accuracy:.1%} ({sum(r['type_correct'] for r in results)}/{len(results)})")
    print(f"事實一致性: {consistent_answers}/{len(results)} ({'✅' if consistent_answers == len(results) else '⚠️'})")
    print(f"包含具體數據: {answers_with_data}/{len(results)} ({'✅' if answers_with_data >= len(results)*0.8 else '⚠️'})")
    print(f"引用來源: {answers_with_citation}/{len(results)} ({'✅' if answers_with_citation >= len(results)*0.8 else '⚠️'})")
    print(f"平均回答長度: {avg_length:.0f} 字符")
    
    # 儲存結果
    output_file = './mlb_data/ollama_rag_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 測試結果已儲存到: {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ Ollama RAG 測試完成！")
    print("=" * 80)
    
    print("\n💡 結果分析:")
    print(f"  - 使用模型: {model_name}")
    print(f"  - 分類準確率: {type_accuracy:.1%}")
    print(f"  - 回答質量: 查看上方的實際回答")
    print(f"  - 與模擬模式的差異: Ollama 提供了真實的自然語言回答")
    
    return results


def main():
    """主函數"""
    
    results = test_ollama_rag()
    
    if results:
        print("\n🎉 測試成功！你現在有真實的 LLM 回答了！")
        print("\n下一步:")
        print("  1. 查看 ./mlb_data/ollama_rag_test_results.json")
        print("  2. 比較 Ollama 回答 vs 模擬回答的差異")
        print("  3. 在報告中使用這些真實的回答作為展示")


if __name__ == "__main__":
    main()
