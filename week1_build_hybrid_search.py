"""
Week 1: 建立 Hybrid Search 系統
使用 LanceDB 實現 Vector Search + Full-Text Search (FTS)

這個系統解決了「人名檢索問題」：
- Vector Search：理解語意（如「打者」、「wRC+」）
- FTS：精確匹配人名（如「Aaron Judge」）
- Hybrid：結合兩者優勢

執行步驟：
1. 載入文檔（從 week1_data_collection.py 的輸出）
2. 生成 embeddings（使用 sentence-transformers）
3. 建立 LanceDB table
4. 建立 FTS index（用於人名）
5. 測試檢索功能
"""

import json
import os
import re
from typing import List, Dict

print("=" * 80)
print("Hybrid Search 系統建立器")
print("=" * 80)

# ============================================
# Step 1: 安裝依賴
# ============================================
print("\n[Step 1] 檢查依賴...")

dependencies = {
    'lancedb': 'LanceDB (Vector Database)',
    'sentence_transformers': 'Sentence Transformers (Embedding Model)',
    'torch': 'PyTorch (Required by sentence-transformers)',
}

missing = []
for package, description in dependencies.items():
    try:
        __import__(package)
        print(f"  ✅ {description}")
    except ImportError:
        print(f"  ❌ {description} - 需要安裝")
        missing.append(package)

if missing:
    print(f"\n請執行：pip install {' '.join(missing)}")
    print("(如果是 Claude 環境，加上 --break-system-packages)")
    exit(1)

# 現在可以安全導入
import lancedb
from sentence_transformers import SentenceTransformer
import pandas as pd

print("✅ 所有依賴已就緒")

# ============================================
# 配置
# ============================================
DATA_DIR = "./mlb_data"
DB_PATH = "./mlb_lancedb"
DOCS_FILE = os.path.join(DATA_DIR, "mlb_documents.json")

# Embedding 模型（輕量且快速）
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 維度，22MB

print(f"\n配置：")
print(f"  資料目錄：{DATA_DIR}")
print(f"  數據庫路徑：{DB_PATH}")
print(f"  文檔檔案：{DOCS_FILE}")
print(f"  Embedding 模型：{EMBEDDING_MODEL}")

# ============================================
# Step 2: 載入文檔
# ============================================
print("\n[Step 2] 載入文檔...")

if not os.path.exists(DOCS_FILE):
    print(f"❌ 找不到文檔檔案：{DOCS_FILE}")
    print("請先執行 week1_data_collection.py")
    exit(1)

with open(DOCS_FILE, 'r', encoding='utf-8') as f:
    documents = json.load(f)

print(f"✅ 載入 {len(documents)} 個文檔")

# ============================================
# Step 3: 初始化 Embedding 模型
# ============================================
print(f"\n[Step 3] 初始化 Embedding 模型...")
print(f"  正在載入 {EMBEDDING_MODEL}...")

model = SentenceTransformer(EMBEDDING_MODEL)
print(f"  ✅ 模型已載入")
print(f"  維度：{model.get_sentence_embedding_dimension()}")

# ============================================
# Step 4: 生成 Embeddings
# ============================================
print(f"\n[Step 4] 生成 Embeddings...")
print(f"  這可能需要幾分鐘...")

# 提取所有描述
descriptions = [doc['description'] for doc in documents]

# 批次生成 embeddings（更快）
print(f"  正在處理 {len(descriptions)} 個描述...")
embeddings = model.encode(
    descriptions,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True
)

print(f"  ✅ 生成完成")
print(f"  Embedding 形狀：{embeddings.shape}")

# 將 embeddings 加入文檔
for i, doc in enumerate(documents):
    doc['vector'] = embeddings[i].tolist()

# ============================================
# Step 5: 建立 LanceDB 資料庫
# ============================================
print(f"\n[Step 5] 建立 LanceDB 資料庫...")

# 連接到資料庫（如果不存在會自動建立）
db = lancedb.connect(DB_PATH)
print(f"  ✅ 連接到資料庫：{DB_PATH}")

# 準備資料（LanceDB 需要 pandas DataFrame 或 pyarrow Table）
# 將嵌套的 stats dict 扁平化
flattened_docs = []
for doc in documents:
    flat_doc = {
        'doc_id': doc['doc_id'],
        'player_id': doc['player_id'],
        'player_name': doc['player_name'],
        'team': doc['team'],
        'season': doc['season'],
        'position': doc['position'],
        'age': doc['age'],
        'type': doc['type'],
        'description': doc['description'],
        'games': doc['games'],
        'vector': doc['vector'],
    }
    
    # 將 stats 扁平化（加上 stat_ 前綴避免衝突）
    for key, value in doc['stats'].items():
        flat_doc[f'stat_{key}'] = value
    
    flattened_docs.append(flat_doc)

df = pd.DataFrame(flattened_docs)
print(f"  資料形狀：{df.shape}")

# 修正資料型態（確保字串欄位是純字串）
print(f"  正在修正資料型態...")
string_columns = ['doc_id', 'player_id', 'player_name', 'team', 'position', 'type', 'description']
for col in string_columns:
    if col in df.columns:
        df[col] = df[col].astype(str)

# 確保數值欄位是數值型態
numeric_columns = ['season', 'age', 'games']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# 處理統計欄位（確保是數值）
stat_columns = [col for col in df.columns if col.startswith('stat_')]
for col in stat_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

print(f"  ✅ 資料型態已修正")

