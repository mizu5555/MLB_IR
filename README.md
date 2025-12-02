⚾ MLB Intelligent Retrieval System

Hybrid Search + Query Router + Structured Stats Engine + Web UI + LLM Dialogue Mode

本系統是一個完整的「MLB 數據智能查詢平台」，支援：

語意查詢（Hybrid Search）

BM25 + Embedding 雙檢索

Query Routing（Intent / Metric / Player / Season / Ranking / Comparison）

Structured Answer（表格、排名、比較）

Raw Hits（檢索來源顯示）

本地 LLM（Ollama）對話模式

聊天介面（右側：使用者 / 左側：AI 球探風格）

可輸入：自然語言、英文、中文、中英混合

🏗 系統架構
project/
│
├── src/
│   ├── datapreprocess/
│   │   ├── step1_clean_json.py
│   │   ├── step2_build_vector_index.py
│   │   ├── step3_build_bm25.py
│   │   ├── step4_hybrid_test.py
│   │
│   ├── retrieval/
│   │   ├── hybrid_search.py      ← Hybrid Search（BM25 + Embedding）
│   │   ├── query_router.py       ← Query Router（Ranking / Comparison / Factual）
│   │   ├── lookup_engine.py      ← Structured Answer Engine
│   │
│   ├── web/
│       ├── app.py                ← Flask 後端 API（含本地 LLM）
│       ├── index.html            ← React UI + Chat Interface
│
├── data/
│   ├── training_data.json
│   ├── vectors.npy
│   ├── vector_ids.json
│
└── README.md

🔧 Step 1：資料清洗（training_data.json）

所有記錄採用固定格式：

{
  "record_key": "Shohei Ohtani_660271_2023_batter",
  "player_name": "Shohei Ohtani",
  "player_id": "660271",
  "season": 2023,
  "team": "LAA",
  "type": "batter",
  "clean_text": "...純文字...",
  "embedding_text": "...專給向量模型...",
  "keyword_text": "...給 BM25 ...",
  "stats": {
    "HR": 44,
    "AVG": 0.304,
    "WAR": 10.0,
    ...
  }
}


每筆都有 embedding_text 與 keyword_text，供後續做向量與 BM25。

🔍 Step 2：向量索引建立（FAISS + vectors.npy）

產生：

vectors.npy          ← shape = (N, 384)
vector_ids.json      ← 每個向量對應的 record_key


生成後，Hybrid Search 會讀：

self.vectors = np.load("vectors.npy")
self.vector_ids = json.load(open("vector_ids.json"))


並初始化：

faiss.IndexFlatIP(384)

📚 Step 3：BM25 索引建立（BM25Okapi）

使用：

keyword_text


斷詞成：

tokenized_corpus = [text.split() for text in keyword_text]


產生：

bm25_index.json


Hybrid Search：

self.bm25 = BM25Okapi(tokenized_corpus)

🔎 Step 4：Hybrid Search 測試（向量 + BM25）

權重：

score = bm25_score * 0.7 + vector_score * 0.3


並支援 type_boost：

pitcher: +0.5
batter: -0.3
...

🔮 Step 5：Query Router（分類使用者意圖）

Query Router 輸入自然語言，輸出結構：

{
  "query_type": "ranking",
  "intent": null,
  "metric": "HR",
  "players": [],
  "seasons": [2024],
  "top_n": 10
}


支援：

factual
例：大谷 2023 ERA

comparison
例：誰 2023 全壘打比大谷高？

ranking
例：2024 全壘打前 10 名

semantic（不知道要幹嘛就搜尋）

metric 與 number 自動抽出
例如：
前 5 名 → top_n=5
比 XX 高 → comparison

📊 Step 6：LookupEngine（Structured Answer Engine）

根據 Router 決定模式：

✔ 1. Factual

只回傳「該指標單一值」

{
  "kind": "factual",
  "player": "Shohei Ohtani",
  "season": 2023,
  "metric": "ERA",
  "value": 3.14
}

✔ 2. Ranking
{
  "kind": "ranking",
  "metric": "HR",
  "season": 2024,
  "top_n": 10,
  "results": [
     { "rank": 1, "player": "Judge", "value": 58 },
     ...
  ]
}

✔ 3. Comparison
{
  "kind": "comparison",
  "metric": "HR",
  "baseline_player": "Shohei Ohtani",
  "season": 2023,
  "results": [
     { "player": "Matt Olson", "value": 54, "diff": +10 }
  ]
}