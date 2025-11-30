"""
Phase 7: RAG 測試腳本
支援真實 LLM 或模擬回答
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system import RAGSystem
import json


def test_rag_system(use_llm: bool = False):
    """
    測試 RAG 系統
    
    Args:
        use_llm: 是否使用真實 LLM（需要 ANTHROPIC_API_KEY）
    """
    
    print("\n" + "=" * 80)
    print("Phase 7: RAG 系統完整測試")
    print("=" * 80)
    
    if use_llm:
        print("\n模式: 使用真實 LLM")
        print("注意: 需要設定 ANTHROPIC_API_KEY 環境變數")
    else:
        print("\n模式: 使用模擬回答")
        print("注意: 要使用真實 LLM，請設定 use_llm=True 並配置 API key")
    
    # 初始化 RAG 系統
    rag = RAGSystem()
    
    # 測試查詢（涵蓋各種類型）
    test_queries = [
        # Factual 查詢
        {
            'query': "Aaron Judge 2022年打了幾支全壘打？",
            'type': 'factual',
            'language': 'zh',
            'expected': '62支全壘打'
        },
        {
            'query': "What was Juan Soto's batting average in 2024?",
            'type': 'factual',
            'language': 'en'
        },
        {
            'query': "Shohei Ohtani 2023年的ERA是多少？",
            'type': 'factual',
            'language': 'zh'
        },
        
        # Ranking 查詢
        {
            'query': "2024年打擊率前5名球員是誰？",
            'type': 'ranking',
            'language': 'zh'
        },
        {
            'query': "Who are the top 3 fastest runners in 2024?",
            'type': 'ranking',
            'language': 'en'
        },
        {
            'query': "最高出棒初速的5位打者",
            'type': 'ranking',
            'language': 'zh'
        },
        
        # Comparison 查詢
        {
            'query': "比較 Aaron Judge 2022 和 2023 的表現",
            'type': 'comparison',
            'language': 'zh'
        },
        {
            'query': "Juan Soto vs Mookie Betts batting stats",
            'type': 'comparison',
            'language': 'en'
        },
        
        # Analysis 查詢
        {
            'query': "分析 Aaron Judge 這幾年的打擊趨勢",
            'type': 'analysis',
            'language': 'zh'
        },
        {
            'query': "Why is Shohei Ohtani so valuable as a two-way player?",
            'type': 'analysis',
            'language': 'en'
        },
    ]
    
    print(f"\n將測試 {len(test_queries)} 個查詢")
    print("涵蓋類型: Factual, Ranking, Comparison, Analysis")
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
        print("=" * 80)
        
        # 執行查詢
        result = rag.answer_query(query, use_llm=use_llm)
        
        # 檢查分類是否正確
        actual_type = result['classification']['query_type']
        type_correct = (actual_type == expected_type)
        
        print(f"\n分類結果: {actual_type} {'✅' if type_correct else '❌ (預期: ' + expected_type + ')'}")
        
        # 顯示最終回答
        print(f"\n最終回答:")
        print("-" * 80)
        answer = result['answer']
        if len(answer) > 500:
            print(answer[:500] + "...\n[回答過長，已截斷]")
        else:
            print(answer)
        
        # 顯示驗證結果
        validation = result['validation']
        print(f"\n驗證結果:")
        print(f"  事實一致性: {'✅ 通過' if validation['is_consistent'] else '❌ 失敗'}")
        print(f"  包含具體數據: {'✅' if validation['has_data'] else '⚠️ 無'}")
        print(f"  引用來源: {'✅' if validation['has_citation'] else '⚠️ 無'}")
        if validation['issues']:
            print(f"  問題: {', '.join(validation['issues'])}")
        
        # 記錄結果
        results.append({
            'query': query,
            'expected_type': expected_type,
            'actual_type': actual_type,
            'type_correct': type_correct,
            'answer': answer,
            'validation': validation,
            'num_results': result['metadata']['num_results']
        })
    
    # 測試總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    
    type_accuracy = sum(r['type_correct'] for r in results) / len(results)
    consistent_answers = sum(r['validation']['is_consistent'] for r in results)
    answers_with_data = sum(r['validation']['has_data'] for r in results)
    answers_with_citation = sum(r['validation']['has_citation'] for r in results)
    
    print(f"\n查詢分類準確率: {type_accuracy:.1%} ({sum(r['type_correct'] for r in results)}/{len(results)})")
    print(f"事實一致性: {consistent_answers}/{len(results)} ({'✅' if consistent_answers == len(results) else '⚠️'})")
    print(f"包含具體數據: {answers_with_data}/{len(results)} ({'✅' if answers_with_data >= len(results)*0.8 else '⚠️'})")
    print(f"引用來源: {answers_with_citation}/{len(results)} ({'✅' if answers_with_citation >= len(results)*0.8 else '⚠️'})")
    
    # 分類準確率分析
    print(f"\n各類型分類準確率:")
    for query_type in ['factual', 'ranking', 'comparison', 'analysis']:
        type_results = [r for r in results if r['expected_type'] == query_type]
        if type_results:
            type_acc = sum(r['type_correct'] for r in type_results) / len(type_results)
            print(f"  {query_type:12s}: {type_acc:.1%} ({sum(r['type_correct'] for r in type_results)}/{len(type_results)})")
    
    # 儲存結果
    output_file = './mlb_data/rag_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 測試結果已儲存到: {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ RAG 系統測試完成！")
    print("=" * 80)
    
    if not use_llm:
        print("\n💡 提示：要使用真實 LLM 測試，請：")
        print("   1. 設定環境變數: export ANTHROPIC_API_KEY='your-api-key'")
        print("   2. 安裝套件: pip install anthropic --break-system-packages")
        print("   3. 重新運行並設定 use_llm=True")
    
    return results


def main():
    """主函數"""
    
    # 檢查是否有 API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if api_key:
        print("✅ 檢測到 ANTHROPIC_API_KEY")
        use_llm = True
    else:
        print("⚠️ 未檢測到 ANTHROPIC_API_KEY，將使用模擬回答")
        use_llm = False
    
    # 執行測試
    results = test_rag_system(use_llm=use_llm)
    
    return results


if __name__ == "__main__":
    main()
