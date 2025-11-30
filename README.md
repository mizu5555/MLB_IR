# MLB Team Manager Assistant

一個基於混合檢索（Vector Search + BM25）和 LLM 的 MLB 球員數據分析系統。

<img width="2397" height="1157" alt="螢幕擷取畫面 2025-11-30 192110" src="https://github.com/user-attachments/assets/cd0a8de8-671b-4f40-9c5a-1222af6969d2" />


---

## 🎯 專案目標

為 MLB 團隊經理提供高性能的球員數據檢索和分析工具，確保事實一致性（Fact Consistency）接近 100%，避免 LLM 幻覺問題。

### 核心 IR 任務

1. **高性能異質檢索** (High-Performance Heterogeneous Retrieval)
   - 混合檢索：Vector Search (語意) + BM25 (關鍵字)
   - 智能查詢路由：根據查詢類型自動調整檢索策略

2. **事實一致性增強生成** (Fact Consistency Enhanced Generation)
   - 基於檢索結果的答案生成
   - 防止數值幻覺
   - 可選的 LLM 深度分析

---

## 📊 系統架構

```
用戶查詢
    ↓
[查詢分類] → 分析查詢類型、語言
    ↓
[混合檢索]
    ├── Vector Search (FAISS) → 語意相似度
    └── BM25 Search → 關鍵字匹配
    ↓
[動態權重融合] → 根據查詢類型調整權重
    ↓
[答案生成]
    ├── 純 RAG 模式 → 從檢索結果提取答案
    └── LLM 模式 → 使用 Ollama 生成深度分析
    ↓
最終答案 + 檢索證據
```

---

## 🚀 性能指標

基於評估數據集的測試結果：

| 指標 | 數值 | 說明 |
|------|------|------|
| **Recall@5** | 1.000 | 前5個結果包含正確答案 |
| **MRR** | 0.829 | 平均排名第1.2位 |
| **Type Accuracy** | 0.880 | 查詢分類準確率 |
| **Fact Consistency** | 1.000 | 事實一致性 |
| **Database Size** | 4,387 | 球員記錄數量 |
| **Seasons** | 2022-2024 | 涵蓋賽季 |

---

## 📁 專案結構

```
mlb-team-manager-assistant/
│
├── src/                           # 源代碼
│   ├── datapreprocess/                    # 資料預處理
│   │   ├── rebuild_data.py                # 腳本
│   │   ├── step1_generate_text_chunks.py  # 生成文本描述
│   │   ├── step2_build_vector_index.py    # 建立 Vector 索引
│   │   └── step3_build_bm25_index.py      # 建立 BM25 索引
│   │                    
│   ├── retrieval/                 # 檢索模組
│   │   ├── hybrid_search.py       # 混合檢索（Vector + BM25）
│   │   └── query_router.py        # 查詢分類與路由
│   │
│   ├── generation/                # 生成模組
│   │   └─ prompt_templates.py     # LLM 提示詞模板
│   │
│   └── web/                       # 網頁應用
│       ├── app.py                 # Flask 後端
│       └── static/
│           └── index.html         # 前端界面
│
├── data/                          # 數據目錄
│   ├── raw/                       # 原始 CSV 數據
│   │   ├── statcast_batters_enhanced.csv
│   │   └── statcast_pitchers_enhanced.csv
│   │
│   └── mlb_data/                  # 生成的索引文件
│       ├── text_chunks.json       # 文本描述
│       ├── vector_index.faiss     # FAISS 向量索引
│       ├── vector_embeddings.npy  # 向量嵌入
│       ├── vector_player_ids.json # Vector Player IDs
│       ├── bm25_index.pkl         # BM25 索引
│       ├── bm25_corpus.pkl        # BM25 分詞語料
│       └── bm25_player_ids.pkl    # BM25 Player IDs
│
├── test/ 
├── ├── report/                    # 測試報告
│   │    ├── bm25_corpus.pkl       # BM25 分詞語料
│   │    └── bm25_player_ids.pkl   # BM25 Player IDs
│   │
│   ├── test_system.py             # 系統測試腳本
│   └── evaluate.py                # 評估腳本
│
├── requirements.txt               
├── .gitignore                     
└── README.md                      
```

---

## 🛠️ 安裝與設置

### 1. 環境要求

- Python 3.8+
- 至少 8GB RAM
- 100MB 磁盤空間

### 2. 環境安裝

```bash
git clone <repository-url>
cd mlb-team-manager-assistant

# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 安裝
pip install -r requirements.txt
```

### 3. 準備數據

