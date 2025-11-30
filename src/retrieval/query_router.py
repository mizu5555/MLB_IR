"""
Query Router
查詢分類器：將用戶查詢分類為不同類型，以使用不同的處理策略
"""

import re
from typing import Dict, List, Tuple


class QueryRouter:
    """
    查詢路由器：分析用戶查詢並分類
    
    查詢類型：
    1. Factual - 事實查詢：查詢特定球員的具體數據
       例如："Aaron Judge 2022年打了幾支全壘打？"
    
    2. Ranking - 排名查詢：需要排序和比較
       例如："2023年打擊率前5名球員"
    
    3. Comparison - 比較查詢：比較多個球員
       例如："比較 Shohei Ohtani 和 Aaron Judge 的表現"
    
    4. Analysis - 分析查詢：需要深入分析和解釋
       例如："分析 Juan Soto 的打擊趨勢"
    """
    
    def __init__(self):
        """初始化查詢路由器"""
        
        # Factual 查詢關鍵字
        self.factual_keywords = [
            # 疑問詞
            '多少', '幾', '什麼', '哪', '誰',
            'how many', 'how much', 'what', 'who', 'which',
            
            # 具體數據
            '數據', '統計', '成績', 'stats', 'statistics', 'data',
            
            # 年份（通常是查詢特定年份數據）
            '2022', '2023', '2024', '2025'
        ]
        
        # Ranking 查詢關鍵字
        self.ranking_keywords = [
            # 排名
            '前', '最', '排名', '名單', '領先',
            'top', 'best', 'worst', 'ranking', 'list', 'leader',
            
            # 比較級
            '最高', '最低', '最快', '最慢', '最多', '最少',
            'highest', 'lowest', 'fastest', 'slowest', 'most', 'least',
            
            # 數字（top 5, 前10名）
            'top 5', 'top 10', '前5', '前10'
        ]
        
        # Comparison 查詢關鍵字
        self.comparison_keywords = [
            # 比較詞
            '比較', '對比', '差異', 'vs', 'versus',
            'compare', 'comparison', 'difference', 'between',
            
            # 連接詞
            '和', '與', '還是', 
            'and', 'or'
        ]
        
        # Analysis 查詢關鍵字
        self.analysis_keywords = [
            # 分析詞
            '分析', '評估', '解釋', '為什麼', '原因',
            'analyze', 'analysis', 'evaluate', 'explain', 'why', 'reason',
            
            # 趨勢
            '趨勢', '變化', '進步', '退步', '發展',
            'trend', 'change', 'improve', 'decline', 'development',
            
            # 深度詞
            '如何', '怎麼', '優勢', '劣勢', '特點',
            'how', 'strength', 'weakness', 'characteristic'
        ]
    
    def classify_query(self, query: str) -> Dict[str, any]:
        """
        分類查詢
        
        Args:
            query: 用戶查詢文字
            
        Returns:
            分類結果字典，包含：
            - query_type: 查詢類型
            - confidence: 信心分數 (0-1)
            - detected_keywords: 檢測到的關鍵字
            - has_player_name: 是否包含球員名字
            - has_year: 是否包含年份
            - language: 語言 (zh/en)
        """
        
        query_lower = query.lower()
        
        # 檢測語言
        language = 'zh' if self._has_chinese(query) else 'en'
        
        # 檢測球員名字（首字母大寫的連續詞）
        has_player_name = bool(re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query))
        
        # 檢測年份
        has_year = bool(re.search(r'\b(2022|2023|2024|2025)\b', query))
        
        # 計算每種類型的匹配分數
        scores = {
            'factual': self._count_matches(query_lower, self.factual_keywords),
            'ranking': self._count_matches(query_lower, self.ranking_keywords),
            'comparison': self._count_matches(query_lower, self.comparison_keywords),
            'analysis': self._count_matches(query_lower, self.analysis_keywords)
        }
        
        # 特殊規則調整分數
        
        # 如果包含球員名字 + 年份 → 很可能是 Factual
        if has_player_name and has_year:
            scores['factual'] += 2
        
        # 如果包含多個球員名字 → 可能是 Comparison
        player_names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query)
        if len(player_names) >= 2:
            scores['comparison'] += 2
        
        # 如果包含 "vs" 或 "和" → 很可能是 Comparison
        if re.search(r'\bvs\b|versus|和.*比', query_lower):
            scores['comparison'] += 3
        
        # 如果包含 "top N" 或 "前N" → 很可能是 Ranking
        if re.search(r'top\s*\d+|前\s*\d+', query_lower):
            scores['ranking'] += 3
        
        # 決定查詢類型
        max_score = max(scores.values())
        
        if max_score == 0:
            # 沒有明確關鍵字，默認為 Factual
            query_type = 'factual'
            confidence = 0.5
        else:
            # 選擇分數最高的類型
            query_type = max(scores, key=scores.get)
            confidence = min(max_score / 5.0, 1.0)  # 標準化到 0-1
        
        # 檢測到的關鍵字
        detected_keywords = self._get_matched_keywords(query_lower, query_type)
        
        return {
            'query_type': query_type,
            'confidence': confidence,
            'detected_keywords': detected_keywords,
            'has_player_name': has_player_name,
            'has_year': has_year,
            'language': language,
            'scores': scores  # 用於調試
        }
    
    def _has_chinese(self, text: str) -> bool:
        """檢測文字是否包含中文"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    def _count_matches(self, text: str, keywords: List[str]) -> int:
        """計算文字中匹配的關鍵字數量"""
        count = 0
        for keyword in keywords:
            if keyword in text:
                count += 1
        return count
    
    def _get_matched_keywords(self, text: str, query_type: str) -> List[str]:
        """獲取匹配的關鍵字列表"""
        if query_type == 'factual':
            keywords = self.factual_keywords
        elif query_type == 'ranking':
            keywords = self.ranking_keywords
        elif query_type == 'comparison':
            keywords = self.comparison_keywords
        else:  # analysis
            keywords = self.analysis_keywords
        
        matched = [kw for kw in keywords if kw in text]
        return matched[:5]  # 最多返回5個
    
    def get_retrieval_params(self, classification: Dict) -> Dict:
        """
        根據查詢類型返回建議的檢索參數
        
        Args:
            classification: classify_query 的返回結果
            
        Returns:
            檢索參數字典
        """
        
        query_type = classification['query_type']
        
        if query_type == 'factual':
            # Factual 查詢：返回少量精確結果
            return {
                'k': 5,
                'description': '事實查詢，需要精確的特定數據'
            }
        
        elif query_type == 'ranking':
            # Ranking 查詢：需要更多結果用於排序
            return {
                'k': 10,
                'description': '排名查詢，需要較多結果進行排序'
            }
        
        elif query_type == 'comparison':
            # Comparison 查詢：需要多個球員的數據
            return {
                'k': 8,
                'description': '比較查詢，需要多個球員的數據'
            }
        
        else:  # analysis
            # Analysis 查詢：需要全面的數據
            return {
                'k': 10,
                'description': '分析查詢，需要全面的背景數據'
            }


def main():
    """測試 Query Router"""
    
    print("=" * 80)
    print("Phase 7: Query Router 測試")
    print("=" * 80)
    
    router = QueryRouter()
    
    # 測試查詢
    test_queries = [
        # Factual
        "Aaron Judge 2022年打了幾支全壘打？",
        "What was Juan Soto's batting average in 2024?",
        "Shohei Ohtani 的 ERA 是多少？",
        
        # Ranking
        "2023年打擊率前5名球員",
        "Who are the top 10 pitchers by strikeout rate?",
        "最快的跑者是誰？",
        
        # Comparison
        "比較 Aaron Judge 和 Shohei Ohtani 的表現",
        "Juan Soto vs Mookie Betts batting stats",
        "Gerrit Cole 和 Jacob deGrom 誰更好？",
        
        # Analysis
        "分析 Aaron Judge 的打擊趨勢",
        "Why is Shohei Ohtani so valuable?",
        "評估 Dodgers 的投手陣容"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n查詢 {i}: \"{query}\"")
        print("-" * 80)
        
        result = router.classify_query(query)
        params = router.get_retrieval_params(result)
        
        print(f"類型: {result['query_type']}")
        print(f"信心: {result['confidence']:.2f}")
        print(f"語言: {result['language']}")
        print(f"包含球員名: {result['has_player_name']}")
        print(f"包含年份: {result['has_year']}")
        print(f"關鍵字: {', '.join(result['detected_keywords'][:3])}")
        print(f"建議檢索數量: k={params['k']}")
        print(f"說明: {params['description']}")
    
    print("\n" + "=" * 80)
    print("✅ Query Router 測試完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
