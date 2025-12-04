# MLB Team Manager Assistant

一個基於混合檢索（Vector Search + BM25）和 LLM 的 MLB 球員數據分析系統，具備完整的評估指標追蹤功能。
<p float="left">
  <img src="https://github.com/user-attachments/assets/19401b82-854c-4d92-a623-34e12a073a33" width="49%" height="350"/>
  <img src="https://github.com/user-attachments/assets/1dcbd96b-efc7-4bf8-9f26-8c4280060521" width="49%" height="350"/>
</p>

---

## 🎯 專案目標

為 MLB 團隊經理提供高性能的球員數據檢索和分析工具，確保事實一致性（Fact Consistency）接近 100%，避免 LLM 幻覺問題。

### 核心 IR 任務

1. **高性能異質檢索** (High-Performance Heterogeneous Retrieval)
   - 混合檢索：Vector Search (語意) + BM25 (關鍵字)
   - 智能查詢路由：根據查詢類型自動調整檢索策略
   - 即時評估指標：Recall@k, Precision@k, MRR

2. **事實一致性增強生成** (Fact Consistency Enhanced Generation)
   - 基於檢索結果的結構化答案生成
   - 防止數值幻覺
   - 可選的 LLM 深度分析（Ollama 本地運行）

---

## 📊 系統架構

```
用戶查詢
    ↓
[查詢分類 & 路由]
    ├── 球員識別（中英文支援）
    ├── 查詢類型分類（Factual/Ranking/Comparison/Analysis）
    ├── Metric 抽取（HR, ERA, OPS...）
    └── 賽季/球員過濾
    ↓
[混合檢索]
    ├── Vector Search (語意相似度)
    │   └── sentence-transformers/all-MiniLM-L6-v2
    └── BM25 Search (關鍵字匹配)
        └── jieba + whitespace tokenizer
    ↓
[動態權重融合]
    └── α * vector_score + (1-α) * bm25_score
    ↓
[評估指標計算] 
    ├── Recall@k
    ├── Precision@k
    ├── MRR
    └── 自動記錄到 metrics_log.jsonl
    ↓
[答案生成]
    ├── 純 RAG 模式 → 結構化答案（比較式/列表式）
    └── LLM 模式 → Ollama 對話式分析
    ↓
最終答案 + 檢索證據 + 評估指標
```

---

## 🚀 性能指標

| 指標 | 數值 | 說明 |
|------|------|------|
| **Recall@5** | 100.0% | 前5個結果包含所有相關文檔 |
| **Precision@5** | 66.7% | 前5個結果中相關文檔比例 |
| **MRR** | 1.000 | 第一個相關結果在第1位 |
| **Query Classification Accuracy** | 100% | 查詢分類準確率 |
| **Fact Consistency Score** | N/A | 事實一致性評分 |
| **Zero Hallucination Rate** | N/A | 無數值幻覺 |
| **Avg Response Time** | 0.23s | 平均響應時間 |
| **Database Size** | 3252 | 球員記錄數量 |
| **Seasons Covered** | 2022-2024 | 涵蓋賽季 |

---

## 📁 專案結構

