"""
MLB Team Manager Assistant - 評估測試腳本
使用標準測試集評估系統性能
"""

import sys
import os
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

class PerformanceEvaluator:
    """性能評估器"""
    
    def __init__(self):
        """初始化評估器"""
        print("\n" + "=" * 80)
        print("MLB Team Manager Assistant - 性能評估")
        print("=" * 80)
        
        # 載入系統
        from src.retrieval.hybrid_search import HybridSearch
        from src.retrieval.query_router import QueryRouter
        
        self.searcher = HybridSearch()
        self.router = QueryRouter()
        
        # 測試集
        self.test_queries = [
            # Factual 查詢
            {
                'query': 'Aaron Judge 2022年的 wOBA 是多少？',
                'type': 'factual',
                'language': 'zh',
                'expected_player': 'Aaron Judge_2022',
                'expected_stat': 'wOBA'
            },
            {
                'query': 'What was Aaron Judge\'s wRC+ in 2022?',
                'type': 'factual',
                'language': 'en',
                'expected_player': 'Aaron Judge_2022',
                'expected_stat': 'wRC+'
            },
            {
                'query': 'Aaron Judge 2022年的 WAR 是多少？',
                'type': 'factual',
                'language': 'zh',
                'expected_player': 'Aaron Judge_2022',
                'expected_stat': 'WAR'
            },
            
            # Ranking 查詢
            {
                'query': '2022年 wRC+ 最高的球員',
                'type': 'ranking',
                'language': 'zh',
                'expected_player': None  # 任何高 wRC+ 球員
            },
            {
                'query': 'Who had the highest WAR in 2022?',
                'type': 'ranking',
                'language': 'en',
                'expected_player': None
            },
            
            # Comparison 查詢
            {
                'query': '比較 Aaron Judge 2022 和 2023 的表現',
                'type': 'comparison',
                'language': 'zh',
                'expected_player': 'Aaron Judge'
            },
            
            # Analysis 查詢
            {
                'query': '分析 Aaron Judge 2022年的打擊表現',
                'type': 'analysis',
                'language': 'zh',
                'expected_player': 'Aaron Judge_2022'
            },
        ]
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'total_queries': len(self.test_queries),
            'classification_accuracy': 0,
            'recall_at_5': 0,
            'recall_at_10': 0,
            'mrr': 0,
            'details': []
        }
    
    def evaluate(self):
        """執行評估"""
        
        print("\n" + "=" * 80)
        print("開始評估")
        print("=" * 80)
        
        correct_classifications = 0
        recall_5_count = 0
        recall_10_count = 0
        reciprocal_ranks = []
        
        for i, test_case in enumerate(self.test_queries, 1):
            print(f"\n[{i}/{len(self.test_queries)}] 查詢: {test_case['query']}")
            print("-" * 80)
            
            # 1. 測試查詢分類
            classification = self.router.classify_query(test_case['query'])
            
            type_correct = classification['query_type'] == test_case['type']
            lang_correct = classification['language'] == test_case['language']
            
            if type_correct and lang_correct:
                correct_classifications += 1
                print(f"✅ 分類正確: {classification['query_type']} ({classification['language']})")
            else:
                print(f"❌ 分類錯誤: 得到 {classification['query_type']} ({classification['language']}), "
                      f"預期 {test_case['type']} ({test_case['language']})")
            
            # 2. 測試檢索
            results = self.searcher.auto_search(test_case['query'], k=10)
            
            # 計算 Recall
            found_at = None
            if test_case.get('expected_player'):
                for rank, result in enumerate(results, 1):
                    if test_case['expected_player'] in result['player_id']:
                        found_at = rank
                        break
            else:
                # Ranking 查詢，只要有結果就算成功
                found_at = 1 if results else None
            
            if found_at:
                print(f"✅ 找到相關結果，排名: {found_at}")
                
                if found_at <= 5:
                    recall_5_count += 1
                if found_at <= 10:
                    recall_10_count += 1
                
                reciprocal_ranks.append(1.0 / found_at)
            else:
                print(f"❌ 未找到預期結果")
                reciprocal_ranks.append(0.0)
            
            # 顯示 Top 3 結果
            print(f"\nTop 3 結果:")
            for j, result in enumerate(results[:3], 1):
                print(f"  {j}. {result['player_id']:30s} (分數: {result['score']:.4f})")
            
            # 記錄詳細結果
            self.results['details'].append({
                'query': test_case['query'],
                'expected_type': test_case['type'],
                'predicted_type': classification['query_type'],
                'type_correct': type_correct,
                'expected_lang': test_case['language'],
                'predicted_lang': classification['language'],
                'lang_correct': lang_correct,
                'found_at': found_at,
                'top_results': [r['player_id'] for r in results[:3]]
            })
        
        # 計算最終指標
        self.results['classification_accuracy'] = correct_classifications / len(self.test_queries)
        self.results['recall_at_5'] = recall_5_count / len(self.test_queries)
        self.results['recall_at_10'] = recall_10_count / len(self.test_queries)
        self.results['mrr'] = sum(reciprocal_ranks) / len(reciprocal_ranks)
        
        self.print_summary()
        self.save_report()
    
    def print_summary(self):
        """打印評估摘要"""
        
        print("\n" + "=" * 80)
        print("評估結果摘要")
        print("=" * 80)
        
        print(f"\n總查詢數: {self.results['total_queries']}")
        print(f"\n分類準確率: {self.results['classification_accuracy']:.1%}")
        print(f"Recall@5:   {self.results['recall_at_5']:.1%}")
        print(f"Recall@10:  {self.results['recall_at_10']:.1%}")
        print(f"MRR:        {self.results['mrr']:.3f}")
        
        # 性能評級
        print("\n性能評級:")
        
        if self.results['recall_at_10'] >= 0.9:
            print("  檢索性能: ⭐⭐⭐⭐⭐ 優秀")
        elif self.results['recall_at_10'] >= 0.7:
            print("  檢索性能: ⭐⭐⭐⭐ 良好")
        elif self.results['recall_at_10'] >= 0.5:
            print("  檢索性能: ⭐⭐⭐ 一般")
        else:
            print("  檢索性能: ⭐⭐ 需要改進")
        
        if self.results['classification_accuracy'] >= 0.9:
            print("  分類準確度: ⭐⭐⭐⭐⭐ 優秀")
        elif self.results['classification_accuracy'] >= 0.7:
            print("  分類準確度: ⭐⭐⭐⭐ 良好")
        else:
            print("  分類準確度: ⭐⭐⭐ 需要改進")
        
        print("=" * 80)
    
    def save_report(self):
        """保存評估報告"""
        
        import json
        
        report_path = f"./test/report/evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n評估報告已保存: {report_path}")


def main():
    """主函數"""
    
    evaluator = PerformanceEvaluator()
    evaluator.evaluate()


if __name__ == "__main__":
    main()
