# Week 4: 年份寫死問題完整修正清單

## 🐛 **問題總結**

系統中有 **3 個文件** 都寫死了 `season == 2024`，導致無論資料庫有多少年份，查詢結果都只返回 2024 的數據。

---

## 📋 **需要修改的文件清單**

| 文件 | 行號 | 問題程式碼 | 影響 |
|------|------|-----------|------|
| `week2_streamlit_demo.py` | Line 217 | `filtered_df[filtered_df['season'] == 2024]` | Streamlit Demo ranking 查詢 |
| `week2_mlb_assistant.py` | Line 223 | `filtered_df[filtered_df['season'] == 2024]` | 主系統 ranking 查詢 |
| `week2_smart_router.py` | Line 207 | `filtered_df[filtered_df['season'] == 2024]` | 智能路由 ranking 查詢 |

---

## ✅ **修正方案**

### **核心邏輯：從查詢中提取年份**

```python
# 加入年份提取函數
def extract_year_from_query(query: str) -> int:
    """從查詢中提取年份"""
    import re
    year_pattern = r'\b(202[0-9])\b'
    match = re.search(year_pattern, query)
    
    if match:
        return int(match.group(1))
    
    return None

# 修改過濾邏輯
# 原本：
filtered_df = filtered_df[filtered_df['season'] == 2024]

# 修正為：
target_year = extract_year_from_query(query)
if target_year:
    filtered_df = filtered_df[filtered_df['season'] == target_year]
else:
    # 如果沒指定年份，使用最新賽季
    max_season = filtered_df['season'].max()
    filtered_df = filtered_df[filtered_df['season'] == max_season]
```

---

## 🔧 **詳細修正步驟**

### **文件 1: week2_streamlit_demo.py**

**Step 1: 在文件開頭加入年份提取函數**

找到 Line 38（配置部分之後），加入：

```python
# ============================================
# 輔助函數
# ============================================

def extract_year_from_query(query: str) -> int:
    """從查詢中提取年份"""
    import re
    year_pattern = r'\b(202[0-9])\b'
    match = re.search(year_pattern, query)
    
    if match:
        return int(match.group(1))
    
    return None
```

**Step 2: 修改 Line 217 附近的 ranking_search 函數**

找到 Line 215-217：
```python
# 過濾和排序
filtered_df = docs_df[docs_df['type'] == player_type].copy()
filtered_df = filtered_df[filtered_df['season'] == 2024]  # ← 要改這行
```

改為：
```python
# 過濾和排序
filtered_df = docs_df[docs_df['type'] == player_type].copy()

# 年份過濾（動態）
target_year = extract_year_from_query(query)
if target_year:
    filtered_df = filtered_df[filtered_df['season'] == target_year]
else:
    # 如果沒指定年份，使用最新賽季
    max_season = filtered_df['season'].max()
    filtered_df = filtered_df[filtered_df['season'] == max_season]
```

**Step 3: 修改 Line 417-422 的 factual 查詢邏輯**

找到：
```python
if query_type == 'factual':
    search_results = vector_search(query, k=3)
    data = {
        'top_result': search_results[0] if search_results else None,
        'all_results': search_results
    }
```

改為：
```python
if query_type == 'factual':
    search_results = vector_search(query, k=10)  # 增加搜尋結果
    
    # 從查詢中提取年份
    target_year = extract_year_from_query(query)
    
    # 如果有指定年份，過濾結果
    if target_year:
        filtered_results = [r for r in search_results if r.get('season') == target_year]
        
        # 如果過濾後有結果，使用過濾結果
        if filtered_results:
            search_results = filtered_results
            st.info(f"🎯 已過濾到 {target_year} 賽季")
    
    data = {
        'top_result': search_results[0] if search_results else None,
        'all_results': search_results
    }
```

---

### **文件 2: week2_mlb_assistant.py**

**Step 1: 找到 Line 223 附近**

```python
filtered_df = filtered_df[filtered_df['season'] == 2024]
```

**Step 2: 改為動態年份**

```python
# 年份過濾（動態）
import re
year_pattern = r'\b(202[0-9])\b'
match = re.search(year_pattern, query)

if match:
    target_year = int(match.group(1))
    filtered_df = filtered_df[filtered_df['season'] == target_year]
else:
    # 如果沒指定年份，使用最新賽季
    max_season = filtered_df['season'].max()
    filtered_df = filtered_df[filtered_df['season'] == max_season]
```

---

### **文件 3: week2_smart_router.py**

**Step 1: 找到 Line 207 附近**

```python
filtered_df = filtered_df[filtered_df['season'] == 2024]
```

**Step 2: 改為動態年份**

```python
# 年份過濾（動態）
import re
year_pattern = r'\b(202[0-9])\b'
match = re.search(year_pattern, query)

if match:
    target_year = int(match.group(1))
    filtered_df = filtered_df[filtered_df['season'] == target_year]
else:
    # 如果沒指定年份，使用最新賽季
    max_season = filtered_df['season'].max()
    filtered_df = filtered_df[filtered_df['season'] == max_season]
```

---

## 🧪 **修正後的測試**

修正所有 3 個文件後，測試：

### **測試 1: Factual 查詢（不同年份）**

```
"Aaron Judge 2022 stats" → 應返回 2022 數據（HR: 62）
"Aaron Judge 2023 stats" → 應返回 2023 數據（HR: 37）
"Aaron Judge 2024 stats" → 應返回 2024 數據（HR: 58）
```

### **測試 2: Ranking 查詢（不同年份）**

```
"Who has the highest wRC+ in 2022?" → 應返回 2022 的排名
"Who has the highest wRC+ in 2023?" → 應返回 2023 的排名
"Who has the highest wRC+ in 2024?" → 應返回 2024 的排名
```

### **測試 3: 無年份查詢（應使用最新賽季）**

```
"Who has the highest wRC+?" → 應返回 2025 或 2024 的排名（最新賽季）
"Aaron Judge stats" → 應返回最新賽季的數據
```

---

## 📦 **快速修正腳本**

我會建立完整修正後的文件供你使用：

1. `week4_streamlit_demo_fixed_v2.py` - 完整修正版
2. `week4_mlb_assistant_fixed.py` - 修正主系統
3. `week4_smart_router_fixed.py` - 修正智能路由

---

## 🎯 **修正優先級**

### **必須修正（影響最大）：**
1. ⭐ `week2_streamlit_demo.py` - 你正在使用的 UI

### **建議修正（保持一致性）：**
2. `week2_mlb_assistant.py` - 主系統
3. `week2_smart_router.py` - 智能路由

---

## ✅ **完成檢查清單**

- [ ] 修正 week2_streamlit_demo.py
- [ ] 修正 week2_mlb_assistant.py
- [ ] 修正 week2_smart_router.py
- [ ] 測試不同年份的 factual 查詢
- [ ] 測試不同年份的 ranking 查詢
- [ ] 測試無年份查詢（應返回最新賽季）

---

## 🚀 **下一步**

我現在建立完整修正後的文件供你直接使用！