```
mlb-team-manager-assistant/
│
├── src/                                    # 源代碼
│   ├── datapreprocess/  
│   │   ├── download.py                     # 資料下載及預處理
│   │   ├── rebuild_data.py                 # 資料重建腳本（支援 CSV/JSON）
│   │   ├── step0_parse_text_chunks.py      # 解析文本塊
│   │   ├── step1_build_training_data.py    # 建立訓練數據
│   │   ├── step2_build_vector_index.py     # 建立 Vector 索引（FAISS）
│   │   └── step3_build_bm25_index.py       # 建立 BM25 索引
│   │
│   ├── retrieval/                          # 檢索模組
│   │   ├── hybrid_search.py                # 混合檢索（Vector + BM25）
│   │   ├── query_router.py                 # 查詢分類與路由
│   │   └── lookup_engine.py                # 結構化查詢引擎
│   │
│   ├── generation/                         # 生成模組
│   │   └── prompt_templates.py             # LLM 提示詞模板（人性化）
│   │
│   └── web/                                # 網頁應用
│       ├── app.py                          # Flask 後端
│       ├── answer_templates.py             # 回答模板系統
│       ├── stat_selection_config.py        # 查詢匹配驅動       
│       └── static/
│           └── index.html                  # React 前端界面
│
├── data/                                   # 數據目錄
│   ├── raw_adv/                            # 新版數據（含player_id）
│   │   ├── statcast_batters_enhanced.csv
│   │   ├── statcast_pitchers_enhanced.csv
│   │   └── statcast_enhanced.json
│   │
│   └── mlb_data_adv/                       # 生成的索引文件
│       ├── text_chunks.json                # 文本描述
│       ├── parsed_records.json             # 解析後的記錄
│       ├── training_data.json              # 訓練數據（含stats）
│       ├── player_db.json                  # 球員資料庫
│       ├── vector_index.faiss              # FAISS 向量索引
│       ├── vector_embeddings.npy           # 向量嵌入
│       ├── vector_ids.json                 # Vector IDs（索引對應）
│       ├── bm25_index.pkl                  # BM25 索引
│       ├── bm25_corpus.pkl                 # BM25 分詞語料
│       └── bm25_ids.pkl                    # BM25 IDs
│
├── test/                                   # 測試
│   ├── reports/                             # 測試報告
│   ├── test_system.py                      # 系統測試
│   ├── evaluate.py                         # 評估腳本
│   ├── view_metrics.py                     # 檢視指標腳本(需運行)
│   └── check_database.py                   # 資料庫檢查
│
├── result/ 
│   └── metrics_log.jsonl                   # 評估指標記錄
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
- 500MB 磁盤空間
- Ollama-用於 LLM 對話模式 (可選)

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

# 安裝依賴
pip install -r requirements.txt
```

### 3. 安裝 Ollama

**啟用 LLM 對話模式需要：**

```bash
# 1. 下載 Ollama
# 訪問：https://ollama.ai/download

# 2. 安裝模型
ollama pull llama3.2

# 3. 驗證
ollama list
```

### 4. 準備數據

確保 `data/raw_adv/` 目錄包含數據文件：
- `statcast_batters_enhanced.csv`
- `statcast_pitchers_enhanced.csv`

第一次使用請生成數據文件(自訂年份)：
```bash
cd src/datapreprocess
python download.py
```
### 5. 建立索引

```bash
cd src/datapreprocess
python rebuild_data.py
python step0_parse_text_chunks.py
python step1_build_training_data.py
python step2_build_vector_index.py
python step3_build_bm25_index.py
```
所有數據文件會被儲存到 `data/mlb_data_adv/` 資料夾底下。

---

## 🚀 使用方法

### 啟動網頁應用

```bash
cd src/web
python app.py
```

**訪問**: http://localhost:8000

**系統狀態檢查**:
- 右上角顯示 LLM 狀態（綠點 = 可用）
- 右上角顯示資料庫大小

### 兩種查詢模式

#### 1. 純 RAG 模式 🔍
- 精確數據查詢
- 結構化答案
- 適合事實型問題

#### 2. LLM 對話模式 💬
- 自然語言對話
- 深度分析
- 需要 Ollama 運行

---

## 💡 查詢範例

### Factual 查詢（事實型）

```
Ohtani 2023 投球表現如何？
What was Aaron Judge's OPS in 2024?
山本由伸的 ERA 是多少？
```

**RAG 回答範例**：
```
找到 Shohei Ohtani 在 2023 年的數據（LAA）。
投球表現：
- ERA: 3.14
- WHIP: 1.06
- K%: 31.5
- FIP: 4.00
詳細數據可以參考下方「原始數據來源」。
```

### Ranking 查詢（排名型）

```
2024 全壘打前 5 名
Who had the highest WAR in 2023?
2022年打擊率前 10 名
```
**RAG 回答範例**：
```
**2024 年 全壘打 (HR) 排名前 5 名**
Aaron Judge (NYY) - 58
Shohei Ohtani (LAD) - 54
Anthony Santander (BAL) - 44
Juan Soto (NYY) - 41
Marcell Ozuna (ATL) - 39
```

