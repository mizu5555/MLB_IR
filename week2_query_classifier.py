"""
Week 2: Query 分類器
使用 Llama 判斷查詢類型

查詢類型：
1. Factual：詢問特定球員的某個數據
   - 例：「Aaron Judge 2024 wRC+ 是多少？」
   - 策略：Vector Search → 找到球員 → 返回數據

2. Ranking：要求排序或比較
   - 例：「2024 年 wRC+ 最高的打者是誰？」
   - 策略：資料庫排序 → 返回 Top N

3. Analysis：深度分析或解釋
   - 例：「為什麼 Aaron Judge 這麼強？」
   - 策略：多維數據 → LLM 分析
"""

import json
import os
from typing import Dict, Literal

print("=" * 80)
print("Query 分類器測試")
print("=" * 80)

# ============================================
# 配置
# ============================================

# 你可以選擇使用的 LLM
LLM_TYPE = "ollama"  # 可選：ollama, openai, anthropic

# Ollama 配置（本地運行）
OLLAMA_MODEL = "llama3.2"  # 或 llama3, mistral, 等
OLLAMA_BASE_URL = "http://localhost:11434"

print(f"\n配置：")
print(f"  LLM 類型：{LLM_TYPE}")
if LLM_TYPE == "ollama":
    print(f"  Ollama 模型：{OLLAMA_MODEL}")
    print(f"  Ollama URL：{OLLAMA_BASE_URL}")

# ============================================
# Query 分類 Prompt
# ============================================

CLASSIFICATION_PROMPT = """You are a query classifier for a baseball statistics system.

Classify the following query into ONE of these types:

1. **factual**: Query asks for specific data about a specific player
   Examples:
   - "Aaron Judge 2024 wRC+"
   - "What is Shohei Ohtani's ERA?"
   - "How many home runs did Juan Soto hit?"

2. **ranking**: Query asks for top/best/worst players or comparisons
   Examples:
   - "Who has the highest wRC+ in 2024?"
   - "Top 5 pitchers by ERA"
   - "Best hitters this season"

3. **analysis**: Query asks for explanation, reasoning, or deep analysis
   Examples:
   - "Why is Aaron Judge so good?"
   - "Explain Shohei Ohtani's performance"
   - "What makes this pitcher effective?"

Query: "{query}"

CRITICAL: Respond with ONLY ONE WORD: factual, ranking, or analysis
Do not include any explanation or additional text.
"""

# ============================================
# LLM 接口
# ============================================

def call_llm(prompt: str) -> str:
    """
    調用 LLM 生成回答
    支援 Ollama (本地) 和其他 API
    """
    
    if LLM_TYPE == "ollama":
        try:
            import requests
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,  # 確保結果一致
                        "num_predict": 10,   # 只需要一個詞
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['response'].strip()
            else:
                raise Exception(f"Ollama API 錯誤：{response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️  Ollama 調用失敗：{e}")
            print(f"  請確保 Ollama 正在運行：ollama serve")
            print(f"  並已下載模型：ollama pull {OLLAMA_MODEL}")
            raise
    
    elif LLM_TYPE == "openai":
        # OpenAI API 實作（需要 API key）
        try:
            import openai
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  ⚠️  OpenAI API 錯誤：{e}")
            raise
    
    else:
        raise ValueError(f"不支援的 LLM 類型：{LLM_TYPE}")

# ============================================
# Query 分類器
# ============================================

def classify_query(query: str) -> Dict:
    """
    分類查詢類型
    
    Returns:
        {
            'query': str,
            'type': 'factual' | 'ranking' | 'analysis',
            'confidence': float,
            'raw_response': str
        }
    """
    
    print(f"\n查詢：'{query}'")
    print(f"  正在分類...")
    
    # 準備 prompt
    prompt = CLASSIFICATION_PROMPT.format(query=query)
    
    # 調用 LLM
    try:
        raw_response = call_llm(prompt)
        print(f"  LLM 回應：'{raw_response}'")
        
        # 解析回應（提取第一個有效的類型詞）
        response_lower = raw_response.lower().strip()
        
        # 嘗試從回應中找到類型
        query_type = None
        if 'factual' in response_lower:
            query_type = 'factual'
        elif 'ranking' in response_lower:
            query_type = 'ranking'
        elif 'analysis' in response_lower:
            query_type = 'analysis'
        else:
            # Fallback：如果無法判斷，默認為 factual
            print(f"  ⚠️  無法解析回應，使用預設類型 'factual'")
            query_type = 'factual'
        
        result = {
            'query': query,
            'type': query_type,
            'raw_response': raw_response,
            'confidence': 1.0 if query_type else 0.5
        }
        
        print(f"  ✅ 分類結果：{query_type}")
        return result
        
    except Exception as e:
        print(f"  ❌ 分類失敗：{e}")
        # Fallback
        return {
            'query': query,
            'type': 'factual',
            'raw_response': '',
            'confidence': 0.0,
            'error': str(e)
        }

# ============================================
# 測試案例
# ============================================

test_queries = [
    # Factual
    "Aaron Judge 2024 wRC+",
    "What is Shohei Ohtani's ERA in 2024?",
    "How many home runs did Juan Soto hit?",
    
    # Ranking
    "Who has the highest wRC+ in 2024?",
    "Top 5 pitchers by ERA",
    "Best hitters this season",
    "誰是 2024 年最強的打者？",
    
    # Analysis
    "Why is Aaron Judge so good?",
    "Explain Shohei Ohtani's performance",
    "What makes Clayton Kershaw effective?",
    "為什麼 Aaron Judge 壓制力這麼強？",
]

# ============================================
# 執行測試
# ============================================

print("\n" + "=" * 80)
print("開始測試")
print("=" * 80)

results = []

for query in test_queries:
    result = classify_query(query)
    results.append(result)
    print()

# ============================================
# 統計結果
# ============================================

print("\n" + "=" * 80)
print("分類統計")
print("=" * 80)

type_counts = {}
for result in results:
    qtype = result['type']
    type_counts[qtype] = type_counts.get(qtype, 0) + 1

print("\n分類分佈：")
for qtype, count in type_counts.items():
    print(f"  {qtype}: {count} 筆 ({count/len(results)*100:.1f}%)")

# ============================================
# 儲存結果
# ============================================

output_dir = "./mlb_data"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, "query_classification_results.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n💾 結果已儲存：{output_file}")

# ============================================
# 結論
# ============================================

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)

successful = sum(1 for r in results if r.get('confidence', 0) > 0)
print(f"✅ 成功分類：{successful}/{len(results)} ({successful/len(results)*100:.1f}%)")

print("\n📊 分類範例：")
for result in results[:5]:  # 顯示前 5 個
    print(f"  '{result['query'][:40]}...' → {result['type']}")

print("\n🎯 下一步：")
print("  1. 驗證分類準確性")
print("  2. 執行 week2_smart_router.py 建立智能路由")
print("  3. 整合 Vector Search 和資料庫排序")
print("=" * 80)
