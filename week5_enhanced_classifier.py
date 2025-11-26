"""
Week 5: 擴展查詢分類器
在原有 3 種查詢類型基礎上，加入獎項、薪資、Statcast 檢測
"""

import ollama
import json
from typing import Dict, Tuple


class EnhancedQueryClassifier:
    """
    擴展查詢分類器
    
    查詢類型：
    1. Factual - 事實查詢（原有）
    2. Ranking - 排名查詢（原有）
    3. Analysis - 分析查詢（原有）
    4. Award - 獎項查詢 ✨ 新增
    5. Contract - 合約/薪資查詢 ✨ 新增
    6. Statcast - 進階指標查詢 ✨ 新增
    """
    
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        
        # 關鍵字檢測（快速初篩）
        self.award_keywords = [
            'mvp', 'cy young', 'rookie', 'all-star', 'gold glove', 
            'silver slugger', 'award', 'won', 'trophy', 'accolade'
        ]
        
        self.contract_keywords = [
            'salary', 'contract', 'pay', 'money', 'earnings', 
            'compensation', 'deal', 'signing', 'free agent'
        ]
        
        self.statcast_keywords = [
            'exit velocity', 'launch angle', 'sprint speed', 
            'hard hit', 'barrel', 'xba', 'xwoba', 'xslg',
            'expected', 'statcast'
        ]
    
    
    def quick_detect(self, query: str) -> str:
        """
        快速檢測查詢類型（基於關鍵字）
        
        Returns:
            'award' | 'contract' | 'statcast' | 'unknown'
        """
        query_lower = query.lower()
        
        # 檢查獎項關鍵字
        if any(kw in query_lower for kw in self.award_keywords):
            return 'award'
        
        # 檢查合約關鍵字
        if any(kw in query_lower for kw in self.contract_keywords):
            return 'contract'
        
        # 檢查 Statcast 關鍵字
        if any(kw in query_lower for kw in self.statcast_keywords):
            return 'statcast'
        
        return 'unknown'
    
    
    def classify_with_llm(self, query: str) -> Dict:
        """
        使用 LLM 精確分類查詢類型
        
        Returns:
            {
                'type': 'factual' | 'ranking' | 'analysis' | 'award' | 'contract' | 'statcast',
                'confidence': float,
                'reasoning': str
            }
        """
        
        system_prompt = """你是一個 MLB 查詢分類器。

查詢類型定義：

1. **Factual（事實查詢）**：
   - 查詢特定球員的特定統計數據
   - 範例："Aaron Judge's 2023 HR", "What is Ohtani's ERA?"

2. **Ranking（排名查詢）**：
   - 找出統計指標最高/最低的球員
   - 範例："Who has the highest wRC+?", "Top 5 batters by OPS"

3. **Analysis（分析查詢）**：
   - 需要跨賽季分析、趨勢、比較
   - 範例："Why is this closer declining?", "Compare Judge vs Ohtani"

4. **Award（獎項查詢）** ✨：
   - 查詢球員獲獎資訊
   - 範例："Has Aaron Judge won MVP?", "List all awards for Ohtani"

5. **Contract（合約查詢）** ✨：
   - 查詢球員薪資、合約
   - 範例："What is Judge's salary?", "Who has the highest contract?"

6. **Statcast（進階指標查詢）** ✨：
   - 查詢 Statcast 進階數據
   - 範例："What is Judge's exit velocity?", "Show me hard hit %"

請分類以下查詢，並以 JSON 格式回答：
{
    "type": "...",
    "confidence": 0.0-1.0,
    "reasoning": "..."
}"""

        user_prompt = f"查詢：{query}"
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={"temperature": 0.1}
            )
            
            response_text = response['message']['content'].strip()
            
            # 解析 JSON
            # 清理可能的 markdown 包裝
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"LLM 分類失敗: {e}")
            return {
                'type': 'unknown',
                'confidence': 0.0,
                'reasoning': f"分類失敗: {str(e)}"
            }
    
    
    def classify(self, query: str) -> Tuple[str, float]:
        """
        分類查詢類型（混合策略）
        
        策略：
        1. 先用關鍵字快速檢測
        2. 如果檢測到新類型，直接返回
        3. 否則使用 LLM 精確分類
        
        Returns:
            (query_type, confidence)
        """
        
        # 快速檢測
        quick_type = self.quick_detect(query)
        
        if quick_type in ['award', 'contract', 'statcast']:
            return quick_type, 0.9  # 關鍵字匹配的信心度
        
        # LLM 精確分類
        result = self.classify_with_llm(query)
        return result['type'], result.get('confidence', 0.8)


# ============================================
# 測試
# ============================================

if __name__ == "__main__":
    
    classifier = EnhancedQueryClassifier()
    
    test_queries = [
        # 原有類型
        ("What is Aaron Judge's 2023 HR?", "factual"),
        ("Who has the highest wRC+ in 2024?", "ranking"),
        ("Why is this closer declining?", "analysis"),
        
        # 獎項查詢
        ("Has Aaron Judge won MVP?", "award"),
        ("Who won the Cy Young in 2023?", "award"),
        ("List all awards for Shohei Ohtani", "award"),
        
        # 合約查詢
        ("What is Aaron Judge's salary?", "contract"),
        ("Who has the highest salary in MLB?", "contract"),
        ("When does Ohtani's contract expire?", "contract"),
        
        # Statcast 查詢
        ("What is Aaron Judge's exit velocity?", "statcast"),
        ("Who has the fastest sprint speed?", "statcast"),
        ("Show me Judge's barrel percentage", "statcast")
    ]
    
    print("=" * 80)
    print("測試擴展查詢分類器")
    print("=" * 80)
    
    correct = 0
    total = len(test_queries)
    
    for query, expected_type in test_queries:
        predicted_type, confidence = classifier.classify(query)
        is_correct = predicted_type == expected_type
        
        if is_correct:
            correct += 1
        
        status = "✅" if is_correct else "❌"
        print(f"\n{status} {query}")
        print(f"   預期: {expected_type}")
        print(f"   預測: {predicted_type} (信心度: {confidence:.2f})")
    
    print("\n" + "=" * 80)
    print(f"準確率: {correct}/{total} = {correct/total*100:.1f}%")
    print("=" * 80)
