"""
Week 3: 事實一致性驗證
驗證 LLM 生成的答案是否與檢索數據一致
"""

import re
from typing import Dict, List, Tuple

# ============================================
# 數值提取
# ============================================

def extract_numbers_from_text(text: str) -> List[Tuple[float, str]]:
    """
    從文本中提取數值
    
    Returns:
        List of (number, context) tuples
    """
    
    # 數值模式
    patterns = [
        r'(\d+\.\d+)',  # 220.0, 3.14
        r'(\d+)',       # 58, 100
    ]
    
    numbers = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            number = float(match.group(1))
            # 提取數值前後的上下文（幫助理解這是什麼數據）
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].replace('\n', ' ')
            numbers.append((number, context))
    
    return numbers

def extract_stats_from_data(data: Dict) -> Dict[str, float]:
    """
    從數據中提取統計數值
    """
    
    stats = {}
    
    if data.get('top_result'):
        player = data['top_result']
        for key, value in player.items():
            if key.startswith('stat_') and isinstance(value, (int, float)):
                stat_name = key.replace('stat_', '')
                stats[stat_name] = float(value)
    
    elif data.get('results'):
        # Ranking 查詢的結果
        for result in data['results']:
            if 'stat_value' in result:
                stat_name = result.get('stat_name', 'unknown')
                stat_value = result['stat_value']
                stats[f"{result['name']}_{stat_name}"] = float(stat_value)
    
    return stats

# ============================================
# 一致性驗證
# ============================================

def verify_fact_consistency(answer: str, data: Dict, tolerance: float = 1.0) -> Dict:
    """
    驗證答案與數據的一致性
    
    Args:
        answer: LLM 生成的答案
        data: 檢索到的原始數據
        tolerance: 容忍誤差（例如四捨五入導致的差異）
    
    Returns:
        {
            'score': float (0-1),
            'total_numbers': int,
            'correct_numbers': int,
            'extracted_numbers': List,
            'ground_truth': Dict,
            'matches': List,
            'mismatches': List
        }
    """
    
    # 提取答案中的數值
    extracted = extract_numbers_from_text(answer)
    
    # 提取數據中的數值
    ground_truth = extract_stats_from_data(data)
    
    matches = []
    mismatches = []
    
    # 對比每個提取的數值
    for number, context in extracted:
        found_match = False
        
        for stat_name, truth_value in ground_truth.items():
            # 容忍小誤差（例如四捨五入）
            if abs(number - truth_value) < tolerance:
                matches.append({
                    'number': number,
                    'stat': stat_name,
                    'truth': truth_value,
                    'context': context,
                    'diff': abs(number - truth_value)
                })
                found_match = True
                break
        
        if not found_match:
            # 檢查是否是年份、排名等非統計數字
            if number >= 2020 and number <= 2025:
                # 年份 - 可能是合理的
                continue
            elif number >= 1 and number <= 10 and '.' not in str(number):
                # 排名 - 可能是合理的
                continue
            else:
                mismatches.append({
                    'number': number,
                    'context': context,
                    'reason': '找不到對應的數據'
                })
    
    # 計算一致性分數
    total = len(extracted)
    correct = len(matches)
    
    # 如果沒有數字，認為一致性為 100%（可能是描述性回答）
    score = correct / total if total > 0 else 1.0
    
    return {
        'score': score,
        'total_numbers': total,
        'correct_numbers': correct,
        'extracted_numbers': extracted,
        'ground_truth': ground_truth,
        'matches': matches,
        'mismatches': mismatches
    }

# ============================================
# 批量驗證
# ============================================

