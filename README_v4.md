# MLB Team Manager Assistant - v4 更新版

## 🔧 v4 修正內容

### 問題 1: 抓不到英文球員名 ✅
**原因：** `extract_players` 只檢查中文 PLAYER_ALIAS 的 key

**修正：** `query_router_v3.py`
- ✅ 支援中文別名（大谷、山本）
- ✅ 支援英文姓氏（Ohtani, Judge, Trout）
- ✅ 支援完整英文名（Shohei Ohtani, Aaron Judge）
- ✅ 大小寫不敏感
- ✅ 內建 25+ 常見球員

### 問題 2: LLM 回答不人性化 ✅
**原因：** Prompt 太機械化，要求過於嚴格

**修正：** `prompt_templates_v3.py`
- ✅ 更自然、對話式的指令
- ✅ 鼓勵提供背景和解釋
- ✅ 加入範例回答
- ✅ 保持事實準確（不幻覺）

---

## 📦 檔案

- **query_router_v3.py** - 路由器（支援中英文球員名）
- **prompt_templates_v3.py** - Prompt（人性化回答）
- **app_v3.py** - 後端（參數修正）
- **hybrid_search_v3.py** - 檢索（type_boost）
- **index_v3.html** - 前端（完整統計）

---

## 🚀 執行順序

```bash
# 1. 替換 5 個檔案
cd C:\Users\mingju\Desktop\IR\project

copy query_router_v3.py src\retrieval\query_router.py
copy prompt_templates_v3.py src\generation\prompt_templates.py
copy app_v3.py src\web\app.py
copy hybrid_search_v3.py src\retrieval\hybrid_search.py
copy index_v3.html src\web\static\index.html

# 2. 啟動
cd src\web
python app.py

# 3. 測試
http://localhost:8000
```

---

## 🧪 測試案例

### 測試 1: 中文球員名
```
輸入：大谷 2023 投球
預期：✅ 抓到 Shohei Ohtani
```

### 測試 2: 英文姓氏
```
輸入：Ohtani 2023 pitching
預期：✅ 抓到 Shohei Ohtani
```

### 測試 3: 英文全名
```
輸入：Aaron Judge 2024 batting
預期：✅ 抓到 Aaron Judge
```

### 測試 4: 比較查詢
```
輸入：Judge vs Ohtani HR 2024
預期：✅ 抓到兩位球員
```

### 測試 5: LLM 回答
```
輸入：大谷 2023 投球表現如何？
預期：✅ 自然、人性化的回答
```

---

## 🔍 預期效果

### 後端日誌：
```
====================================
📊 Query: Judge vs Ohtani 2024

🎯 應用 type_boost: {'batter': 0.0, 'pitcher': 0.0}
🔍 過濾球員: ['Aaron Judge', 'Shohei Ohtani'] → 4 筆  ← 看這裡
🔍 過濾年度: [2024] → 2 筆

HybridSearch 返回 2 筆結果:
   1. Aaron Judge 2024 batter score=0.9523
   2. Shohei Ohtani 2024 batter score=0.9201
====================================
```

### LLM 回答（改進前）：
```
Aaron Judge: HR 58, OPS 1.159
Shohei Ohtani: HR 54, OPS 1.036
Judge higher.
```

### LLM 回答（改進後）：
```
Both Aaron Judge and Shohei Ohtani had exceptional 2024 seasons. 
Judge led with 58 home runs compared to Ohtani's 54, maintaining 
his power dominance. Judge's OPS of 1.159 was slightly higher than 
Ohtani's impressive 1.036. Both players were MVP-caliber performers.
```

---

## 📋 測試步驟

1. 替換 5 個檔案
2. 啟動 `python app.py`
3. 測試以下查詢：
   - 「大谷 2023 投球」
   - 「Ohtani 2023 pitching」
   - 「Judge vs Ohtani 2024」
   - 「Aaron Judge 2024 batting performance」
4. 貼上：
   - 後端日誌（過濾球員）
   - LLM 回答內容

---

## 🎯 內建球員名單

**日本球員：**
- Shohei Ohtani (大谷翔平)
- Yoshinobu Yamamoto (山本由伸)
- Yu Darvish (達比修有)
- Seiya Suzuki (鈴木誠也)
- Yusei Kikuchi (菊池雄星)
- Kenta Maeda (前田健太)

**美國球員：**
- Aaron Judge
- Mike Trout
- Mookie Betts
- Freddie Freeman
- Juan Soto
- Bryce Harper
- Ronald Acuna Jr.
- Fernando Tatis Jr.
- ... (共 25+ 名)

---

## 🐛 如果還抓不到球員

### 檢查 1: 後端日誌
```
🔍 過濾球員: ['Aaron Judge'] → X 筆
```

如果顯示 `[]` → 球員名沒被抓到

### 檢查 2: 手動測試 query_router
```bash
cd src\retrieval
python query_router_v3.py
```

應該會執行測試並顯示抓到的球員。

### 檢查 3: 增加新球員
編輯 `query_router_v3.py`：

```python
COMMON_PLAYERS = [
    "Ohtani", "Judge", "Trout",
    "你的球員姓氏",  # 加在這裡
]

def _get_full_name(self, last_name: str):
    name_map = {
        "ohtani": "Shohei Ohtani",
        "你的球員姓氏小寫": "完整名稱",  # 加在這裡
    }
```

---

## 📝 補充說明

### query_router_v3.py 改進：
1. 三階段檢查：中文別名 → 英文姓氏 → 完整英文名
2. 大小寫不敏感
3. 避免重複添加
4. 內建常見球員列表

### prompt_templates_v3.py 改進：
1. 對話式指令（"You are a friendly..."）
2. 提供範例回答
3. 鼓勵背景說明
4. 保持事實準確

---

測試後回報結果！
