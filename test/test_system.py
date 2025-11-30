"""
MLB Team Manager Assistant - 系統測試腳本
測試所有核心功能是否正常運作
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


class SystemTester:
    """系統測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'tests': []
        }
    
    def log_test(self, name, passed, message=""):
        """記錄測試結果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if message:
            print(f"       {message}")
        
        self.test_results['tests'].append({
            'name': name,
            'passed': passed,
            'message': message
        })
        
        if passed:
            self.test_results['tests_passed'] += 1
        else:
            self.test_results['tests_failed'] += 1
    
    def test_data_files(self):
        """測試 1: 檢查數據文件是否存在"""
        print("\n" + "=" * 80)
        print("測試 1: 數據文件檢查")
        print("=" * 80)
        
        required_files = {
            'text_chunks.json': './data/mlb_data/text_chunks.json',
            'vector_index.faiss': './data/mlb_data/vector_index.faiss',
            'vector_embeddings.npy': './data/mlb_data/vector_embeddings.npy',
            'vector_player_ids.json': './data/mlb_data/vector_player_ids.json',
            'bm25_index.pkl': './data/mlb_data/bm25_index.pkl',
            'bm25_corpus.pkl': './data/mlb_data/bm25_corpus.pkl',
            'bm25_player_ids.pkl': './data/mlb_data/bm25_player_ids.pkl'
        }
        
        all_exist = True
        for name, path in required_files.items():
            exists = Path(path).exists()
            if exists:
                size_mb = Path(path).stat().st_size / (1024 * 1024)
                self.log_test(
                    f"文件存在: {name}",
                    True,
                    f"大小: {size_mb:.1f} MB"
                )
            else:
                self.log_test(
                    f"文件存在: {name}",
                    False,
                    f"找不到文件: {path}"
                )
                all_exist = False
        
        return all_exist
    
    def test_hybrid_search_init(self):
        """測試 2: 混合檢索系統初始化"""
        print("\n" + "=" * 80)
        print("測試 2: 混合檢索系統初始化")
        print("=" * 80)
        
        try:
            ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            sys.path.insert(0, ROOT_DIR)
            from src.retrieval.hybrid_search import HybridSearch
            
            searcher = HybridSearch()
            
            # 檢查組件
            has_faiss = hasattr(searcher, 'faiss_index')
            has_bm25 = hasattr(searcher, 'bm25')
            has_encoder = hasattr(searcher, 'encoder')
            has_text = hasattr(searcher, 'text_chunks')
            
            self.log_test("FAISS 索引載入", has_faiss)
            self.log_test("BM25 索引載入", has_bm25)
            self.log_test("Encoder 模型載入", has_encoder)
            self.log_test("文本描述載入", has_text, f"{len(searcher.text_chunks)} 條記錄")
            
            return searcher if all([has_faiss, has_bm25, has_encoder, has_text]) else None
        
        except Exception as e:
            self.log_test("混合檢索初始化", False, str(e))
            return None
    
    def test_query_router(self):
        """測試 3: 查詢分類器"""
        print("\n" + "=" * 80)
        print("測試 3: 查詢分類器")
        print("=" * 80)
        
        try:
            ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            sys.path.insert(0, ROOT_DIR)
            from src.retrieval.query_router import QueryRouter
            
            router = QueryRouter()
            
            # 測試查詢
            test_queries = [
                ("Aaron Judge 2022年的 wOBA 是多少？", "factual", "zh"),
                ("What was Aaron Judge's wRC+ in 2022?", "factual", "en"),
                ("2024年 WAR 最高的5位球員", "ranking", "zh"),
                ("Compare Aaron Judge and Juan Soto", "comparison", "en"),
            ]
            
            all_passed = True
            for query, expected_type, expected_lang in test_queries:
                result = router.classify_query(query)
                
                type_correct = result['query_type'] == expected_type
                lang_correct = result['language'] == expected_lang
                
                passed = type_correct and lang_correct
                all_passed = all_passed and passed
                
                self.log_test(
                    f"分類查詢: '{query[:40]}...'",
                    passed,
                    f"類型: {result['query_type']} (預期: {expected_type}), "
                    f"語言: {result['language']} (預期: {expected_lang})"
                )
            
            return router if all_passed else None
        
        except Exception as e:
            self.log_test("查詢分類器", False, str(e))
            return None
    
    def test_search_functionality(self, searcher):
        """測試 4: 檢索功能"""
        print("\n" + "=" * 80)
        print("測試 4: 檢索功能")
        print("=" * 80)

        if not searcher:
            self.log_test("檢索功能測試", False, "混合檢索系統未初始化")
            return False
        
        try:
            # 測試查詢
            test_queries = [
                "Aaron Judge 2022",
                "high exit velocity",
                "pitcher strikeout rate"
            ]
            
            all_passed = True
            for query in test_queries:
                results = searcher.auto_search(query, k=5)
                
                has_results = len(results) > 0
                has_scores = all('score' in r for r in results)
                has_text = all('full_text' in r for r in results)
                
                passed = has_results and has_scores and has_text
                all_passed = all_passed and passed
                
                if passed:
                    top_player = results[0]['player_id']
                    top_score = results[0]['score']
                    self.log_test(
                        f"檢索: '{query}'",
                        True,
                        f"返回 {len(results)} 個結果, Top: {top_player} ({top_score:.4f})"
                    )
                else:
                    self.log_test(f"檢索: '{query}'", False, "結果格式錯誤")
            
            return all_passed
        
        except Exception as e:
            self.log_test("檢索功能", False, str(e))
            return False
    
    def test_vector_search(self, searcher):
        """測試 5: Vector Search"""
        print("\n" + "=" * 80)
        print("測試 5: Vector Search")
        print("=" * 80)
        
        if not searcher:
            self.log_test("Vector Search 測試", False, "混合檢索系統未初始化")
            return False
        
        try:
            query = "high power hitter"
            player_ids, scores = searcher.vector_search(query, k=5)
            
            has_results = len(player_ids) == 5
            has_scores = len(scores) == 5
            scores_valid = all(isinstance(s, (int, float)) for s in scores)
            
            passed = has_results and has_scores and scores_valid
            
            self.log_test(
                "Vector Search",
                passed,
                f"返回 {len(player_ids)} 個結果" if passed else "結果數量或格式錯誤"
            )
            
            return passed
        
        except Exception as e:
            self.log_test("Vector Search", False, str(e))
            return False
    
    def test_bm25_search(self, searcher):
        """測試 6: BM25 Search"""
        print("\n" + "=" * 80)
        print("測試 6: BM25 Search")
        print("=" * 80)
        
        if not searcher:
            self.log_test("BM25 Search 測試", False, "混合檢索系統未初始化")
            return False
        
        try:
            query = "Aaron Judge 2022"
            player_ids, scores = searcher.bm25_search(query, k=5)
            
            has_results = len(player_ids) == 5
            has_scores = len(scores) == 5
            scores_valid = all(isinstance(s, (int, float)) for s in scores)
            
            passed = has_results and has_scores and scores_valid
            
            self.log_test(
                "BM25 Search",
                passed,
                f"返回 {len(player_ids)} 個結果" if passed else "結果數量或格式錯誤"
            )
            
            return passed
        
        except Exception as e:
            self.log_test("BM25 Search", False, str(e))
            return False
    
    def test_answer_extraction(self):
        """測試 7: 答案提取（從 app.py）"""
        print("\n" + "=" * 80)
        print("測試 7: 答案提取")
        print("=" * 80)
        
        try:
            # 模擬檢索結果
            mock_result = {
                'player_id': 'Aaron Judge_2022',
                'full_text': 'Player: Aaron Judge. Season: 2022. Type: batter. wOBA: 0.458. wRC+: 206. WAR: 11.1',
                'score': 0.95
            }
            
            # 模擬分類
            mock_classification = {
                'query_type': 'factual',
                'language': 'zh'
            }
            
            # 測試不同查詢
            test_cases = [
                ("Aaron Judge 2022年的 wOBA 是多少？", "0.458"),
                ("Aaron Judge 2022年的 wRC+ 是多少？", "206"),
                ("Aaron Judge 2022年的 WAR 是多少？", "11.1"),
            ]
            
            all_passed = True
            for query, expected_value in test_cases:
                # 簡單的答案提取邏輯
                if 'wOBA' in query:
                    stat = 'wOBA'
                elif 'wRC+' in query:
                    stat = 'wRC+'
                elif 'WAR' in query:
                    stat = 'WAR'
                
                import re
                pattern = f'{stat}[:\s]+([0-9]+\.?[0-9]*)'
                match = re.search(pattern, mock_result['full_text'])
                
                if match:
                    extracted = match.group(1)
                    passed = extracted == expected_value
                    self.log_test(
                        f"答案提取: '{stat}'",
                        passed,
                        f"提取值: {extracted} (預期: {expected_value})"
                    )
                    all_passed = all_passed and passed
                else:
                    self.log_test(f"答案提取: '{stat}'", False, "未找到匹配")
                    all_passed = False
            
            return all_passed
        
        except Exception as e:
            self.log_test("答案提取", False, str(e))
            return False
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 80)
        print("測試報告")
        print("=" * 80)
        
        total = self.test_results['tests_passed'] + self.test_results['tests_failed']
        pass_rate = (self.test_results['tests_passed'] / total * 100) if total > 0 else 0
        
        print(f"\n總測試數: {total}")
        print(f"通過: {self.test_results['tests_passed']}")
        print(f"失敗: {self.test_results['tests_failed']}")
        print(f"通過率: {pass_rate:.1f}%")
        
        # 保存報告
        report_path = f"./test/report/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n測試報告已保存: {report_path}")
        
        if self.test_results['tests_failed'] == 0:
            print("\n🎉 所有測試通過！系統運行正常。")
        else:
            print(f"\n⚠️  有 {self.test_results['tests_failed']} 個測試失敗，請檢查。")
        
        print("=" * 80)


def main():
    """主測試流程"""
    
    print("\n" + "=" * 80)
    print("MLB Team Manager Assistant - 系統測試")
    print("=" * 80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SystemTester()
    
    # 執行測試
    data_ok = tester.test_data_files()
    
    if data_ok:
        searcher = tester.test_hybrid_search_init()
        router = tester.test_query_router()
        
        if searcher:
            tester.test_search_functionality(searcher)
            tester.test_vector_search(searcher)
            tester.test_bm25_search(searcher)
        
        tester.test_answer_extraction()
    else:
        print("\n⚠️  數據文件缺失，跳過功能測試")
        print("請先運行: python rebuild_data.py")
    
    # 生成報告
    tester.generate_report()


if __name__ == "__main__":
    main()
