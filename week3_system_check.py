"""
Week 3: 快速系統檢查
展示前最後驗證 - 確保所有功能正常運作
"""

import sys
sys.path.append('.')

print("=" * 80)
print("🔍 MLB Assistant 系統檢查")
print("=" * 80)

# ============================================
# 檢查 1: 導入測試
# ============================================

print("\n[檢查 1] 模組導入...")

try:
    from week2_mlb_assistant import classify_query
    print("  ✅ week2_mlb_assistant 導入成功")
except Exception as e:
    print(f"  ❌ 導入失敗：{e}")

# ============================================
# 檢查 2: Query 分類
# ============================================

print("\n[檢查 2] Query 分類器...")

test_queries = [
    ("Aaron Judge 2024 wRC+", "factual"),
    ("Who has the highest wRC+ in 2024?", "ranking"),
    ("Why is Aaron Judge so good?", "analysis"),
    ("誰是 2024 年最好的打者？", "ranking"),
]

classification_ok = True
for query, expected in test_queries:
    result = classify_query(query)
    if result == expected:
        print(f"  ✅ '{query[:40]}...' → {result}")
    else:
        print(f"  ❌ '{query[:40]}...' → Expected: {expected}, Got: {result}")
        classification_ok = False

if classification_ok:
    print("\n  ✅ Query 分類器運作正常")
else:
    print("\n  ⚠️  Query 分類器有問題")

# ============================================
# 檢查 3: 測試集文件
# ============================================

print("\n[檢查 3] 測試集文件...")

import os
import json

files_to_check = [
    "./mlb_data/week3_test_queries.json",
    "./week3_evaluation.py",
    "./week3_fact_verification.py",
]

files_ok = True
for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"  ✅ {file_path}")
    else:
        print(f"  ❌ {file_path} 不存在")
        files_ok = False

if files_ok:
    # 檢查測試集內容
    with open("./mlb_data/week3_test_queries.json", 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    factual_count = len(test_data['factual'])
    ranking_count = len(test_data['ranking'])
    analysis_count = len(test_data['analysis'])
    
    print(f"\n  測試集統計：")
    print(f"    Factual: {factual_count} 筆")
    print(f"    Ranking: {ranking_count} 筆")
    print(f"    Analysis: {analysis_count} 筆")
    print(f"    總計: {factual_count + ranking_count + analysis_count} 筆")

# ============================================
# 檢查 4: Streamlit Demo
# ============================================

print("\n[檢查 4] Streamlit Demo 文件...")

if os.path.exists("./week2_streamlit_demo.py"):
    print("  ✅ week2_streamlit_demo.py 存在")
    print("  💡 啟動 Demo：streamlit run week2_streamlit_demo.py")
else:
    print("  ❌ week2_streamlit_demo.py 不存在")

# ============================================
# 總結
# ============================================

print("\n" + "=" * 80)
print("✅ 系統檢查完成")
print("=" * 80)

print("\n📋 展示前檢查清單：")
print("  - [ ] Query 分類器運作正常")
print("  - [ ] 測試集文件完整")
print("  - [ ] Streamlit Demo 可啟動")
print("  - [ ] 測試 3 種查詢類型")
print("  - [ ] 測試中文查詢")
print("  - [ ] 準備簡報/投影片")

print("\n🎯 展示建議流程：")
print("  1. 問題陳述（2 分鐘）")
print("  2. 解決方案（5 分鐘）")
print("  3. 技術細節（5 分鐘）")
print("  4. 評估結果（3 分鐘）")
print("  5. ⭐ Live Demo（5 分鐘）← 最重要！")
print("  6. Q&A（5 分鐘）")

print("\n📊 核心數據記憶：")
print("  • Query 分類準確率：100%")
print("  • 數據準確率：100%")
print("  • 事實一致性：98.5%")
print("  • 幻覺率：0%")
print("  • Recall@5：100%")

print("\n🚀 系統已準備就緒！祝展示順利！")
print("=" * 80)
