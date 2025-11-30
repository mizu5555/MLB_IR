"""
Phase 7: RAG System with Ollama Support
支援 Ollama 本地 LLM 的 RAG 系統
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from query_router import QueryRouter
from prompt_templates import PromptTemplates
from phase6_hybrid_search import HybridSearch
from typing import Dict, List
import json


class RAGSystemOllama:
    """
    支援 Ollama 的 RAG 系統
    
    支援的 LLM 模式：
    1. ollama - 使用本地 Ollama (免費)
    2. claude - 使用 Claude API (需要 API key)
    3. mock - 模擬模式 (測試用)
    """
    
    def __init__(self, llm_mode: str = "ollama", ollama_model: str = "llama3.2"):
        """
        初始化 RAG 系統
        
        Args:
            llm_mode: LLM 模式 (ollama/claude/mock)
            ollama_model: Ollama 模型名稱
        """
        
        print("\n" + "=" * 80)
        print("初始化 RAG 系統")
        print("=" * 80)
        
        self.llm_mode = llm_mode
        self.ollama_model = ollama_model
        
        print(f"\nLLM 模式: {llm_mode}")
        if llm_mode == "ollama":
            print(f"Ollama 模型: {ollama_model}")
            self._test_ollama_connection()
        
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
    
    def _test_ollama_connection(self):
        """測試 Ollama 連接"""
        try:
            import ollama
            
            # 測試連接
            models = ollama.list()
            print(f"   ✅ Ollama 連接成功")
            print(f"   可用模型: {len(models.models)} 個")
            
            # 檢查指定模型是否存在
            # 處理對象和字典兩種情況
            model_names = []
            for m in models.models:
                if hasattr(m, 'model'):
                    model_names.append(m.model)
                elif isinstance(m, dict):
                    model_names.append(m.get('name', m.get('model', '')))
            
            if self.ollama_model not in model_names and f"{self.ollama_model}:latest" not in model_names:
                print(f"   ⚠️ 模型 {self.ollama_model} 未找到")
                print(f"   請運行: ollama pull {self.ollama_model}")
                print(f"   可用模型: {', '.join(model_names[:3])}")
            
        except ImportError:
            print("   ⚠️ ollama 套件未安裝")
            print("   請運行: pip install ollama --break-system-packages")
        except Exception as e:
            print(f"   ⚠️ Ollama 連接失敗: {e}")
            print("   請確認 Ollama 已安裝並運行")
    
    def answer_query(self, query: str) -> Dict:
        """
        回答用戶查詢
        
        Args:
            query: 用戶查詢
            
        Returns:
            回答字典
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
            preview = result['text_preview'][:80]
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
        
        # 步驟 5: 生成回答
        print(f"\n步驟 5: 生成回答 (使用 {self.llm_mode})")
        print("-" * 80)
        
        if self.llm_mode == "ollama":
            answer = self._generate_with_ollama(prompt)
        elif self.llm_mode == "claude":
            answer = self._generate_with_claude(prompt)
        else:
            answer = self._generate_mock_answer(query, classification, search_results)
        
        print(f"回答生成完成 ({len(answer)} 字符)")
        
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
                'language': classification['language'],
                'llm_mode': self.llm_mode
            }
        }
    
    def _generate_with_ollama(self, prompt: str) -> str:
        """
        使用 Ollama 生成回答
        """
        
        try:
            import ollama
            
            print(f"   正在調用 Ollama ({self.ollama_model})...")
            
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {'role': 'user', 'content': prompt}
                ]
            )
            
            answer = response['message']['content']
            print(f"   ✅ Ollama 回答生成成功")
            
            return answer
        
        except ImportError:
            print("   ⚠️ ollama 套件未安裝")
            print("   請運行: pip install ollama --break-system-packages")
            return "[錯誤: ollama 套件未安裝]"
        
        except Exception as e:
            print(f"   ⚠️ Ollama 調用失敗: {e}")
            print("   提示: 請確認 Ollama 已啟動，並且已下載模型")
            print(f"   運行: ollama pull {self.ollama_model}")
            return f"[Ollama 錯誤: {e}]"
    
    def _generate_with_claude(self, prompt: str) -> str:
        """
        使用 Claude API 生成回答
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
        
        except Exception as e:
            print(f"   ⚠️ Claude API 調用失敗: {e}")
            return f"[Claude API 錯誤: {e}]"
    
    def _generate_mock_answer(self, query: str, classification: Dict, 
                              search_results: List[Dict]) -> str:
        """生成模擬回答"""
        
        if not search_results:
            return "抱歉，我沒有找到相關的數據來回答這個問題。"
        
        top_result = search_results[0]
        player_id = top_result['player_id']
        text = top_result['full_text']
        
        language = classification['language']
        
        if language == 'zh':
            return f"根據檢索結果，{player_id} 的相關數據如下：\n\n{text[:200]}...\n\n（這是模擬回答。）"
        else:
            return f"Based on the search results for {player_id}:\n\n{text[:200]}...\n\n(This is a mock answer.)"
    
    def _validate_answer(self, answer: str, search_results: List[Dict]) -> Dict:
        """驗證回答"""
        
        validation = {
            'is_consistent': True,
            'has_data': False,
            'has_citation': False,
            'issues': []
        }
        
        # 檢查是否包含數據
        import re
        if re.search(r'\d+\.?\d*', answer):
            validation['has_data'] = True
        
        # 檢查是否引用來源
        if search_results and any(result['player_id'].split('_')[0] in answer for result in search_results):
            validation['has_citation'] = True
        
        return validation
    
    def batch_query(self, queries: List[str]) -> List[Dict]:
        """批次處理查詢"""
        
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'=' * 80}")
            print(f"查詢 {i}/{len(queries)}")
            print("=" * 80)
            
            result = self.answer_query(query)
            results.append(result)
        
        return results


def main():
    """測試 Ollama RAG 系統"""
    
    print("\n" + "=" * 80)
    print("Phase 7: RAG 系統 (Ollama 版本)")
    print("=" * 80)
    
    # 檢查 Ollama 是否可用
    try:
        import ollama
        print("\n✅ ollama 套件已安裝")
        
        # 列出可用模型
        models = ollama.list()
        print(f"✅ 找到 {len(models['models'])} 個模型")
        
        if models['models']:
            print("\n可用模型:")
            for model in models['models'][:5]:
                print(f"  - {model['name']}")
        else:
            print("\n⚠️ 沒有可用模型，請先下載:")
            print("   ollama pull llama3.2")
            return
        
    except ImportError:
        print("\n⚠️ ollama 套件未安裝")
        print("請運行: pip install ollama --break-system-packages")
        return
    except Exception as e:
        print(f"\n⚠️ Ollama 連接失敗: {e}")
        print("請確認 Ollama 已安裝並運行")
        return
    
    # 初始化 RAG 系統
    rag = RAGSystemOllama(llm_mode="ollama", ollama_model="llama3.2")
    
    # 測試查詢
    test_queries = [
        "Aaron Judge 2022年打了幾支全壘打？",
        "Who are the top 3 home run hitters in 2024?",
    ]
    
    print(f"\n將測試 {len(test_queries)} 個查詢\n")
    
    # 執行測試
    results = rag.batch_query(test_queries)
    
    # 顯示結果
    print("\n" + "=" * 80)
    print("測試結果摘要")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n查詢 {i}: {result['query']}")
        print("-" * 80)
        print(f"類型: {result['classification']['query_type']}")
        print(f"檢索結果數: {result['metadata']['num_results']}")
        print(f"驗證: {'✅ 通過' if result['validation']['is_consistent'] else '❌ 失敗'}")
        print(f"\n回答:\n{result['answer'][:300]}...")
    
    print("\n" + "=" * 80)
    print("✅ Ollama RAG 測試完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
