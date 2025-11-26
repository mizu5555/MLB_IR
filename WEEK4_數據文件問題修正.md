# Week 4: 數據文件問題修正指南

## 🐛 **問題根源確認**

你的 Streamlit 顯示賽季還是 2023-2024，原因是：

**Streamlit 讀取的是舊的 JSON 文件！**

```python
# Line 59 in week2_streamlit_demo.py
docs_file = os.path.join(DATA_DIR, "mlb_documents.json")  # ← Week 3 舊文件
```

**情況對比：**

| 項目 | 舊文件 | 新文件 |
|------|--------|--------|
| 檔名 | `mlb_documents.json` | `mlb_players_2022_2025.json` |
| 數據量 | 3,023 筆 | 6,133 筆 |
| 賽季 | 2023-2024 | 2022-2025 |
| 狀態 | Week 3 | Week 4 ✅ |

**結論：**
- ✅ LanceDB 資料庫是新的（有 2022-2025）
- ❌ Streamlit 讀取的 JSON 是舊的（只有 2023-2024）

---

## 🔍 **驗證問題（可選）**

執行這個命令確認：

```bash
# 檢查兩個文件的內容
python -c "import json; old = json.load(open('./mlb_data/mlb_documents.json')); new = json.load(open('./mlb_data/mlb_players_2022_2025.json')); print(f'舊文件: {len(old)} 筆, 賽季: {sorted(set(d[\"season\"] for d in old))}'); print(f'新文件: {len(new)} 筆, 賽季: {sorted(set(d[\"season\"] for d in new))}')"
```

**預期輸出：**
```
舊文件: 3023 筆, 賽季: [2023, 2024]
新文件: 6133 筆, 賽季: [2022, 2023, 2024, 2025]
```

---

## ✅ **解決方案**

### **方式 1：覆蓋舊文件（最簡單）** ⭐ **推薦**

```bash
# 1. 用新文件覆蓋舊文件
cp ./mlb_data/mlb_players_2022_2025.json ./mlb_data/mlb_documents.json

# 2. 清除 Streamlit 快取
streamlit cache clear

# 3. 重新啟動 Streamlit
streamlit run week2_streamlit_demo.py
```

**優點：**
- 最簡單，一行命令解決
- 不需要改程式碼
- 立即生效

---

### **方式 2：使用修正版 Streamlit（自動選擇文件）**

```bash
# 1. 使用修正版（會自動選擇新文件）
cp week4_streamlit_demo_fixed.py week2_streamlit_demo.py

# 2. 清除 Streamlit 快取
streamlit cache clear

# 3. 重新啟動
streamlit run week2_streamlit_demo.py
```

**優點：**
- 自動優先使用新文件
- 如果新文件不存在，會顯示警告
- 更智能

**修正後的邏輯：**
```python
# 優先使用新文件
docs_file_new = os.path.join(DATA_DIR, "mlb_players_2022_2025.json")
docs_file_old = os.path.join(DATA_DIR, "mlb_documents.json")

if os.path.exists(docs_file_new):
    docs_file = docs_file_new
    st.info("📊 使用擴充數據（2022-2025）")
else:
    docs_file = docs_file_old
    st.warning("⚠️ 使用舊數據（2023-2024）")
```

---

## 🧪 **驗證修正效果**

修正後，重新啟動 Streamlit，檢查：

### **1. 系統啟動訊息**
```
✅ 系統已載入：6133 筆球員記錄  ← 應該是 6133（不是 3023）
```

### **2. 側邊欄資訊**
```
📊 系統資訊
資料庫：6133 筆記錄
賽季：2022-2025  ← 應該是 2022-2025（不是 2023-2024）
```

### **3. 測試不同年份查詢**

**測試 A：2022 年**
```
查詢："Aaron Judge 2022 stats"
預期：HR: 62
```

**測試 B：2023 年**
```
查詢："Aaron Judge 2023 stats"
預期：HR: 37
```

**測試 C：2024 年**
```
查詢："Aaron Judge 2024 stats"
預期：HR: 58
```

**測試 D：2025 年**
```
查詢："Aaron Judge 2025 stats"
預期：HR: 53（根據你的驗證結果）
```

---

## 📊 **為什麼會有兩個 JSON 文件？**

**歷史原因：**

| 階段 | 文件名 | 賽季 | 用途 |
|------|--------|------|------|
| Week 3 | `mlb_documents.json` | 2023-2024 | 原始數據 |
| Week 4 | `mlb_players_2022_2025.json` | 2022-2025 | 擴充數據 |

**為什麼不自動更新？**
- Week 4 數據收集腳本建立了新文件，但沒有覆蓋舊文件
- Streamlit 程式碼寫死讀取舊文件名

---

## 🎯 **推薦的完整修正流程**

```bash
# Step 1: 覆蓋舊文件
cp ./mlb_data/mlb_players_2022_2025.json ./mlb_data/mlb_documents.json

# Step 2: 使用修正版 Streamlit（包含年份過濾等所有修正）
cp week4_streamlit_demo_fixed.py week2_streamlit_demo.py

# Step 3: 清除快取
streamlit cache clear

# Step 4: 重新啟動
streamlit run week2_streamlit_demo.py
```

---

## ✅ **修正完成檢查清單**

- [ ] 系統啟動顯示 6133 筆記錄
- [ ] 側邊欄顯示 2022-2025
- [ ] 查詢 "Aaron Judge 2022 stats" 顯示 HR: 62
- [ ] 查詢 "Aaron Judge 2023 stats" 顯示 HR: 37
- [ ] 查詢 "Aaron Judge 2024 stats" 顯示 HR: 58
- [ ] 年份過濾提示顯示（例如 "🎯 已過濾到 2022 賽季"）

**全部打勾？恭喜！Week 4 Phase 1 真正完成！** 🎉

---

## 💡 **未來避免此問題**

**建議：** 統一文件命名

```bash
# 以後數據收集後，直接覆蓋標準文件名
python week4_data_collection.py
cp ./mlb_data/mlb_players_2022_2025.json ./mlb_data/mlb_documents.json
python week4_build_vector_db.py
```

或者修改數據收集腳本，直接輸出到 `mlb_documents.json`。

---

## 🚀 **立即執行**

**最簡單的方式（推薦）：**

```bash
cp ./mlb_data/mlb_players_2022_2025.json ./mlb_data/mlb_documents.json
cp week4_streamlit_demo_fixed.py week2_streamlit_demo.py
streamlit cache clear
streamlit run week2_streamlit_demo.py
```

**執行後檢查側邊欄是否顯示 "賽季：2022-2025"！** ✅
