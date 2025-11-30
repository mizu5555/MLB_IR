"""
Phase 6: 混合檢索完整評估
比較 Pure Vector、Pure BM25、Hybrid 的效果
"""

import json
from typing import List, Dict, Tuple
import sys
import os

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase6_hybrid_search import HybridSearch


def evaluate_recall(results: List[Dict], ground_truth: List[str], k: int = 5) -> float:
    """計算 Recall@k"""
    
    if not ground_truth:
        return 0.0
    
    # 提取前 k 個結果的 player_ids
    top_k_ids = [r['player_id'] for r in results[:k]]
    
    # 計算有多少 ground truth 在前 k 個結果中
    hits = sum(1 for gt in ground_truth if gt in top_k_ids)
    
    recall = hits / len(ground_truth)
    return recall


def evaluate_mrr(results: List[Dict], ground_truth: List[str]) -> float:
    """計算 Mean Reciprocal Rank"""
    
    if not ground_truth:
        return 0.0
    
    # 提取所有結果的 player_ids
    result_ids = [r['player_id'] for r in results]
    
    # 找到第一個 ground truth 的位置
    for gt in ground_truth:
        if gt in result_ids:
            rank = result_ids.index(gt) + 1  # 1-indexed
            return 1.0 / rank
    
    return 0.0


def load_test_queries():
    """載入測試查詢"""
    
    # 定義測試查詢和 ground truth
    test_queries = [
        {
            'query': 'Aaron Judge home runs 2022',
            'type': 'factual',
            'ground_truth': ['Aaron Judge_2022'],
            'expected_type': 'batter'
        },
        {
            'query': 'high exit velocity power hitter',
            'type': 'semantic',
            'ground_truth': [],  # 沒有固定答案，檢查類型
            'expected_type': 'batter'
        },
        {
            'query': 'Shohei Ohtani pitching fastball velocity',
            'type': 'factual',
            'ground_truth': ['Shohei Ohtani_2022', 'Shohei Ohtani_2023'],
            'expected_type': 'pitcher'
        },
        {
            'query': 'best barrel rate and hard hit rate',
            'type': 'semantic',
            'ground_truth': [],
            'expected_type': 'batter'
        },
        {
            'query': 'Juan Soto batting average 2024',
            'type': 'factual',
            'ground_truth': ['Juan Soto_2024'],
            'expected_type': 'batter'
        },
        {
            'query': 'pitcher with high strikeout rate and low walk rate',
            'type': 'semantic',
            'ground_truth': [],
            'expected_type': 'pitcher'
        },
        {
            'query': 'Gerrit Cole ERA FIP 2023',
            'type': 'factual',
            'ground_truth': ['Gerrit Cole_2023'],
            'expected_type': 'pitcher'
        },
        {
            'query': 'best sprint speed fastest runner',
            'type': 'semantic',
            'ground_truth': [],
            'expected_type': 'batter'
        },
        {
            'query': 'MVP award winner 2022',
            'type': 'factual',
            'ground_truth': ['Aaron Judge_2022'],
            'expected_type': 'batter'
        },
        {
            'query': 'high WAR valuable player',
            'type': 'semantic',
            'ground_truth': [],
            'expected_type': 'batter'
        }
    ]
    
    return test_queries


def check_player_type(results: List[Dict], expected_type: str) -> float:
    """檢查結果的球員類型正確率"""
    
    if not results:
        return 0.0
    
    correct = 0
    for result in results[:5]:
        text = result['full_text']
        if expected_type == 'batter' and 'Type: batter' in text:
            correct += 1
        elif expected_type == 'pitcher' and 'Type: pitcher' in text:
            correct += 1
    
    return correct / min(5, len(results))


