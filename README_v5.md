# MLB Team Manager Assistant - v5 更新版

## 🎯 v5 重大更新

### 1. RAG 回答格式改進 ✅
**風格：選項 A（直接比較式）**

#### 改進前：
```
找到 2 筆相關數據：
1. Shohei Ohtani (2023 LAA) - batter
   AVG: 0.304 | HR: 44 | OPS: 1.066
2. Aaron Judge (2023 NYY) - batter
   AVG: 0.267 | HR: 37 | OPS: 1.019
```

#### 改進後：
```
2023 年數據比較：

AVG：Shohei Ohtani 0.304 > Aaron Judge 0.267（Ohtani 較佳）
HR：Shohei Ohtani 44 > Aaron Judge 37（Ohtani 較佳）
OPS：Shohei Ohtani 1.066 > Aaron Judge 1.019（Ohtani 較佳）

詳細數據可以參考下方「原始數據來源」。
```

---

### 2. 評估指標系統 ✅

#### 後端日誌顯示：
```
📊 檢索評估指標:
   Recall@5: 100.0%
   Precision@5: 66.7%
   MRR: 1.000
   相關文檔: 2/3
```

#### 前端 Debug 面板顯示：
```
📊 Retrieval Metrics
Recall@5: 100.0%
Precision@5: 66.7%
MRR: 1.000
Relevant: 2/3
```

#### 獨立 API 端點：
```
GET http://localhost:8000/api/metrics

返回：
{
  "ok": true,
  "total_queries": 25,
  "average_metrics": {
    "recall@k": 0.9524,
    "precision@k": 0.7143,
    "mrr": 0.8952,
    "avg_response_time": 0.234
  },
  "recent_queries": [...],
  "metrics_file": "data/metrics_log.jsonl"
}
```

#### 自動記錄到檔案：
`data/metrics_log.jsonl` - 每次查詢都會追加記錄

---

## 📦 檔案

1. **app_v4.py** (23 KB) - 後端（改進回答 + 評估指標）
2. **index_v4.html** (25 KB) - 前端（Debug 面板顯示指標）
3. **query_router_v3.py** (9.0 KB) - 支援中英文球員
4. **prompt_templates_v3.py** (5.8 KB) - LLM 人性化 Prompt
5. **hybrid_search_v3.py** (8.4 KB) - 檢索引擎

---

## 🚀 執行順序

```bash
# 1. 替換 5 個檔案
cd C:\Users\mingju\Desktop\IR\project

copy app_v4.py src\web\app.py
copy index_v4.html src\web\static\index.html
copy query_router_v3.py src\retrieval\query_router.py
copy prompt_templates_v3.py src\generation\prompt_templates.py
copy hybrid_search_v3.py src\retrieval\hybrid_search.py

# 2. 啟動
cd src\web
python app.py

# 3. 測試
http://localhost:8000
```

---

## 🧪 測試案例

### 測試 1: 比較查詢
```
輸入：Ohtani 跟 Judge 2023年的打擊數據比較

預期 RAG 回答：
2023 年數據比較：
AVG：Shohei Ohtani 0.304 > Aaron Judge 0.267（Ohtani 較佳）
...
詳細數據可以參考下方「原始數據來源」。

預期日誌：
📊 檢索評估指標:
   Recall@5: 100.0%
   Precision@5: 66.7%
   MRR: 1.000
   相關文檔: 2/3
```

### 測試 2: 單一查詢
```
輸入：大谷 2023 投球

預期 RAG 回答：
找到 Shohei Ohtani 在 2023 年的數據（LAA）。

投球表現：
- ERA: 3.14
- WHIP: 1.06
- K%: 31.5
- FIP: 4.00

詳細數據可以參考下方「原始數據來源」。
```

### 測試 3: 查看累積指標
```
打開：http://localhost:8000/api/metrics

應該顯示：
- 總查詢次數
- 平均 Recall@k
- 平均 Precision@k
- 平均 MRR
- 最近 10 筆查詢
```

---

## 📊 評估指標說明

### Recall@k
**定義：** 在前 k 個結果中找到的相關文檔比例

**計算：**
- 相關性判斷：如果查詢指定球員/年份，則匹配的結果為相關
- Recall@5 = (前 5 個中相關的數量) / (總相關數量)

**範例：**
- 查詢：「Ohtani 2023」
- 前 5 個結果中有 2 個是 Ohtani 2023
- Recall@5 = 100%（假設只有 2 個相關結果）

### Precision@k
**定義：** 前 k 個結果中相關文檔的比例

**計算：**
- Precision@5 = (前 5 個中相關的數量) / 5

**範例：**
- 前 5 個結果中有 2 個相關
- Precision@5 = 2/5 = 40%