### Comparison 查詢（比較型）

```
比較Judge跟Ohtani2022年的全壘打數
```

**RAG 回答範例**：
```
**2022 年 全壘打 (HR) 比較**
Shohei Ohtani (LAA): 34
Aaron Judge (NYY): 62

詳細數據可以參考下方「原始數據來源」。
```

### Analysis 查詢（分析型）

```
Trout為什麼2024被三振這麼多
```

**RAG 回答範例**：
```
** Mike Trout 2023 年分析報告**
問題診斷: 壓制力不足
🔍 關鍵數據診斷
打擊率 (AVG): 0.322
BABIP: 0.367
Contact%: 71.2%
三振率 (K%): 24.3%
📈 支援數據
LD%: 23.3%
GB%: 30.5%
💡 分析重點
接觸率是否不足 → 數據分析中...
場內打擊率是否偏低（運氣） → 數據分析中...
擊球型態是否不理想 → 數據分析中...
🎯 改善建議
提高接觸率：調整揮棒時機
```

---

## 🔧 技術細節

### Query Router（v4 增強）

**球員識別**：
- 中文別名：「大谷」→ Shohei Ohtani
- 英文姓氏：「Ohtani」→ Shohei Ohtani
- 完整英文名：「Aaron Judge」
- 混合查詢：「大谷 vs Judge」

**查詢分類**：
- Factual（事實型）
- Ranking（排名型）
- Comparison（比較型）

**Metric 識別**：
- 中文：「全壘打」→ HR
- 英文：「home runs」→ HR
- 縮寫：「ops」→ OPS

### Vector Search

- **模型**: `sentence-transformers/all-MiniLM-L6-v2`
- **維度**: 384
- **索引**: FAISS (IndexFlatL2)
- **優勢**: 捕捉語意相似度

### BM25 Search

- **分詞**: jieba (中文) + whitespace (英文)
- **實作**: rank-bm25 (BM25Okapi)
- **優勢**: 精確關鍵字匹配

### 混合策略

```python
final_score = α * vector_score + (1 - α) * bm25_score
```

**α 值（依查詢類型）**:
- Factual: 0.4 (平衡，略偏向語意)
- Ranking: 直接數值排序（不使用混合分數）
- Comparison: 0.4
- Analysis: 0.6 (偏向語意理解)

### 評估指標系統（v5 新增）

**即時計算**：
```python
def calculate_metrics(results, routed, k=5):
    # 相關性判斷：
     - 匹配 filter_players
     - 匹配 filter_seasons
    # 計算指標：
    - Recall@k: 找到相關文檔的比例
    - Precision@k: 前k個中相關的比例
    - MRR: 第一個相關結果的排名倒數
```

**三處顯示**：
1. **後端日誌**：即時輸出每次查詢的指標
2. **前端 Debug 面板**：點擊「🐞 Debug」查看
3. **獨立 API**：`GET /api/metrics` 查看累積統計

**自動記錄**：
- 檔案：`data/metrics_log.jsonl`
- 格式：每行一個 JSON 物件
- 用途：長期追蹤、實驗比較

---

## 📈 支援的統計類型
這裡只列出幾項常用的，詳細可以執行 `test\check_database.py` 查看。

### 打者統計（275+ 欄位）

**基本**：

| 指標  | 英文欄位     | 說明         |
| --- | -------- | ---------- |
| 打擊率 | AVG      | 打者最基本的打擊能力 |
| 安打  | Hits        | 全部安打數      |
| 全壘打 | HR       | 長打能力代表     |
| 打點  | RBI      | 攻擊貢獻       |
| 得分  | Runs (R) | 跑回本壘得分     |

**進階**：
| 指標   | 英文欄位 | 說明                 |
| ---- | ---- | ------------------ |
| 上壘率  | OBP  | 上壘能力               |
| 長打率  | SLG  | 長打火力               |
| OPS  | OPS  | 上壘＋長打              |
| wOBA | wOBA | 綜合攻擊評估             |
| wRC+ | wRC+ | 數據調整後的攻擊表現（100 平均） |

