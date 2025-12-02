# 修正版本

## 📦 檔案
- `app_fixed_v2.py` - 後端
- `index_fixed_v2.html` - 前端

## 🚀 執行順序

```bash
# 1. 替換
cd C:\Users\mingju\Desktop\IR\project
copy app_fixed_v2.py src\web\app.py
copy index_fixed_v2.html src\web\static\index.html

# 2. 啟動
cd src\web
python app.py

# 3. 測試
# 開啟 http://localhost:8000
# 輸入：大谷 2023 投球
```

## 🔍 修正內容

### 問題 1: 排序錯誤
- **增加詳細 debug 日誌**
- **確保序列化時保持順序**

### 問題 2: 數量寫死
- **改為動態顯示 `{len(hits)} 筆`**
- **預設 topk = 5**

### 問題 3: 點開空白
- **確保 `stats` 完整傳遞**
- **前端增加 debug console.log**
- **顯示「無詳細統計」提示**

## 📋 觀察後端日誌

應該看到：

```
====================================
📊 Query: 大谷 2023 投球
   Type: factual, Metric: None, Mode: rag, TopK: 5

🔍 HybridSearch 返回 5 筆結果:
   1. Shohei Ohtani 2023 pitcher score=1.2965
   2. Shohei Ohtani 2023 batter score=0.6797
   ...

🔄 開始序列化 5 筆結果:
   序列化 1: Shohei Ohtani 2023 pitcher score=1.2965 stats_keys=['ERA', 'WHIP', 'K%']
   序列化 2: Shohei Ohtani 2023 batter score=0.6797 stats_keys=['AVG', 'HR', 'OPS']
   ...

✅ 序列化完成: 5 筆
   前3名: [('Shohei Ohtani', 'pitcher', 1.2965), ('Shohei Ohtani', 'batter', 0.6797), ...]

✅ 返回 5 筆結果給前端
====================================
```

## 📋 觀察前端

### 控制台 (F12)
```
API Response: {...}
Search Results: [{...}, {...}, ...]
Card 0: Shohei Ohtani pitcher stats keys: ['ERA', 'WHIP', 'K%', ...]
Card 1: Shohei Ohtani batter stats keys: ['AVG', 'HR', 'OPS', ...]
```

### 顯示結果
```
找到 5 筆相關數據。前 3 名最相關的結果：

1. Shohei Ohtani (2023 LAA) - pitcher | ERA: 3.14
2. Shohei Ohtani (2023 LAA) - batter | HR: 44
3. ...

（共 5 筆結果，請展開「檢索來源」查看完整資料）

查看 5 筆原始數據來源（點擊展開）
  ▶ Shohei Ohtani (2023) - LAA [投手] | Score: 1.297
  ▶ Shohei Ohtani (2023) - LAA [打者] | Score: 0.680
  ...
```

### 點擊展開後
```
▼ Shohei Ohtani (2023) - LAA [投手] | Score: 1.297
  ERA: 3.14    WHIP: 1.28    K/9: 12.38    FIP: 3.16
  W: 10        L: 5          SV: 0         IP: 132.0
```

## 🐛 如果還有問題

貼上：
1. 後端完整日誌（從 `====` 開始到結束）
2. 前端 console (F12) 的輸出
3. 前端顯示的結果