### MRR (Mean Reciprocal Rank)
**定義：** 第一個相關結果的排名倒數

**計算：**
- 如果第一個相關結果在第 1 名：MRR = 1/1 = 1.000
- 如果第一個相關結果在第 2 名：MRR = 1/2 = 0.500
- 如果第一個相關結果在第 3 名：MRR = 1/3 = 0.333

---

## 🔍 前端 Debug 面板

**開啟方式：** 點擊右上角「🐞 Debug」

**顯示內容：**
1. **Query Router**
   - Type, Intent, Metric, Season, Players

2. **Retrieval Metrics** ⭐ 新增
   - Recall@k
   - Precision@k
   - MRR
   - Relevant docs count

3. **Structured Lookup**（如果有）
   - Kind, Results count

4. **Full JSON**（展開查看）

---

## 📁 Metrics 記錄檔案

**位置：** `data/metrics_log.jsonl`

**格式：** 每行一個 JSON 物件
```json
{
  "timestamp": "2024-12-02T10:30:45.123456",
  "query": "Ohtani 跟 Judge 2023年的打擊數據比較",
  "mode": "rag",
  "query_type": "factual",
  "metrics": {
    "recall@k": 1.0,
    "precision@k": 0.667,
    "mrr": 1.0,
    "relevant_count": 2,
    "total_retrieved": 3,
    "k": 5
  },
  "response_time": 0.234,
  "results_count": 3
}
```

---

## 🎯 後端日誌範例

```
============================================================
📊 Query: Ohtani 跟 Judge 2023年的打擊數據比較
   Type: factual, Metric: None, Mode: rag, TopK: 5

   🎯 應用 type_boost: {'batter': 0.0, 'pitcher': 0.0}
   🔍 過濾球員: ['Shohei Ohtani', 'Aaron Judge'] → 4 筆
   🔍 過濾年度: [2023] → 3 筆

🔍 HybridSearch 返回 3 筆結果:
   1. Shohei Ohtani 2023 batter score=1.2965
   2. Aaron Judge 2023 batter score=1.1523
   3. Shohei Ohtani 2023 pitcher score=0.7965

📊 檢索評估指標:
   Recall@5: 100.0%
   Precision@5: 66.7%
   MRR: 1.000
   相關文檔: 2/3

🔄 開始序列化 3 筆結果:
   序列化 1: Shohei Ohtani 2023 batter score=1.2965
      → stats 包含 275 個欄位: ['Season', 'Player', 'Type', ...]
   序列化 2: Aaron Judge 2023 batter score=1.1523
      → stats 包含 268 個欄位: ['Season', 'Player', 'Type', ...]
   序列化 3: Shohei Ohtani 2023 pitcher score=0.7965
      → stats 包含 298 個欄位: ['Type', 'Team', 'Age', ...]

✅ 序列化完成: 3 筆

✅ 返回 3 筆結果給前端
⏱️  響應時間: 0.23s
============================================================
```

---

## 🔧 v5 技術改進

### 1. RAG 回答生成邏輯（app_v4.py）
```python
def generate_rag_answer(query, hits, routed):
    # 比較查詢：生成直接比較式回答
    if len(players) >= 2:
        # 按球員分組
        # 找出相同類型數據
        # 生成比較文字（高低判斷）
        # 加上提示語
    
    # 單一/列表查詢：簡潔呈現
    # ...
```

### 2. 評估指標計算（app_v4.py）
```python
def calculate_metrics(results, routed, k=5):
    # 相關性判斷：
    # - 匹配 filter_players
    # - 匹配 filter_seasons
    
    # 計算：
    # - Recall@k
    # - Precision@k
    # - MRR
    
    return metrics
```

### 3. 前端 Debug 面板（index_v4.html）
```jsx
{metrics && (
    <div>
        <h4>📊 Retrieval Metrics</h4>
        <div className="debug-grid">
            <div>Recall@{metrics.k}: {(metrics['recall@k'] * 100).toFixed(1)}%</div>
            <div>Precision@{metrics.k}: {(metrics['precision@k'] * 100).toFixed(1)}%</div>
            <div>MRR: {metrics.mrr.toFixed(3)}</div>
            <div>Relevant: {metrics.relevant_count}/{metrics.total_retrieved}</div>
        </div>
    </div>
)}
```

---

## 📝 注意事項

1. **Metrics 檔案路徑**
   - 確保 `data/` 目錄存在
   - 檔案會自動創建

2. **API 端點**
   - 訪問 `/api/metrics` 查看累積指標
   - 可以用於系統監控或實驗比較

3. **評估指標限制**
   - 目前基於查詢參數判斷相關性
   - 未來可加入人工標註的 ground truth

---

測試後回報結果！
