# MLB IR System (MLB 資料檢索系統)

本系統提供 **純 RAG 資料檢索** 與 **LLM + RAG 問答能力**，支援 **中英文查詢**，並針對 MLB 數據做高一致性回覆。

專案使用 **高效異質檢索 High‑Performance Heterogeneous Retrieval**（向量 + BM25）與 **Fact Consistency Enhanced Generation**（結構化事實注入）以達成高品質的數據問答能力。

---

# 🔧 專案架構 Project Structure

```
├── src/
│   ├── datapreprocess/          # 數據前處理
│   │   ├── step0_parse_text_chunks.py      # 從 text_chunks.json 解析＋生成 player_db
│   │   ├── step1_build_training_data.py     # 產生訓練資料 (embedding_text, keyword_text 等)
│   │   ├── step2_build_vector_index.py      # 建立向量索引 FAISS
│   │   ├── step3_build_bm25_index.py        # 建立 BM25 索引
│   │   └── field_canonical_map.json         # 指標欄位標準化映射
│   │
│   ├── retrieval/               # 檢索系統
│   │   ├── hybrid_search.py     # 混合檢索 (Vector + BM25)
│   │   ├── query_router.py      # 查詢分類器＋路由
│   │   └── lookup_engine.py     # 數值查詢與事實取回
│   │
│   ├── generation/
│   │   └── prompt_templates.py  # LLM 提示詞與 Fact Consistency
│   │
│   └── web/
│       ├── app.py               # 後端 API
│       └── static/
│           └── index.html       # 前端網頁介面
│
├── data/
│   ├── raw/                     # 原始 CSV
│   └── mlb_data_adv/            # 處理後資料與索引
│       ├── text_chunks.json
│       ├── player_db.json
│       ├── training_data.json
│       ├── vector_index.faiss
│       ├── vector_embeddings.npy
│       ├── vector_ids.json
│       ├── bm25_index.pkl
│       ├── bm25_corpus.pkl
│       └── bm25_ids.pkl
```

---

# 🧩 處理流程 Processing Pipeline

系統的資料建構與檢索流程如下：

---

## ✅ Step 0 — 解析原始 text_chunks.json

**輸入：** data/mlb_data_adv/text_chunks.json
**輸出：**

* `player_db.json`（逐年記錄打/投）
* 每一筆資料解析後的清潔結構

🎯 功能：

* 解析 PlayerName_PlayerID_Season 格式
* 支援雙刀流（Shohei Ohtani），並逐年記錄 type：

```
"2022": ["batter", "pitcher"],
"2024": ["batter"]
```

---

## ✅ Step 1 — 產生訓練資料（embedding_text + keyword_text）

**輸入：** Step0 數據
**輸出：** training_data.json

包含：

* embedding_text（英文摘要用於向量）
* keyword_text（中英混合、專有名詞英文用於 BM25）
* field_text（後續 LLM 查詢可用）

📌 embedding_text 完全英文
📌 keyword_text 中英混合（名詞英文）
📌 數字處理為 **純文字，不會造成小數點解析問題**

---

## 📌 Step 2 — 建立向量索引（FAISS）

**模型：** all‑MiniLM‑L6‑v2（384 維度）
**輸入：** training_data.json
**輸出：**

* vector_embeddings.npy
* vector_index.faiss
* vector_ids.json

📌 選用 384d 模型理由：效率極高、泛化強、能支援英文 MLB 數據語意。

---

## 📌 Step 3 — 建立 BM25 索引

**輸入：** keyword_text
**輸出：**

* bm25_index.pkl
* bm25_corpus.pkl
* bm25_ids.pkl

📌 使用 jieba（中文）＋ whitespace tokenizer（英文）

---

# 🔍 檢索 Retrieval

## Hybrid Search 混合檢索

### 🔍 Step4 問題回顧 & 改進方向

在 Step4 測試 Hybrid Search 時觀察到兩個重要問題：

#### **問題 1：中文查詢對不到英文球員名字**

例如：`大谷 2023 投球` → 無法命中 Shohei Ohtani。
原因：

* embedding_text 完全英文
* keyword_text 也只有英文
* 中文名字未被映射 → 檢索系統完全不認得「大谷」「大谷翔平」

➡ **解法將於 Step5 實作：加入中英球員姓名映射表（alias dictionary）**
系統會先將中文別名轉成英文正式名稱再進行檢索。

---

#### **問題 2：查詢 pitching 時，打者資料比投手資料排更前面**

例如查：`Shohei Ohtani 2023 pitching`

* Shohei Ohtani 2023 batter → score 更高（BM25 優勢）
* Shohei Ohtani 2023 pitcher → 被排到第 4 名

原因：

* BM25 偏好文字較長的文件（打者 stats 行數遠大於投手）
* vector 其實判對（pitcher vec 分數更高）
* 但 hybrid 後被 BM25 拉偏

➡ **解法將於 Step5 實作：Query Router + Document Boosting**

* 自動偵測 query 在問 pitching / batting
* 若問 pitching → pitcher 文檔加權 +0.5、batter 文檔扣權 -0.3
* 若問 batting → batter 文檔加權 +0.5
* ranking/analysis 也會調整 α 值

---

### ⭐ Step4 重要結論

Hybrid Search 已正常運作，但若無 Query Router：

* 中文查詢無法命中球員
* 投打類型無法精準控制
* BM25 存在偏好長文件的偏差

➡ **Step5 將改善這些問題，讓檢索更精準且語意更聰明。**

```
final_score = α * vector + (1 - α) * bm25
```

依查詢類型自動調整 α：

* Factual → 0.2
* Ranking → 0.5
* Comparison → 0.3
* Analysis → 0.4

---

# 🧠 LLM 生成 Generation

## Fact Consistency Enhanced Generation (FCEG)

* hybrid search 回傳 N 筆資料 → 整理成 fact_block
* 注入 prompt → 避免幻覺
* 支援中英文球探式語氣

---

# 💻 Web 介面 Web App

提供 2 種模式：

1. **純 RAG 模式**：直接秀出檢索結果
2. **LLM + RAG 問答模式**：整合檢索結果回答


---

如需補充、調整格式、或加入示例，隨時告訴我！