**Statcast 數據**：
| 指標            | 英文欄位          | 說明       |
| ------------- | ------------- | -------- |
| Barrel%       | Barrel%       | 高質量擊球比例   |
| 強擊球率       | HardHit%      | 擊出球的初速超過特定標準(\(95\) 英里)的比例 |
| 純長打率       | ISO           | 單次擊球最高初速 |


### 投手統計（298+ 欄位）

**基本**：
| 指標    | 英文欄位 | 說明        |
| ----- | ---- | --------- |
| 防禦率   | ERA  | 最重要投手統計   |
| 三振率    | K%   | 奪三振能力     |
| 勝場    | Wins  |  勝場    |
| 敗場    | Losses   | 敗場      |
| 救援成功    | Saves   | 救援成功      |


**進階**：
| 指標    | 英文欄位  | 說明       |
| ----- | ----- | -------- |
| WHIP  | WHIP  | 每局被上壘率   |
| FIP   | FIP   | 投手純技術表現  |
| xFIP  | xFIP  | 預期 FIP   |
| SIERA | SIERA | 技能互動 ERA |


**Statcast 數據**：
| 指標                       | 英文欄位          | 說明                          |
| ------------------------ | ------------- | --------------------------- |
| 被全壘打                     | Home_Runs_Allowed     | 被全壘打次數                      |
| K/9   | K/9   | 每 9 局三振  |
| bb/9   | K/9   | 每 9 局保送數  |


---

## 🔍 v5 新功能詳解

### 1. 評估指標系統

#### 後端日誌範例：
```
============================================================
📊 Query: Ohtani 跟 Judge 2023年的打擊數據比較

🔍 HybridSearch 返回 3 筆結果:
   1. Shohei Ohtani 2023 batter score=1.2965
   2. Aaron Judge 2023 batter score=1.1523
   3. Shohei Ohtani 2023 pitcher score=0.7965

📊 檢索評估指標:
   Recall@5: 100.0%
   Precision@5: 66.7%
   MRR: 1.000
   相關文檔: 2/3

✅ 返回 3 筆結果給前端
⏱️  響應時間: 0.23s
============================================================
```

#### 前端 Debug 面板：
點擊右上角「🐞 Debug」後顯示：
```
🔧 Debug Info: Query Router
Query Type Type: factual
Intent: null
Metric: N/A
Season: 2023
Players: Shohei Ohtani, Aaron Judge

📊 Retrieval Metrics
Recall@5: 100.0%
Precision@5: 66.7%
MRR: 1.000
Relevant: 2/3
```

#### 獨立 API：
```bash
# 訪問 API
curl http://localhost:8000/api/metrics

# 或在瀏覽器打開
http://localhost:8000/api/metrics
```

**返回範例**：
```json
{
  "ok": true,
  "total_queries": 25,
  "average_metrics": {
    "recall@k": 0.9524,
    "precision@k": 0.7143,
    "mrr": 0.8952,
    "avg_response_time": 0.234
  },
  "recent_queries": [
    {
      "timestamp": "2024-12-02T10:30:45",
      "query": "Ohtani 跟 Judge 2023 打擊",
      "metrics": {
        "recall@k": 1.0,
        "precision@k": 0.667,
        "mrr": 1.0
      }
    }
  ],
  "metrics_file": "data/metrics_log.jsonl"
}
```

#### 自動記錄檔案：
**位置**：`data/metrics_log.jsonl`

**格式**：
```json
{"timestamp": "2024-12-02T10:30:45.123456", "query": "...", "metrics": {...}, "response_time": 0.234}
{"timestamp": "2024-12-02T10:31:12.456789", "query": "...", "metrics": {...}, "response_time": 0.189}
```

**用途**：
- 長期性能追蹤
- A/B 測試比較
- 系統優化分析

## 📦 v6 新功能

### 1. 回答模板系統
- **Factual Query**：先回答主要指標，再補充相關數據
- **Ranking Query**：結構化排名列表
- **Comparison Query**：區分多球員/多賽季比較
- **AnAnalysis Query**：數據說話，沒有數據就不給意見

