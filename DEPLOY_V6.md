# ============================================================
# MLB RAG v6 部署指南
# 優化回答模板系統 + Debug 面板改進
# ============================================================

## 📦 v6 新功能

### 1. 回答模板系統
- **Factual Query**：先回答主要指標，再補充相關數據
- **Ranking Query**：結構化排名列表
- **Comparison Query**：區分多球員/多賽季比較

### 2. 改進的 Query Router
- 支援**單球員多賽季比較**（如：「Ohtani 2022 2023 全壘打」）
- 支援**多球員比較**（不要求明確 metric）

### 3. Debug 面板優化
- 加入 **Top N** 顯示（Ranking 查詢時）
- 移除重複的 **Execution Mode**

---

## 📂 檔案結構

```
mlb_v6/
├── answer_templates.py           # 回答模板系統（新檔案）
├── query_router.py              # 改進的 Query Router
├── app_v6_modifications.py      # app.py 修改內容
├── INDEX_HTML_MODIFICATIONS.md  # index.html 修改指南
└── DEPLOY_V6.md                 # 本檔案
```

---

## 🚀 部署步驟

### 步驟 1：複製 answer_templates.py

將 `answer_templates.py` 複製到專案的 `src/web/` 目錄：

**Windows:**
```batch
cd C:\Users\mingju\Desktop\IR\project
copy mlb_v6\answer_templates.py src\web\
```

**Linux/Mac:**
```bash
cd /path/to/project
cp mlb_v6/answer_templates.py src/web/
```

### 步驟 2：更新 query_router.py

將 `query_router.py` 複製到 `src/retrieval/`：

**Windows:**
```batch
copy src\retrieval\query_router.py src\retrieval\query_router_backup.py
copy mlb_v6\query_router.py src\retrieval\
```

**Linux/Mac:**
```bash
cp src/retrieval/query_router.py src/retrieval/query_router_backup.py
cp mlb_v6/query_router.py src/retrieval/
```

### 步驟 3：修改 app.py

#### 3.1 加入新的 import

在 `src/web/app.py` 的開頭（大約第 30 行），加入：

```python
# ⭐ 新增：導入回答模板系統
try:
    from answer_templates import (
        format_factual_answer,
        format_ranking_answer,
        format_comparison_answer,
        extract_comparison_data,
        extract_ranking_data
    )
    TEMPLATES_AVAILABLE = True
    print("✅ 成功載入 answer_templates")
except ImportError as e:
    print(f"⚠️ answer_templates 載入失敗: {e}")
    TEMPLATES_AVAILABLE = False
```

#### 3.2 替換 generate_rag_answer 函數

1. 打開 `src/web/app.py`
2. 找到 `generate_rag_answer` 函數（大約第 173 行）
3. 用 `app_v6_modifications.py` 中的版本替換整個函數

**重要：** 完整替換第 173-450 行左右的內容。

### 步驟 4：修改 index.html

按照 `INDEX_HTML_MODIFICATIONS.md` 的指示：

1. 打開 `src/web/static/index.html`
2. 找到 `renderDebugPanel` 函數
3. 用修改指南中的版本替換

---

## ✅ 驗證測試

### 測試 1：Factual Query（指定 metric）

**輸入：**
```
Yamamoto 防禦率
```

**預期後端日誌：**
```
   🎯 智能選擇統計數據 (Factual - 單一):
      查詢: Yamamoto 防禦率
      Metric: ERA
      類型: pitcher
      選擇: ['ERA', 'FIP', 'xFIP', 'SIERA']
```

**預期回答：**
```
Yoshinobu Yamamoto 在 2024 年 MLB 賽季（LAD）的防禦率（ERA）為 **3.00**。

其他投球表現數據：
- FIP: 3.02
- xFIP: 3.21
- SIERA: 3.15

其他詳細數據可以參考下方「原始數據來源」。
```

**Debug 面板應顯示：**
```
Query Type: factual
Intent: pitching
Metric: ERA
Season: 2024
Target Players: None
```

---

### 測試 2：Ranking Query

**輸入：**
```
2024 全壘打前 10 名
```

**預期後端日誌：**
```
   🎯 智能選擇統計數據 (Ranking):
      查詢: 2024 全壘打前 10 名
      Metric: HR
      類型: batter
      選擇: ['HR', 'ISO', 'SLG', 'Barrel%']
```

**預期回答：**
```
以下是 MLB 2024 年的 **全壘打** 前 10 名：

1. **Aaron Judge** (NYY) – 58
2. **Kyle Schwarber** (PHI) – 46
3. **Shohei Ohtani** (LAA) – 44
...

其他詳細數據可以參考下方「原始數據來源」。
```

