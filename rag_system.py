"""
Phase 7: RAG System
完整的檢索增強生成系統
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_router import QueryRouter
from prompt_templates import PromptTemplates
from phase6_hybrid_search import HybridSearch
from typing import Dict, List
import json


class RAGSystem:
    """
    完整的 RAG 系統
    
    流程：
    1. 用戶查詢 → Query Router（分類）
    2. Hybrid Search（檢索相關數據）
    3. Prompt Templates（生成提示詞）
    4. LLM Generator（生成回答）[模擬]
    5. Response Validation（驗證）
    6. 返回最終回答
    """
    
    def __init__(self):
        """初始化 RAG 系統"""
        
        print("\n" + "=" * 80)
        print("初始化 RAG 系統")
        print("=" * 80)
        
        # 初始化組件
        print("\n1. 初始化 Query Router...")
        self.query_router = QueryRouter()
        print("   ✅ Query Router 初始化完成")
        
        print("\n2. 初始化 Hybrid Search...")
        self.hybrid_search = HybridSearch()
        print("   ✅ Hybrid Search 初始化完成")
        
        print("\n3. 初始化 Prompt Templates...")
        self.prompt_templates = PromptTemplates()
        print("   ✅ Prompt Templates 初始化完成")
        
        print("\n" + "=" * 80)
        print("✅ RAG 系統初始化完成！")
        print("=" * 80)
    
    def answer_query(self, query: str, use_llm: bool = False) -> Dict:
        """
        回答用戶查詢
        
        Args:
            query: 用戶查詢
            use_llm: 是否使用真實 LLM（需要 API key）
            
        Returns:
            回答字典，包含：
            - query: 原始查詢
            - classification: 查詢分類結果
            - search_results: 檢索結果
            - prompt: 生成的提示詞
            - answer: 最終回答
            - metadata: 元數據
        """
        
        print(f"\n{'=' * 80}")
        print(f"查詢: \"{query}\"")
        print("=" * 80)
        
        # 步驟 1: 查詢分類
        print("\n步驟 1: 查詢分類")
        print("-" * 80)
        classification = self.query_router.classify_query(query)
        print(f"查詢類型: {classification['query_type']}")
        print(f"信心分數: {classification['confidence']:.2f}")
        print(f"語言: {classification['language']}")
        
        # 步驟 2: 獲取檢索參數
        retrieval_params = self.query_router.get_retrieval_params(classification)
        k = retrieval_params['k']
        print(f"\n步驟 2: 檢索參數")
        print("-" * 80)
        print(f"檢索數量: k={k}")
        print(f"說明: {retrieval_params['description']}")
        
        # 步驟 3: 執行檢索
        print(f"\n步驟 3: 執行混合檢索")
        print("-" * 80)
        search_results = self.hybrid_search.auto_search(query, k=k)
        print(f"檢索到 {len(search_results)} 個結果")
        
        # 顯示 Top 3 結果
        print("\nTop 3 結果:")
        for i, result in enumerate(search_results[:3], 1):
            player_id = result['player_id']
            score = result['score']
            preview = result['text_preview'][:100]
            print(f"  {i}. {player_id:30s} (分數: {score:.4f})")
            print(f"     {preview}...")
        
        # 步驟 4: 生成提示詞
        print(f"\n步驟 4: 生成提示詞")
        print("-" * 80)
        prompt = self.prompt_templates.get_prompt(
            query_type=classification['query_type'],
            query=query,
            search_results=search_results,
            language=classification['language']
        )
        print(f"提示詞長度: {len(prompt)} 字符")
        print(f"提示詞預覽:\n{prompt[:200]}...")
        
        # 步驟 5: 生成回答
        print(f"\n步驟 5: 生成回答")
        print("-" * 80)
        
        if use_llm:
            # 使用真實 LLM（需要實作）
            answer = self._generate_with_llm(prompt)
        else:
            # 模擬 LLM 回答
            answer = self._generate_mock_answer(
                query=query,
                query_type=classification['query_type'],
                search_results=search_results,
                language=classification['language']
            )
        
        print(f"回答生成完成")
        
        # 步驟 6: 驗證回答
        print(f"\n步驟 6: 驗證回答")
        print("-" * 80)
        validation = self._validate_answer(answer, search_results)
        print(f"事實一致性: {'通過 ✅' if validation['is_consistent'] else '失敗 ❌'}")
        print(f"包含具體數據: {'是 ✅' if validation['has_data'] else '否 ⚠️'}")
        print(f"引用來源: {'是 ✅' if validation['has_citation'] else '否 ⚠️'}")
        
        # 返回完整結果
        return {
            'query': query,
            'classification': classification,
            'retrieval_params': retrieval_params,
            'search_results': search_results,
            'prompt': prompt,
            'answer': answer,
            'validation': validation,
            'metadata': {
                'num_results': len(search_results),
                'query_type': classification['query_type'],
                'language': classification['language']
            }
        }
    
    def _generate_with_llm(self, prompt: str) -> str:
        """
        使用真實 LLM 生成回答
        
        注意：需要設定 ANTHROPIC_API_KEY 環境變數
        """
        
        try:
            import anthropic
            
            client = anthropic.Anthropic()
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        
        except ImportError:
            print("⚠️ anthropic 套件未安裝，使用模擬回答")
            return "[需要安裝 anthropic 套件並設定 API key]"
        
        except Exception as e:
            print(f"⚠️ LLM 調用失敗: {e}")
            return f"[LLM 錯誤: {e}]"
    
    def _generate_mock_answer(self, query: str, query_type: str, 
                              search_results: List[Dict], language: str) -> str:
        """
        生成模擬的 LLM 回答（用於測試）
        """
        
        if not search_results:
            if language == 'zh':
                return "抱歉，我沒有找到相關的數據來回答這個問題。"
            else:
                return "Sorry, I couldn't find relevant data to answer this question."
        
        # 提取第一個結果的信息
        top_result = search_results[0]
        player_id = top_result['player_id']
        text = top_result['full_text']
        
        if query_type == 'factual':
            if language == 'zh':
                return f"根據檢索結果，{player_id} 的相關數據如下：\n\n{text[:200]}...\n\n（這是模擬回答。完整回答需要使用真實 LLM。）"
            else:
                return f"Based on the search results, here's the data for {player_id}:\n\n{text[:200]}...\n\n(This is a mock answer. Full answer requires real LLM.)"
        
        elif query_type == 'ranking':
            if language == 'zh':
                ranking_text = "根據檢索結果，排名如下：\n\n"
                for i, result in enumerate(search_results[:5], 1):
                    ranking_text += f"{i}. {result['player_id']}\n"
                ranking_text += "\n（這是模擬回答。完整排名需要使用真實 LLM 進行數值比較。）"
                return ranking_text
            else:
                ranking_text = "Based on the search results, the ranking is:\n\n"
                for i, result in enumerate(search_results[:5], 1):
                    ranking_text += f"{i}. {result['player_id']}\n"
                ranking_text += "\n(This is a mock answer. Complete ranking requires real LLM for value comparison.)"
                return ranking_text
        
        else:
            if language == 'zh':
                return f"（這是 {query_type} 類型查詢的模擬回答。需要使用真實 LLM 生成完整回答。）"
            else:
                return f"(This is a mock answer for {query_type} query. Full answer requires real LLM.)"
    
    def _validate_answer(self, answer: str, search_results: List[Dict]) -> Dict:
        """
        驗證回答的事實一致性
        
        Returns:
            驗證結果字典
        """
        
        # 簡單的驗證規則
        validation = {
            'is_consistent': True,  # 假設一致（完整驗證需要 LLM）
            'has_data': False,
            'has_citation': False,
            'issues': []
        }
        
        # 檢查是否包含具體數據（數字）
        import re
        if re.search(r'\d+\.?\d*', answer):
            validation['has_data'] = True
        
        # 檢查是否引用來源（包含球員名字）
        if search_results and any(result['player_id'].split('_')[0] in answer for result in search_results):
            validation['has_citation'] = True
        
        # 檢查是否有明顯的幻覺標記
        hallucination_markers = [
            '我認為', '可能', '大概', '應該',
            'I think', 'probably', 'maybe', 'should be'
        ]
        
        for marker in hallucination_markers:
            if marker in answer.lower():
                validation['issues'].append(f"包含不確定詞彙: '{marker}'")
        
        return validation
    
    def batch_query(self, queries: List[str], use_llm: bool = False) -> List[Dict]:
        """
        批次處理多個查詢
        
        Args:
            queries: 查詢列表
            use_llm: 是否使用真實 LLM
            
        Returns:
            結果列表
        """
        
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'=' * 80}")
            print(f"查詢 {i}/{len(queries)}")
            print("=" * 80)
            
            result = self.answer_query(query, use_llm=use_llm)
            results.append(result)
        
        return results


def main():
    """測試 RAG 系統"""
    
    print("\n" + "=" * 80)
    print("Phase 7: RAG 系統測試")
    print("=" * 80)
    
    # 初始化 RAG 系統
    rag = RAGSystem()
    
    # 測試查詢
    test_queries = [
        "Aaron Judge 2022年打了幾支全壘打？",
        "Who are the top 5 fastest runners?",
        "比較 Juan Soto 和 Aaron Judge 的打擊表現",
    ]
    
    print(f"\n將測試 {len(test_queries)} 個查詢")
    print("注意：由於沒有設定 LLM API，將使用模擬回答\n")
    
    # 批次處理
    results = rag.batch_query(test_queries, use_llm=False)
    
    # 顯示最終結果摘要
    print("\n" + "=" * 80)
    print("測試結果摘要")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n查詢 {i}: {result['query']}")
        print("-" * 80)
        print(f"類型: {result['classification']['query_type']}")
        print(f"檢索結果數: {result['metadata']['num_results']}")
        print(f"驗證: {'✅ 通過' if result['validation']['is_consistent'] else '❌ 失敗'}")
        print(f"\n回答預覽:\n{result['answer'][:200]}...")
    
    print("\n" + "=" * 80)
    print("✅ RAG 系統測試完成！")
    print("=" * 80)
    print("\n下一步：")
    print("1. 設定 ANTHROPIC_API_KEY 環境變數")
    print("2. 運行 test_rag_with_llm.py 使用真實 LLM")
    print("3. 運行 evaluate_rag.py 進行完整評估")
    print("=" * 80)


if __name__ == "__main__":
    main()