### 2. 改進的 Query Router
- 支援**單球員多賽季比較**（如：「Ohtani 2022 2023 全壘打」）
- 支援**多球員比較**（不要求明確 metric）

### 3. Debug 面板優化
- 加入 **Top N** 顯示（Ranking 查詢時）

### 4. 加入範例查詢
- 新增Factual/Ranking/Comparsion/Analysis 範例問題按鈕

### 5. 改善Ranking機制
- Ranking不使用hybrid_search做查詢排名，直接從lookup_engine中根據對應Metric排序

---

## 🧪 測試與評估

### 運行測試

```bash
# 系統功能測試
python test/test_system.py

# 評估數據集測試
python test/evaluate.py
```

### 查看評估指標

```bash
# Windows
type results\metrics_log.jsonl

# Mac/Linux
cat results/metrics_log.jsonl
```

### 評估指標說明

**Recall@k**:
- 定義：前 k 個結果中找到的相關文檔比例
- 計算：(前k個中相關的數量) / (總相關數量)
- 範例：查詢 "Ohtani 2023"，前5個結果包含所有2個相關結果 → Recall@5 = 100%

**Precision@k**:
- 定義：前 k 個結果中相關文檔的比例
- 計算：(前k個中相關的數量) / k
- 範例：前5個結果中有4個相關 → Precision@5 = 80%

**MRR (Mean Reciprocal Rank)**:
- 定義：第一個相關結果的排名倒數
- 計算：1 / (第一個相關結果的排名)
- 範例：
  - 第1名是相關結果 → MRR = 1.000
  - 第2名是相關結果 → MRR = 0.500

---

## 🎯 開發計劃

### 已完成

- [x] 混合檢索系統（Vector + BM25）
- [x] 智能查詢路由（中英文球員識別）
- [x] 評估指標系統（Recall@k, Precision@k, MRR）
- [x] 後端日誌顯示指標
- [x] 前端 Debug 面板
- [x] 獨立評估 API
- [x] 自動指標記錄（metrics_log.jsonl）
- [x] RAG 回答格式改進
- [x] 事實一致性驗證
- [x] 網頁界面（純 RAG + LLM 對話模式）
- [x] 雙語支援（中英文）
- [x] RAG加入分析型回答 

### 計劃中
- [ ] LLM 加入分析型回答
- [ ] LLM 對話式回答優化
- [ ] 加入人工標記評分
- [ ] 更多賽季數據
- [ ] 獎項數據整合（MVP, Gold Glove...）
- [ ] 合約與薪資資訊
- [ ] 進階視覺化圖表
- [ ] 用戶偏好記憶
- [ ] RESTful API 文檔

---

## 📚 參考文獻

1. Min et al., 2024. "Exploring the Impact of Table-to-Text Methods on Augmenting LLM-based Question Answering with Domain Hybrid Data"
2. Robertson & Zaragoza, 2009. "The Probabilistic Relevance Framework: BM25 and Beyond"
3. Reimers & Gurevych, 2019. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"
4. [FanGraphs](https://www.fangraphs.com/) - MLB Advanced Statistics
5. [Baseball Savant](https://baseballsavant.mlb.com/) - Statcast Data

---

## 📝 版本歷史

**當前版本**: v6.1.0
**最後更新**: 2024-12-04

**v6.0**
- 回答模板系統更新
- Query Router 增強（中英文球員識別）
- Comparison 查詢增強（多球員,多年份比較）
- Debug 面板優化
- 修正Ranking抓不到stats問題
- 改善Comparison二刀流選手會回答兩筆數據的問題
- 加入Analysis問題

**v5.0**
- 新增完整評估指標系統
- RAG 回答格式改進
- 獨立評估 API
- 自動指標記錄

**v4.0**
- LLM Prompt 人性化
- 前端 Debug 面板

**v3.0** 
- 完整統計數據展開
- 混合檢索優化

**v2.0** 
- LLM 對話模式
- 兩種查詢模式切換

**v1.0** 
- 初始版本
- 基礎檢索功能