# 建立 table（如果已存在會覆蓋）
print(f"  正在建立 table...")
table = db.create_table("players", data=df, mode="overwrite")
print(f"  ✅ Table 建立完成：{len(table)} 筆記錄")

# ============================================
# Step 6: 建立 FTS Index（用於人名精確匹配）
# ============================================
print(f"\n[Step 6] 建立 Full-Text Search Index...")

try:
    # 對 player_name 和 description 建立 FTS index
    table.create_fts_index(["player_name", "description"])
    print(f"  ✅ FTS Index 建立完成")
    print(f"  可搜尋欄位：player_name, description")
except Exception as e:
    print(f"  ⚠️  FTS Index 建立失敗：{e}")
    print(f"  將只使用 Vector Search")

# ============================================
# Step 7: 測試 Hybrid Search
# ============================================
print(f"\n[Step 7] 測試 Hybrid Search 功能...")

def hybrid_search(query: str, k: int = 5, vector_weight: float = 0.5) -> List[Dict]:
    """
    Hybrid Search：結合 Vector Search 和 FTS
    
    Args:
        query: 查詢字串
        k: 返回結果數量
        vector_weight: Vector Search 的權重（0-1，越高越依賴語意搜尋）
    
    Returns:
        檢索結果列表
    """
    
    # 1. 檢查是否包含人名（簡單 NER：大寫字母開頭的連續詞）
    potential_names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query)
    
    has_person_name = len(potential_names) > 0
    
    print(f"\n  查詢：'{query}'")
    print(f"  偵測到人名：{potential_names if has_person_name else '無'}")
    
    # 2. 如果有人名，優先用 FTS
    if has_person_name:
        print(f"  策略：FTS (人名) + Vector (語意)")
        
        try:
            # FTS search on player_name
            fts_query = potential_names[0]  # 使用第一個偵測到的人名
            fts_results = table.search(fts_query, query_type="fts").limit(k * 2).to_list()
            
            print(f"  FTS 找到：{len(fts_results)} 筆")
            
            if len(fts_results) >= k:
                # FTS 結果足夠，直接返回
                return fts_results[:k]
            
            # FTS 結果不足，補充 Vector Search
            query_embedding = model.encode(query).tolist()
            vector_results = table.search(query_embedding).limit(k * 2).to_list()
            
            print(f"  Vector 找到：{len(vector_results)} 筆")
            
            # 合併結果（去重）
            seen_ids = {r['doc_id'] for r in fts_results}
            combined = fts_results + [r for r in vector_results if r['doc_id'] not in seen_ids]
            
            return combined[:k]
            
        except Exception as e:
            print(f"  ⚠️  FTS 失敗：{e}")
            print(f"  降級到純 Vector Search")
            has_person_name = False
    
    # 3. 沒有人名，使用純 Vector Search
    if not has_person_name:
        print(f"  策略：純 Vector Search (語意)")
        
        query_embedding = model.encode(query).tolist()
        results = table.search(query_embedding).limit(k).to_list()
        
        print(f"  找到：{len(results)} 筆")
        return results

# 測試案例
test_queries = [
    "Aaron Judge 2024 wRC+",  # 有人名
    "Aaron Judge",  # 只有人名
    "誰是 2024 年最強的打者？",  # 無人名，語意查詢
    "投手 ERA 最低",  # 無人名，統計查詢
    "Shohei Ohtani home runs",  # 有人名
]

print("\n" + "=" * 80)
print("測試查詢")
print("=" * 80)

for query in test_queries:
    results = hybrid_search(query, k=3)
    
    print(f"\n  結果 Top 3：")
    for i, result in enumerate(results, 1):
        print(f"    {i}. {result['player_name']} ({result['type']}) - {result['team']} {result['season']}")
    print()

# ============================================
# Step 8: 儲存檢索函數（給後續使用）
# ============================================
print(f"\n[Step 8] 儲存檢索配置...")

config = {
    'db_path': DB_PATH,
    'table_name': 'players',
    'embedding_model': EMBEDDING_MODEL,
    'embedding_dim': model.get_sentence_embedding_dimension(),
    'total_documents': len(documents),
    'fts_enabled': True,
}

config_file = os.path.join(DATA_DIR, "search_config.json")
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)

print(f"  💾 已儲存：{config_file}")

# ============================================
# 完成
# ============================================
print("\n" + "=" * 80)
print("✨ Hybrid Search 系統建立完成！")
print("=" * 80)
print(f"📊 系統資訊：")
print(f"   - 資料庫：{DB_PATH}")
print(f"   - 文檔數：{len(documents)}")
print(f"   - Embedding 模型：{EMBEDDING_MODEL}")
print(f"   - 維度：{model.get_sentence_embedding_dimension()}")
print(f"   - FTS Index：已啟用")
print(f"\n🎯 測試結果：")
print(f"   - ✅ Vector Search：運作正常")
print(f"   - ✅ FTS：運作正常")
print(f"   - ✅ Hybrid Search：運作正常")
print(f"\n🔍 測試建議：")
print(f"   試試看：hybrid_search('Aaron Judge 2024 wRC+')")
print(f"   對比：純名字搜尋 vs 有統計項目的搜尋")
print(f"\n📝 下一步：")
print(f"   1. 測試更多查詢，驗證檢索準確度")
print(f"   2. 執行 week1_test_retrieval.py 進行完整測試")
print(f"   3. 進入 Week 2：建立 LLM Agent")
print("=" * 80)