def main():
    print("\n" + "=" * 80)
    print("Phase 6: 混合檢索完整評估")
    print("=" * 80)
    
    # 初始化檢索器
    searcher = HybridSearch()
    
    # 載入測試查詢
    test_queries = load_test_queries()
    
    print(f"\n測試 {len(test_queries)} 個查詢")
    
    # 評估不同配置
    configs = [
        {'name': 'Pure Vector', 'alpha': 1.0, 'use_filter': False},
        {'name': 'Pure BM25', 'alpha': 0.0, 'use_filter': False},
        {'name': 'Hybrid 50-50', 'alpha': 0.5, 'use_filter': False},
        {'name': 'Hybrid 70-30', 'alpha': 0.7, 'use_filter': False},
        {'name': 'Auto Hybrid', 'alpha': 'auto', 'use_filter': False},
        {'name': 'Auto + Type Filter', 'alpha': 'auto', 'use_filter': True},
    ]
    
    results_summary = {config['name']: {
        'recall@5': [],
        'recall@10': [],
        'mrr': [],
        'type_accuracy': []
    } for config in configs}
    
    # 執行評估
    for config in configs:
        print(f"\n{'=' * 80}")
        print(f"評估: {config['name']}")
        print('=' * 80)
        
        for i, test in enumerate(test_queries, 1):
            query = test['query']
            ground_truth = test['ground_truth']
            expected_type = test['expected_type']
            
            print(f"\n查詢 {i}: {query}")
            print(f"  類型: {test['type']}")
            
            # 執行檢索
            if config['alpha'] == 'auto':
                results = searcher.auto_search(query, k=10)
            else:
                player_type = expected_type if config['use_filter'] else None
                results = searcher.hybrid_search(
                    query, 
                    k=10, 
                    alpha=config['alpha'],
                    player_type=player_type
                )
            
            # 顯示 Top 5
            print("  Top 5:")
            for j, result in enumerate(results[:5], 1):
                print(f"    {j}. {result['player_id']:30s} (分數: {result['score']:.4f})")
            
            # 評估指標
            if ground_truth:
                recall_5 = evaluate_recall(results, ground_truth, k=5)
                recall_10 = evaluate_recall(results, ground_truth, k=10)
                mrr = evaluate_mrr(results, ground_truth)
                
                results_summary[config['name']]['recall@5'].append(recall_5)
                results_summary[config['name']]['recall@10'].append(recall_10)
                results_summary[config['name']]['mrr'].append(mrr)
                
                print(f"  評估: Recall@5={recall_5:.2f}, Recall@10={recall_10:.2f}, MRR={mrr:.3f}")
            
            # 檢查類型正確率
            type_acc = check_player_type(results, expected_type)
            results_summary[config['name']]['type_accuracy'].append(type_acc)
            print(f"  類型正確率: {type_acc:.2f}")
    
    # 總結
    print("\n" + "=" * 80)
    print("評估總結")
    print("=" * 80)
    
    print("\n{:25s} {:>12s} {:>12s} {:>12s} {:>15s}".format(
        "配置", "Recall@5", "Recall@10", "MRR", "Type Accuracy"
    ))
    print("-" * 80)
    
    for config_name, metrics in results_summary.items():
        recall5 = sum(metrics['recall@5']) / len(metrics['recall@5']) if metrics['recall@5'] else 0
        recall10 = sum(metrics['recall@10']) / len(metrics['recall@10']) if metrics['recall@10'] else 0
        mrr = sum(metrics['mrr']) / len(metrics['mrr']) if metrics['mrr'] else 0
        type_acc = sum(metrics['type_accuracy']) / len(metrics['type_accuracy']) if metrics['type_accuracy'] else 0
        
        print("{:25s} {:>12.3f} {:>12.3f} {:>12.3f} {:>15.3f}".format(
            config_name, recall5, recall10, mrr, type_acc
        ))
    
    print("\n" + "=" * 80)
    print("✅ 評估完成！")
    print("=" * 80)
    
    # 找出最佳配置
    print("\n最佳配置建議:")
    
    best_recall = max(results_summary.items(), 
                      key=lambda x: sum(x[1]['recall@5']) / len(x[1]['recall@5']) if x[1]['recall@5'] else 0)
    print(f"  Recall@5 最高: {best_recall[0]}")
    
    best_type = max(results_summary.items(),
                    key=lambda x: sum(x[1]['type_accuracy']) / len(x[1]['type_accuracy']))
    print(f"  Type Accuracy 最高: {best_type[0]}")


if __name__ == "__main__":
    main()
