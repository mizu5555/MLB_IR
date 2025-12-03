"""
MLB Team Manager Assistant - 系統測試腳本
測試所有核心功能是否正常運作
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent   
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(PROJECT_ROOT))

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
            'training_data.json': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'training_data.json'),
            'parsed_records.json': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'parsed_records.json'),
            'text_chunks.json': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'text_chunks.json'),
            'vector_ids.json': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'vector_ids.json'),
            'vector_index.faiss': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'vector_index.faiss'),
            'vector_embeddings.npy': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'vector_embeddings.npy'),
            'vector_player_ids.json': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'vector_player_ids.json'),
            'bm25_ids.pkl': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'bm25_ids.pkl'),
            'bm25_index.pkl': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'bm25_index.pkl'),
            'bm25_corpus.pkl': str(PROJECT_ROOT / 'data' / 'mlb_data_adv' / 'bm25_corpus.pkl'),
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
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 80)
        print("系統測試報告")
        print("=" * 80)
        print(f"測試時間: {self.test_results['timestamp']}")
        print(f"通過測試數: {self.test_results['tests_passed']}")
        print(f"失敗測試數: {self.test_results['tests_failed']}")
        REPORT_ROOT = PROJECT_ROOT / 'test' / 'reports'
        sys.path.insert(0, str(REPORT_ROOT))
        report_path = REPORT_ROOT / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        print(f"\n測試報告已保存: {report_path}")
        print("=" * 80)

def main():
    """主測試流程"""
    
    print("\n" + "=" * 80)
    print("MLB Team Manager Assistant - 系統測試")
    print("=" * 80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SystemTester()
    
    # 執行測試
    tester.test_data_files()
    
    # 生成報告
    tester.generate_report()


if __name__ == "__main__":
    main()