確保 `data/raw/` 目錄包含原始 CSV 文件：
- `statcast_batters_enhanced.csv`
- `statcast_pitchers_enhanced.csv`

### 4. 建立索引

```bash
# 運行數據重建腳本(待改進)
python rebuild_all_data.py
```

**生成文件**: 
- `data/mlb_data/text_chunks.json` (~8MB)
- `data/mlb_data/vector_index.faiss` (~7MB)
- `data/mlb_data/vector_embeddings.npy` (~7MB)
- `data/mlb_data/vector_player_ids.pkl` (~100KB)
- `data/mlb_data/bm25_index.pkl` (~5MB)
- `data/mlb_data/bm25_corpus.pkl` (~2MB)
- `data/mlb_data/bm25_player_ids.pkl` (~100KB)

---

## 🚀 使用方法

### 啟動網頁應用

```bash
python src/web/app.py
```

訪問: http://127.0.0.1:5000

---

## 💡 查詢範例

### Factual 查詢（事實型）

```
Aaron Judge 2022年的 wOBA 是多少？
What was Aaron Judge's wRC+ in 2022?
Aaron Judge 的出棒初速是多少？
```

### Ranking 查詢（排名型）

```
2022年 wRC+ 最高的5位球員
Who had the highest WAR in 2024?
最高出棒初速的打者有誰？
```

### Comparison 查詢（比較型）

```
比較 Aaron Judge 2022 和 2023 的表現
Compare Aaron Judge and Juan Soto in 2024
```

### Analysis 查詢（分析型）

```
分析 Aaron Judge 2022年為什麼能獲得 MVP
Why is Aaron Judge's 2022 season so valuable?
```

---

## 🔧 技術細節

### Vector Search

- **模型**: `sentence-transformers/all-MiniLM-L6-v2`
- **維度**: 384
- **索引**: FAISS (Flat L2)
- **優勢**: 捕捉語意相似度

### BM25 Search

- **分詞**: jieba (中文) + whitespace (英文)
- **參數**: k1=1.5, b=0.75
- **優勢**: 精確關鍵字匹配

### 混合策略

```python
final_score = α * vector_score + (1 - α) * bm25_score
```

**α 值（依查詢類型）**:
- Factual: 0.2 (偏向 BM25，精確匹配)
- Ranking: 0.5 (平衡)
- Comparison: 0.3 (略偏向 Vector)
- Analysis: 0.4 (略偏向 BM25)

---

## 📈 支援的統計類型

### 進階統計

- **wOBA** (加權上壘率): 0.320為聯盟平均
- **wRC+** (加權得分創造指數): 100為平均
- **WAR** (勝場貢獻值): 8+為MVP級別

### Statcast 數據

- Exit Velocity (出棒初速)
- Launch Angle (擊球仰角)
- Barrel Rate (強勁擊球率)
- Hard-Hit Rate (強擊球率)

### 其他統計

- 三振率 (K%)
- 保送率 (BB%)
- 滾地球率 (GB%)
- 飛球率 (FB%)
- 薪資與合約資訊

---

## 🧪 測試與評估

### 運行測試

```bash
# 系統功能測試
python test/test_system.py

# 評估數據集測試
python test/evaluate.py

```

生成文件會在 test/report 目錄中。


### 評估指標

- **Recall@k**: 前k個結果中包含正確答案的比例
- **MRR**: Mean Reciprocal Rank（平均倒數排名）
- **Type Accuracy**: 查詢分類準確率
- **Fact Consistency**: 事實一致性分數

---

## 🔄 數據更新

如果需要更新數據或重建索引：

```bash
# 1. 更新 data/raw/ 中的 CSV 文件

# 2. 重建所有索引
python rebuild_all_data.py

# 3. 重啟服務器
python src/web/app.py
```

---

## 開發計劃

### 已完成

- [x] 混合檢索系統（Vector + BM25）
- [x] 智能查詢路由
- [x] 事實一致性驗證
- [x] 網頁界面
- [x] 雙語支援（中英文）
- [x] 數據重建工具

### 待開發

- [ ] 賽季數據擴展
- [ ] 更多統計類型支援
- [ ] 進階分析功能
- [ ] 用戶對話
- [ ] API 文檔

---


## 📚 參考文獻

1. Min et al., 2024. "Exploring the Impact of Table-to-Text Methods on Augmenting LLM-based Question Answering with Domain Hybrid Data"
2. Robertson & Zaragoza, 2009. "The Probabilistic Relevance Framework: BM25 and Beyond"
3. Reimers & Gurevych, 2019. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"

---

**版本**: 1.0.1

本專案為課程作業，僅供學術用途。