**Debug 面板應顯示：**
```
Query Type: ranking
Intent: batting
Metric: HR
Season: 2024
Top N: 10  ← 新增！
Target Players: None
```

---

### 測試 3：Comparison Query（多球員）

**輸入：**
```
Ohtani 跟 Judge 打擊率比較
```

**預期後端日誌：**
```
   🎯 智能選擇統計數據 (Comparison):
      查詢: Ohtani 跟 Judge 打擊率比較
      Metric: AVG
      類型: batter
      選擇: ['AVG', 'OBP', 'BABIP', 'wOBA']
```

**預期回答：**
```
2023 年賽季中，**打擊率（AVG）** 比較如下：

- **Shohei Ohtani** (LAA): 0.304
- **Aaron Judge** (NYY): 0.267

結論：**Shohei Ohtani** 的 打擊率（AVG） 較佳（0.304）。

其他詳細數據可以參考下方「原始數據來源」。
```

**Debug 面板應顯示：**
```
Query Type: comparison
Intent: batting
Metric: AVG
Season: 2023
Target Players: Shohei Ohtani, Aaron Judge
```

---

### 測試 4：Comparison Query（多賽季）

**輸入：**
```
Ohtani 2022 2023 全壘打
```

**預期後端日誌：**
```
   🎯 智能選擇統計數據 (Comparison):
      查詢: Ohtani 2022 2023 全壘打
      Metric: HR
      類型: batter
      選擇: ['HR', 'ISO', 'SLG', 'Barrel%']
```

**預期回答：**
```
**Shohei Ohtani** 在不同賽季的 **全壘打（HR）** 比較如下：

- 2022 (LAA): 34
- 2023 (LAA): 44

趨勢：從 2022 到 2023 增加了 **10.00**。

其他詳細數據可以參考下方「原始數據來源」。
```

**Debug 面板應顯示：**
```
Query Type: comparison
Intent: batting
Metric: HR
Season: 2022, 2023
Target Players: Shohei Ohtani
```

---

## 🔧 問題排除

### 問題 1：ImportError: No module named 'answer_templates'

**原因：** answer_templates.py 不在正確的位置

**解決：**
```batch
# 檢查檔案位置
cd C:\Users\mingju\Desktop\IR\project\src\web
dir answer_templates.py

# 如果不存在，複製過來
copy ..\..\mlb_v6\answer_templates.py .
```

---

### 問題 2：回答仍使用舊格式

**原因：** generate_rag_answer 函數沒有正確替換

**解決：**
1. 確認 `generate_rag_answer` 函數開頭有：
   ```python
   if qtype == "ranking":
       if not metric:
           # 沒有指定 metric，使用傳統格式
   ```

2. 確認有導入模板：
   ```python
   if TEMPLATES_AVAILABLE:
       answer = format_ranking_answer(...)
   ```

---

### 問題 3：Debug 面板沒有顯示 Top N

**原因：** renderDebugPanel 函數沒有正確修改

**解決：**
在 `renderDebugPanel` 中加入：
```javascript
{routed.top_n && (
    <div><span className="debug-label">Top N:</span> {routed.top_n}</div>
)}
```

---

## 📊 v5 → v6 對比

| 功能 | v5 | v6 |
|------|----|----|
| Factual 回答 | 平鋪直述所有統計 | 先回答主要指標，再補充相關數據 ✨ |
| Ranking 回答 | 簡單列表 | 結構化排名 + 中文指標名稱 ✨ |
| Comparison 判斷 | 需要 2+ 球員 + metric | 支援單球員多賽季比較 ✨ |
| Debug 面板 | 缺少 top_n，有重複的 mode | 顯示 top_n，移除重複 ✨ |

---

## 📝 下一步優化建議

1. **加入單位顯示**
   - 速度：mph
   - 角度：degrees
   - 百分比：%

2. **加入趨勢分析**
   - 多賽季比較時，顯示趨勢圖或增減百分比

3. **加入排名上下文**
   - Ranking 查詢時，顯示聯盟平均值或中位數

4. **加入球員照片**
   - 在回答中顯示球員頭像

---

## 🎯 成功標準

- ✅ Factual 查詢先回答主要指標
- ✅ Ranking 查詢顯示結構化排名
- ✅ 支援單球員多賽季比較
- ✅ Debug 面板顯示 top_n
- ✅ 所有測試案例通過

---

**檔案位置：** `/mnt/user-data/outputs/mlb_v6/`

**部署完成後，記得測試所有功能！** 🚀
