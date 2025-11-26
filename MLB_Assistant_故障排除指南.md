# MLB Assistant - 故障排除指南

**最後更新：** 2024-11-24

---

## 目錄

1. [常見問題](#常見問題)
2. [數據問題](#數據問題)
3. [搜索問題](#搜索問題)
4. [LLM 問題](#llm-問題)
5. [性能問題](#性能問題)
6. [UI 問題](#ui-問題)

---

## 常見問題

### Q1: 啟動時報錯 "Cannot connect to LanceDB"

**症狀：**
```
FileNotFoundError: [Errno 2] No such file or directory: './mlb_data/lancedb'
```

**原因：** 向量資料庫尚未建立

**解決方案：**
```bash
# 建立向量資料庫
python week4_build_vector_db.py
```

---

### Q2: "找不到球員" 錯誤

**症狀：**
```
找不到球員：Aaron Jude
```

**原因：** 拼寫錯誤或球員不在資料庫

**解決方案：**
1. 檢查拼寫：`Aaron Jude` → `Aaron Judge`
2. 確認球員在 2022-2025 賽季有數據
3. 嘗試使用全名

---

### Q3: LLM 返回佔位符

**症狀：**
```
1. [Top Player 1]
2. [Top Player 2]
```

**原因：** 統計鍵名不匹配

**解決方案：**
```bash
# 1. 運行診斷
python diagnose_ranking.py

# 2. 如果顯示 "有 wRC+ 數據的球員：0"
# 執行一鍵修正
week4_fix_keynames.bat

# 3. 重啟 Streamlit
streamlit run week2_streamlit_demo.py
```

---

### Q4: 側邊欄顯示 "賽季：2023-2024" 但數據已擴充

**症狀：** 資料庫有 2022-2025，但界面只顯示 2023-2024

**原因：** 數據文件未更新或快取問題

**解決方案：**
```bash
# 1. 更新數據文件
cp ./mlb_data/mlb_players_2022_2025.json ./mlb_data/mlb_documents.json

# 2. 清除快取
streamlit cache clear

# 3. 重啟
streamlit run week2_streamlit_demo.py
```

---

## 數據問題

### 問題：數據不是最新的

**症狀：** 查詢 2024 賽季數據，但統計不正確

**原因：** 數據需要手動更新

**解決方案：**
```bash
# 1. 重新收集數據
python week4_data_collection.py

# 2. 重建向量資料庫
python week4_build_vector_db.py

# 3. 更新數據文件
cp ./mlb_data/mlb_players_2022_2025.json ./mlb_data/mlb_documents.json

# 4. 重啟系統
streamlit cache clear
streamlit run week2_streamlit_demo.py
```

---

### 問題：部分球員找不到

**檢查清單：**

1. **確認數據文件：**
```bash
python -c "import json; data = json.load(open('./mlb_data/mlb_documents.json')); print(f'{len(data)} 筆記錄')"
```

應該顯示 6133 筆（如果是 Week 4）

2. **檢查資料庫：**
```bash
python verify_database_content.py
```

3. **檢查球員名稱：**
```bash
python check_stats_keys.py
```

---

### 問題：統計數值為 0

**症狀：**
```
有 wRC+ 數據的球員：0
```

**原因：** 統計鍵名不匹配

**診斷：**
```bash
python check_stats_keys.py
```

查看輸出中的實際鍵名

**解決：**
```bash
# 使用修正版文件
week4_fix_keynames.bat
```

---

## 搜索問題

### 問題：Vector Search 返回不相關結果

**症狀：** 查詢 "Aaron Judge" 返回其他球員

**原因：**
- Embedding 模型限制
- 查詢太短

**解決方案：**
1. 使用更具體的查詢：`"Aaron Judge NYY"`
2. 使用 FTS 替代：精確匹配球員名

**驗證：**
```python
# 測試 FTS
results = table.search("Aaron Judge", query_type="fts")
```

---

### 問題：FTS 找不到球員

**症狀：** FTS Search 返回空結果

**原因：** FTS 索引未建立

**解決方案：**
```bash
# 重建資料庫（包含 FTS 索引）
python week4_build_vector_db.py
```

---

### 問題：年份過濾失敗

**症狀：**
```
查詢："Aaron Judge 2022 stats"
返回：2024 數據
```

**原因：** 年份提取函數失敗

**檢查：**
```python
from week2_streamlit_demo import extract_year_from_query
year = extract_year_from_query("Aaron Judge 2022 stats")
print(year)  # 應該是 2022
```

**解決：**
- 確保使用 `week4_streamlit_demo_fixed.py`（有年份提取功能）

---

## LLM 問題

### 問題：Ollama 連接失敗

**症狀：**
```
ConnectionError: Cannot connect to Ollama at http://localhost:11434
```

**原因：** Ollama 未運行

**解決方案：**
```bash
# 啟動 Ollama
ollama serve

# 驗證
ollama list
```

---

### 問題：LLM 回應太慢

**症狀：** 每個查詢需要 10+ 秒

**原因：**
- 硬體限制
- 模型太大

**解決方案：**
1. 使用更小的模型（如果可用）
2. 增加 RAM
3. 使用 GPU 加速

**臨時方案：**
```python
# 降低 max_tokens
"max_tokens": 100  # 從 200 降到 100
```

---

### 問題：LLM 產生幻覺

**症狀：** 返回的數值與資料庫不符

**原因：**
- Temperature 太高
- Prompt 不夠嚴格

**解決方案：**
```python
# 降低 temperature
"temperature": 0.1  # 或更低

# 加強 prompt
prompt += "\nCRITICAL: Use ONLY provided statistics. Do NOT estimate."
```

---

## 性能問題

### 問題：查詢太慢（> 10 秒）

**診斷步驟：**

1. **測試 Vector Search：**
```python
import time
start = time.time()
results = vector_search("Aaron Judge", k=10)
print(f"Vector Search: {time.time() - start:.2f}s")
```

2. **測試 LLM：**
```python
start = time.time()
response = call_llm(prompt)
print(f"LLM: {time.time() - start:.2f}s")
```

**優化：**
- Vector Search > 1s → 重建索引
- LLM > 5s → 硬體問題或降低 max_tokens

---

### 問題：記憶體不足

**症狀：**
```
MemoryError: Unable to allocate array
```

**原因：** Embedding 生成佔用太多記憶體

**解決方案：**
```python
# 批量處理 Embeddings
batch_size = 100
for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    embeddings = model.encode(batch)
```

---

## UI 問題

### 問題：Streamlit 無法啟動

**症狀：**
```
ModuleNotFoundError: No module named 'streamlit'
```

**解決方案：**
```bash
pip install streamlit --break-system-packages
```

---

### 問題：界面卡住

**症狀：** 點擊查詢後沒有反應

**原因：**
- Ollama 未運行
- 資料庫損壞

**檢查：**
1. 確認 Ollama 運行：`ollama list`
2. 確認資料庫存在：`ls ./mlb_data/lancedb`
3. 查看終端錯誤訊息

---

### 問題：原始數據為空

**症狀：** 點擊「查看原始數據」，但沒有內容

**原因：** 數據傳遞問題

**檢查：**
```python
# 在 Streamlit 中加入除錯
st.write("Debug:", data)
```

---

## 診斷工具

### 工具 1: verify_database_content.py

**用途：** 檢查資料庫內容

**使用：**
```bash
python verify_database_content.py
```

**輸出：**
- 總記錄數
- 各賽季分布
- 測試查詢結果

---

### 工具 2: diagnose_ranking.py

**用途：** 診斷 Ranking 查詢問題

**使用：**
```bash
python diagnose_ranking.py
```

**輸出：**
- 過濾步驟結果
- 統計數據分布
- Top 5 球員

---

### 工具 3: check_stats_keys.py

**用途：** 檢查統計鍵名

**使用：**
```bash
python check_stats_keys.py
```

**輸出：**
- 所有鍵名列表
- wRC 相關鍵名
- 其他關鍵統計鍵名

---

## 日誌檢查

### Streamlit 日誌

**位置：** 終端輸出

**關鍵訊息：**
```
✅ 系統已載入：6133 筆球員記錄  ← 正常
❌ 系統初始化失敗  ← 有問題
```

---

### LanceDB 日誌

**檢查：**
```python
import lancedb
db = lancedb.connect("./mlb_data/lancedb")
table = db.open_table("mlb_players")
print(f"Records: {table.count_rows()}")
```

**應該：** 6133（Week 4）

---

## 重置系統

### 完整重置流程

```bash
# 1. 備份重要文件
cp week2_streamlit_demo.py week2_streamlit_demo_backup.py

# 2. 刪除資料庫
rm -rf ./mlb_data/lancedb

# 3. 重新收集數據
python week4_data_collection.py

# 4. 重建向量資料庫
python week4_build_vector_db.py

# 5. 更新系統文件
cp week4_streamlit_demo_fixed.py week2_streamlit_demo.py
cp week4_mlb_assistant_fixed.py week2_mlb_assistant.py
cp week4_smart_router_fixed.py week2_smart_router.py

# 6. 清除快取
streamlit cache clear

# 7. 重啟
streamlit run week2_streamlit_demo.py
```

---

## 聯絡支援

如果以上方法都無法解決問題：

1. **收集資訊：**
   - 錯誤訊息截圖
   - 診斷工具輸出
   - 系統配置（Python 版本、OS）

2. **查看文檔：**
   - [完整系統文檔](./MLB_Assistant_完整系統文檔.md)
   - [API 參考](./MLB_Assistant_API參考.md)

3. **聯絡開發團隊**

---

## 預防性維護

### 定期檢查清單

**每週：**
- [ ] 更新數據（`python week4_data_collection.py`）
- [ ] 驗證資料庫（`python verify_database_content.py`）
- [ ] 測試關鍵查詢

**每月：**
- [ ] 清除舊快取
- [ ] 檢查磁碟空間
- [ ] 備份資料庫

---

**故障排除指南結束**
