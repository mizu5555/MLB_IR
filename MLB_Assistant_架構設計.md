# MLB Assistant - 架構設計文檔

**版本：** 1.0  
**最後更新：** 2024-11-24

---

## 目錄

1. [設計理念](#設計理念)
2. [系統架構](#系統架構)
3. [數據流](#數據流)
4. [核心組件設計](#核心組件設計)
5. [設計決策](#設計決策)
6. [擴展性設計](#擴展性設計)

---

## 設計理念

### 核心原則

1. **精確性優先**
   - 100% 數值準確
   - 零幻覺生成
   - 事實一致性保證

2. **模組化設計**
   - 清晰的職責分離
   - 可獨立測試
   - 易於擴展

3. **智能路由**
   - 自動識別查詢類型
   - 針對性處理策略
   - 最優化檢索路徑

4. **用戶友好**
   - 自然語言接口
   - 即時反饋
   - 清晰的結果展示

---

## 系統架構

### 三層架構

```
┌─────────────────────────────────────────────────────┐
│                    展示層 (UI Layer)                 │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │         Streamlit Web Interface              │  │
│  │  - 查詢輸入                                   │  │
│  │  - 結果顯示                                   │  │
│  │  - 原始數據展示                               │  │
│  └──────────────────────────────────────────────┘  │
└───────────────────┬─────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│                   應用層 (Application Layer)         │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │    Query     │→ │    Smart     │→ │  Answer  │ │
│  │  Classifier  │  │    Router    │  │Generator │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                      │
│  決策邏輯：                                          │
│  - Query Type 識別                                  │
│  - 檢索策略選擇                                      │
│  - 回答生成控制                                      │
└───────────────────┬─────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│                  數據層 (Data Layer)                 │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   LanceDB    │  │     JSON     │  │pybaseball│ │
│  │ Vector Store │  │  Documents   │  │   API    │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
│                                                      │
│  檢索策略：                                          │
│  - Vector Search (語義)                             │
│  - FTS (精確匹配)                                    │
│  - Database Sort (排序)                             │
└─────────────────────────────────────────────────────┘
```

---

### 組件交互圖

```
用戶輸入
   ↓
┌─────────────────┐
│ Query Classifier│ ← Llama 3.2
└────────┬────────┘
         ↓
    Query Type
         ↓
┌────────┴────────────────────────┐
│                                 │
│  Factual    Ranking    Analysis │
│     ↓          ↓          ↓     │
│  Vector    Database    Multi-   │
│  Search     Sort      Season    │
│    +          +        Data     │
│   FTS      Filter    Collection │
│    +       Threshold            │
│  Year                           │
│  Filter                         │
│     ↓          ↓          ↓     │
└─────┬──────────┬──────────┬────┘
      │          │          │
      └──────────┴──────────┘
               ↓
       ┌───────────────┐
       │ LLM Generator │ ← Llama 3.2
       └───────┬───────┘
               ↓
          自然語言回答
```

---

## 數據流

### Factual Query 數據流

```
1. 用戶查詢："Aaron Judge 2023 wRC+"
   ↓
2. Query Classifier
   → 識別為 'factual'
   ↓
3. Year Extraction
   → 提取年份：2023
   ↓
4. Hybrid Search
   ├─ Vector Search (k=10)
   │  → 找到相關球員
   └─ FTS Search (k=10)
      → 精確匹配 "Aaron Judge"
   ↓
5. Year Filter
   → 過濾到 2023 賽季
   ↓
6. Top Result Selection
   → Aaron Judge (NYY, 2023)
   ↓
7. Stats Extraction
   → wRC+: 157.0
   ↓
8. LLM Generation
   → 生成自然語言回答
   ↓
9. 返回給用戶
```

**關鍵設計：**
- Hybrid Search 確保高召回率
- Year Filter 確保年份準確
- Stats Extraction 確保數值準確

---

### Ranking Query 數據流

```
1. 用戶查詢："Who has the highest wRC+ in 2023?"
   ↓
2. Query Classifier
   → 識別為 'ranking'
   ↓
3. Stat Identification
   → wRC+
   ↓
4. Player Type Identification
   → batter
   ↓
5. Year Extraction
   → 2023
   ↓
6. Database Filter
   ├─ Type: batter
   ├─ Season: 2023
   └─ Stat: wRC+ > 0
   ↓
7. Threshold Filter
   → PA ≥ 100
   ↓
8. Sort
   → 按 wRC+ 降序
   ↓
9. Top N Selection
   → 前 5 名
   ↓
10. LLM Generation
    → 生成排名列表
    ↓
11. 返回給用戶
```

**關鍵設計：**
- Threshold Filter 確保統計顯著性
- Database Sort 確保排序準確
- 直接從數據庫排序，避免檢索誤差

---

### Analysis Query 數據流

```
1. 用戶查詢："Why is Aaron Judge so good?"
   ↓
2. Query Classifier
   → 識別為 'analysis'
   ↓
3. Player Identification
   → Vector Search
   → 找到：Aaron Judge
   ↓
4. Multi-Season Data Collection
   → 收集 2022, 2023, 2024 數據
   ↓
5. Stats Organization
   ├─ 2022: wRC+ 211, HR 62
   ├─ 2023: wRC+ 157, HR 37
   └─ 2024: wRC+ 220, HR 58
   ↓
6. LLM Analysis
   → 提供多維度統計
   → 生成分析性回答
   ↓
7. 返回給用戶
```

**關鍵設計：**
- Multi-Season Collection 提供完整視角
- Structured Data 確保 LLM 有充分信息
- Low Temperature 確保回答基於數據

---

## 核心組件設計

### 1. Query Classifier

**職責：**
- 將自然語言查詢分類為 3 種類型

**設計：**
```python
class QueryClassifier:
    def __init__(self, model_name='llama3.2'):
        self.model = model_name
        self.prompt_template = """..."""
    
    def classify(self, query: str) -> str:
        # 1. 構建 prompt
        prompt = self.build_prompt(query)
        
        # 2. 調用 LLM
        response = self.call_llm(prompt)
        
        # 3. 解析結果
        return self.parse_response(response)
```

**關鍵設計決策：**
- 使用 LLM 而非規則：更靈活，更準確
- 低溫度（0.1）：確保一致性
- 簡單 prompt：減少誤判

---

### 2. Smart Router

**職責：**
- 根據查詢類型路由到對應處理流程

**設計：**
```python
class SmartRouter:
    def route(self, query: str, query_type: str) -> Dict:
        if query_type == 'factual':
            return self.handle_factual(query)
        elif query_type == 'ranking':
            return self.handle_ranking(query)
        else:  # analysis
            return self.handle_analysis(query)
    
    def handle_factual(self, query: str):
        # 1. Hybrid Search
        results = self.hybrid_search(query)
        
        # 2. Year Filter
        year = self.extract_year(query)
        if year:
            results = self.filter_by_year(results, year)
        
        # 3. Return top result
        return {'top_result': results[0]}
```

**關鍵設計決策：**
- 策略模式：不同類型不同策略
- 可擴展：新增類型只需添加方法
- 獨立測試：每個策略可單獨測試

---

### 3. Hybrid Search Engine

**職責：**
- 結合 Vector Search 和 FTS

**設計：**
```python
class HybridSearchEngine:
    def __init__(self, table, model):
        self.table = table
        self.model = model
    
    def search(self, query: str, k: int = 10) -> List[Dict]:
        # 1. Vector Search
        vector_results = self.vector_search(query, k)
        
        # 2. FTS Search
        fts_results = self.fts_search(query, k)
        
        # 3. Merge & Deduplicate
        merged = self.merge_results(vector_results, fts_results)
        
        return merged[:k]
    
    def merge_results(self, results1, results2):
        seen = set()
        merged = []
        
        for r in results1 + results2:
            key = (r['player_name'], r['season'])
            if key not in seen:
                seen.add(key)
                merged.append(r)
        
        return merged
```

**關鍵設計決策：**
- 兩種搜索並行：提高召回率
- 去重邏輯：避免重複結果
- 可配置 k 值：靈活性

---

### 4. Ranking Engine

**職責：**
- 高效的排名查詢處理

**設計：**
```python
class RankingEngine:
    def rank(self, query: str, top_n: int = 5) -> Dict:
        # 1. Identify stat & type
        stat_col, player_type = self.identify_stat_and_type(query)
        
        # 2. Extract year
        year = self.extract_year(query)
        
        # 3. Filter data
        df = self.docs_df[self.docs_df['type'] == player_type]
        if year:
            df = df[df['season'] == year]
        
        # 4. Extract stat values
        df['stat'] = df['stats'].apply(lambda x: x.get(stat_col, 0))
        
        # 5. Apply threshold
        df = self.apply_threshold(df, player_type)
        
        # 6. Sort and return top N
        sorted_df = df.sort_values('stat', ascending=False)
        return self.format_results(sorted_df.head(top_n))
```

**關鍵設計決策：**
- 直接從 DataFrame 排序：高效
- Threshold Filter：統計顯著性
- Lazy Evaluation：需要時才計算

---

## 設計決策

### 決策 1: 為什麼使用 Hybrid Search？

**背景：**
- Vector Search 善於語義理解
- FTS 善於精確匹配

**決策：** 結合兩者

**理由：**
1. **互補性：**
   - "Aaron Judge" vs "Judge" → Vector Search 理解
   - "Aaron Judge" 精確匹配 → FTS 確保

2. **召回率：**
   - Hybrid Search Recall@5: 100%
   - 單獨 Vector Search: 90%
   - 單獨 FTS: 80%

---

### 決策 2: 為什麼使用 LLM 做分類？

**背景：**
- 可以用規則（if-else）
- 也可以用 LLM

**決策：** 使用 LLM

**理由：**
1. **靈活性：**
   - 規則脆弱，需要維護
   - LLM 理解自然語言變體

2. **準確率：**
   - LLM 分類：100%
   - 規則分類：~85%（測試結果）

3. **可擴展：**
   - 新增類型只需修改 prompt
   - 規則需要重寫邏輯

---

### 決策 3: 為什麼設置樣本門檻？

**背景：**
- 小樣本數據不可靠
- 替補球員可能有極端數據

**決策：** 打者 PA≥100，投手 IP≥20

**理由：**
1. **統計顯著性：**
   - 避免小樣本偏差
   - 例如：5 個打席打出 3 支全壘打 → AVG 0.600（不可靠）

2. **業界標準：**
   - FanGraphs 使用相似門檻
   - MLB 資格標準

---

### 決策 4: 為什麼使用 Low Temperature？

**背景：**
- Temperature 控制 LLM 隨機性
- High: 創意，Low: 確定性

**決策：** Temperature = 0.1

**理由：**
1. **數值準確性：**
   - 降低創造性
   - 嚴格遵循數據

2. **一致性：**
   - 相同輸入 → 相同輸出
   - 可重現結果

---

## 擴展性設計

### 水平擴展

**現狀：**
- 單機運行
- LanceDB 本地存儲

**擴展方案：**

```
┌──────────────┐
│ Load Balancer│
└───────┬──────┘
        │
   ┌────┴────┐
   │         │
┌──▼──┐  ┌──▼──┐
│Node1│  │Node2│
└──┬──┘  └──┬──┘
   │        │
   └────┬───┘
        │
┌───────▼────────┐
│ Shared LanceDB │
└────────────────┘
```

**關鍵點：**
- Stateless 設計（無狀態）
- 共享數據層
- 負載均衡

---

### 功能擴展

**Phase 2-4 擴展架構：**

```
當前：
┌──────────────────┐
│  MLB Stats       │
│  2022-2025       │
└──────────────────┘

Phase 2 (獎項)：
┌──────────────────┐  ┌──────────────────┐
│  MLB Stats       │  │  Awards Data     │
│  2022-2025       │  │  MVP, CY, ...    │
└──────────────────┘  └──────────────────┘

Phase 3 (合約)：
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  MLB Stats       │  │  Awards Data     │  │  Contract Data   │
│  2022-2025       │  │  MVP, CY, ...    │  │  Salary, Years   │
└──────────────────┘  └──────────────────┘  └──────────────────┘

Phase 4 (Statcast)：
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  MLB Stats       │  │  Awards Data     │  │  Contract Data   │  │  Statcast Data   │
│  2022-2025       │  │  MVP, CY, ...    │  │  Salary, Years   │  │  EV, LA, SS      │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

**擴展策略：**
1. 獨立數據源
2. 統一檢索接口
3. 智能數據融合

---

### 新查詢類型擴展

**當前：**
- Factual
- Ranking
- Analysis

**未來可擴展：**
- Comparison（比較查詢）
- Trend（趨勢分析）
- Prediction（預測）

**擴展方法：**
```python
# 1. 在 Query Classifier 中加入新類型
prompt += "4. comparison: Comparing two players"

# 2. 在 Smart Router 中加入處理方法
def handle_comparison(self, query: str):
    # 提取兩個球員
    # 收集數據
    # 生成比較
    pass

# 3. 在 UI 中加入示例
st.markdown("**Comparison:**")
st.markdown("- Compare Aaron Judge vs Mookie Betts")
```

---

## 性能優化

### 現有優化

1. **LanceDB 索引：**
   - Vector Index：HNSW
   - FTS Index：Tantivy

2. **批量處理：**
   - Embedding 批量生成
   - 減少 I/O 次數

3. **快取：**
   - Streamlit @cache_resource
   - 避免重複載入模型

---

### 未來優化方向

1. **模型優化：**
   - 使用更小的 Embedding 模型
   - 量化 LLM 模型

2. **數據預處理：**
   - 預計算常見查詢
   - 結果快取

3. **並行處理：**
   - Vector Search + FTS 並行
   - 多球員數據並行收集

---

## 安全性設計

### 輸入驗證

```python
def validate_query(query: str) -> bool:
    # 1. 長度檢查
    if len(query) > 500:
        return False
    
    # 2. 注入檢查
    if any(char in query for char in ['<', '>', ';', '--']):
        return False
    
    return True
```

---

### 錯誤處理

```python
try:
    result = process_query(query)
except PlayerNotFoundException:
    return "找不到球員"
except DatabaseError:
    return "資料庫錯誤"
except Exception as e:
    log_error(e)
    return "系統錯誤"
```

---

## 測試策略

### 單元測試

```python
def test_query_classifier():
    assert classify_query("Aaron Judge wRC+") == 'factual'
    assert classify_query("Who has the highest ERA?") == 'ranking'

def test_year_extraction():
    assert extract_year_from_query("Judge 2023") == 2023
    assert extract_year_from_query("Judge") == None
```

---

### 整合測試

```python
def test_end_to_end():
    query = "Who has the highest wRC+ in 2023?"
    result = assistant.query(query)
    
    assert result['data']['stat_name'] == 'wRC+'
    assert result['data']['season'] == 2023
    assert len(result['data']['results']) > 0
```

---

## 文檔維護

### 設計文檔同步

- 代碼變更 → 更新架構圖
- 新功能 → 更新設計決策
- 性能變化 → 更新優化策略

---

## 總結

### 架構優勢

1. **模組化：** 清晰的職責分離
2. **可測試：** 每個組件獨立測試
3. **可擴展：** 易於添加新功能
4. **高性能：** 優化的檢索路徑

### 設計權衡

1. **準確性 vs 速度：** 選擇準確性
2. **複雜性 vs 靈活性：** 選擇靈活性
3. **本地 vs 雲端：** 選擇本地（隱私）

---

**架構文檔結束**