def batch_verify_consistency(results: List[Dict]) -> Dict:
    """
    批量驗證多個查詢結果的一致性
    
    Args:
        results: List of {query, answer, data} dicts
    
    Returns:
        {
            'total': int,
            'average_score': float,
            'perfect_count': int,
            'issues': List
        }
    """
    
    total = 0
    total_score = 0.0
    perfect_count = 0
    issues = []
    
    for result in results:
        verification = verify_fact_consistency(
            result['answer'], 
            result['data']
        )
        
        total += 1
        total_score += verification['score']
        
        if verification['score'] == 1.0:
            perfect_count += 1
        
        if verification['score'] < 1.0:
            issues.append({
                'query': result['query'],
                'score': verification['score'],
                'mismatches': verification['mismatches']
            })
    
    return {
        'total': total,
        'average_score': total_score / total if total > 0 else 0,
        'perfect_count': perfect_count,
        'perfect_rate': perfect_count / total if total > 0 else 0,
        'issues': issues
    }

# ============================================
# 測試範例
# ============================================

if __name__ == "__main__":
    
    print("=" * 80)
    print("事實一致性驗證 - 測試")
    print("=" * 80)
    
    # 測試案例 1: 完全一致
    print("\n[測試 1] 完全一致的答案")
    answer1 = "Aaron Judge's 2024 wRC+ is 220.0, with an OPS of 1.159 and 58 home runs."
    data1 = {
        'top_result': {
            'player_name': 'Aaron Judge',
            'stat_wRC_plus': 220.0,
            'stat_OPS': 1.159,
            'stat_HR': 58
        }
    }
    
    result1 = verify_fact_consistency(answer1, data1)
    print(f"  一致性分數：{result1['score']:.1%}")
    print(f"  提取數值：{result1['total_numbers']} 個")
    print(f"  正確數值：{result1['correct_numbers']} 個")
    
    if result1['matches']:
        print("\n  匹配：")
        for match in result1['matches']:
            print(f"    {match['number']} → {match['stat']}: {match['truth']} (diff: {match['diff']:.3f})")
    
    if result1['mismatches']:
        print("\n  ⚠️  不匹配：")
        for mismatch in result1['mismatches']:
            print(f"    {mismatch['number']}: {mismatch['reason']}")
            print(f"      Context: {mismatch['context']}")
    
    # 測試案例 2: 有錯誤
    print("\n" + "=" * 80)
    print("[測試 2] 有錯誤的答案")
    answer2 = "Aaron Judge's wRC+ is 250.0 (錯誤), with 58 home runs (正確)."
    data2 = {
        'top_result': {
            'stat_wRC_plus': 220.0,
            'stat_HR': 58
        }
    }
    
    result2 = verify_fact_consistency(answer2, data2)
    print(f"  一致性分數：{result2['score']:.1%}")
    print(f"  提取數值：{result2['total_numbers']} 個")
    print(f"  正確數值：{result2['correct_numbers']} 個")
    
    if result2['mismatches']:
        print("\n  ⚠️  不匹配：")
        for mismatch in result2['mismatches']:
            print(f"    {mismatch['number']}: {mismatch['reason']}")
    
    # 測試案例 3: Ranking 查詢
    print("\n" + "=" * 80)
    print("[測試 3] Ranking 查詢")
    answer3 = """根據 wRC+ 數據，排名如下：
1. Aaron Judge (NYY) - 220.0
2. Juan Soto (NYY) - 181.0
3. Shohei Ohtani (LAD) - 180.0"""
    
    data3 = {
        'results': [
            {'name': 'Aaron Judge', 'stat_name': 'wRC_plus', 'stat_value': 220.0},
            {'name': 'Juan Soto', 'stat_name': 'wRC_plus', 'stat_value': 181.0},
            {'name': 'Shohei Ohtani', 'stat_name': 'wRC_plus', 'stat_value': 180.0}
        ]
    }
    
    result3 = verify_fact_consistency(answer3, data3)
    print(f"  一致性分數：{result3['score']:.1%}")
    print(f"  提取數值：{result3['total_numbers']} 個")
    print(f"  正確數值：{result3['correct_numbers']} 個")
    
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)
