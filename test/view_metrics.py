"""
Metrics 查看工具

使用方法：
1. 啟動 app.py
2. 執行此腳本查看累積指標
"""

import requests
import json

def view_metrics():
    url = "http://localhost:8000/api/metrics"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data.get("ok"):
            print("❌ 無法取得指標")
            return
        
        print("=" * 60)
        print("📊 MLB RAG System - Retrieval Metrics")
        print("=" * 60)
        
        if data.get("total_queries", 0) == 0:
            print("\n⚠️ 尚無查詢記錄")
            print("請先在前端執行一些查詢。")
            return
        
        print(f"\n📈 總查詢次數: {data['total_queries']}")
        print("\n平均指標:")
        
        avg = data.get("average_metrics", {})
        print(f"  • Recall@k:    {avg.get('recall@k', 0):.1%}")
        print(f"  • Precision@k: {avg.get('precision@k', 0):.1%}")
        print(f"  • MRR:         {avg.get('mrr', 0):.3f}")
        print(f"  • 響應時間:     {avg.get('avg_response_time', 0):.3f}s")
        
        print(f"\n📁 記錄檔案: {data.get('metrics_file')}")
        
        recent = data.get("recent_queries", [])
        if recent:
            print(f"\n🔍 最近 {len(recent)} 筆查詢:")
            for i, q in enumerate(recent[-5:], 1):  # 只顯示最後 5 筆
                print(f"\n  {i}. {q['query']}")
                print(f"     時間: {q['timestamp']}")
                print(f"     Recall: {q['metrics']['recall@k']:.1%}, "
                      f"Precision: {q['metrics']['precision@k']:.1%}, "
                      f"MRR: {q['metrics']['mrr']:.3f}")
        
        print("\n" + "=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器")
        print("請確認 app.py 已啟動（http://localhost:8000）")
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    view_metrics()
