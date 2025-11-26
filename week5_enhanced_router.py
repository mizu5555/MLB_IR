"""
Week 5: 擴展智能路由器
處理 6 種查詢類型：Factual, Ranking, Analysis, Award, Contract, Statcast
"""

import json
import ollama
from typing import Dict, List, Optional


class EnhancedSmartRouter:
    """
    擴展智能路由器
    
    處理 6 種查詢類型：
    1. Factual - 事實查詢
    2. Ranking - 排名查詢
    3. Analysis - 分析查詢
    4. Award - 獎項查詢 ✨
    5. Contract - 合約查詢 ✨
    6. Statcast - Statcast 查詢 ✨
    """
    
    def __init__(self, documents_path: str, model_name: str = "llama3.2"):
        self.documents_path = documents_path
        self.model_name = model_name
        self.documents = self.load_documents()
    
    
    def load_documents(self) -> List[Dict]:
        """載入球員文檔"""
        try:
            with open(self.documents_path, 'r', encoding='utf-8') as f:
                docs = json.load(f)
            print(f"✅ 載入 {len(docs)} 筆球員文檔")
            return docs
        except Exception as e:
            print(f"❌ 載入文檔失敗: {e}")
            return []
    
    
    def handle_award_query(self, query: str, player_name: Optional[str] = None) -> Dict:
        """
        處理獎項查詢
        
        Args:
            query: 查詢字串
            player_name: 球員名字（如果已知）
        
        Returns:
            {
                'type': 'award',
                'player': str,
                'awards': {...},
                'answer': str
            }
        """
        
        # 如果沒有指定球員，嘗試從查詢中提取
        if not player_name:
            player_name = self.extract_player_name(query)
        
        if not player_name:
            return {
                'type': 'award',
                'error': '無法識別球員名字',
                'answer': '請指定球員名字，例如："Has Aaron Judge won MVP?"'
            }
        
        # 搜尋球員
        player_docs = [doc for doc in self.documents if doc['player_name'] == player_name]
        
        if not player_docs:
            return {
                'type': 'award',
                'error': '找不到球員',
                'answer': f'找不到球員 {player_name} 的數據'
            }
        
        # 取第一筆（任一年份都可以，因為獎項數據是累積的）
        player = player_docs[0]
        awards = player.get('awards', {'total_count': 0})
        
        # 生成回答
        if awards.get('total_count', 0) == 0:
            answer = f"{player_name} 在記錄中沒有獲得過獎項。"
        else:
            answer = f"{player_name} 的獎項：\n\n"
            for award_type, years in awards.items():
                if award_type != 'total_count' and years:
                    years_sorted = sorted(years)
                    answer += f"• {award_type}: {len(years)} 次 ({', '.join(map(str, years_sorted))})\n"
            answer += f"\n總計：{awards['total_count']} 個獎項"
        
        return {
            'type': 'award',
            'player': player_name,
            'awards': awards,
            'answer': answer
        }
    
    
    def handle_contract_query(self, query: str, player_name: Optional[str] = None) -> Dict:
        """
        處理合約/薪資查詢
        
        Args:
            query: 查詢字串
            player_name: 球員名字（如果已知）
        
        Returns:
            {
                'type': 'contract',
                'player': str,
                'contract': {...},
                'answer': str
            }
        """
        
        # 如果沒有指定球員，嘗試從查詢中提取
        if not player_name:
            player_name = self.extract_player_name(query)
        
        if not player_name:
            return {
                'type': 'contract',
                'error': '無法識別球員名字',
                'answer': '請指定球員名字，例如："What is Aaron Judge\'s salary?"'
            }
        
        # 搜尋球員
        player_docs = [doc for doc in self.documents if doc['player_name'] == player_name]
        
        if not player_docs:
            return {
                'type': 'contract',
                'error': '找不到球員',
                'answer': f'找不到球員 {player_name} 的數據'
            }
        
        # 取第一筆
        player = player_docs[0]
        contract = player.get('contract', None)
        
        # 生成回答
        if not contract:
            answer = f"{player_name} 的薪資數據暫無記錄。"
        else:
            salary = contract['current_salary']
            year = contract['year']
            team = contract['team']
            answer = f"{player_name} 的合約資訊：\n\n"
            answer += f"• 當前薪資：${salary:,}\n"
            answer += f"• 年份：{year}\n"
            answer += f"• 球隊：{team}"
        
        return {
            'type': 'contract',
            'player': player_name,
            'contract': contract,
            'answer': answer
        }
    
    
    def handle_statcast_query(self, query: str, player_name: Optional[str] = None) -> Dict:
        """
        處理 Statcast 查詢
        
        Args:
            query: 查詢字串
            player_name: 球員名字（如果已知）
        
        Returns:
            {
                'type': 'statcast',
                'player': str,
                'statcast': {...},
                'answer': str
            }
        """
        
        # 如果沒有指定球員，嘗試從查詢中提取
        if not player_name:
            player_name = self.extract_player_name(query)
        
        if not player_name:
            return {
                'type': 'statcast',
                'error': '無法識別球員名字',
                'answer': '請指定球員名字，例如："What is Aaron Judge\'s exit velocity?"'
            }
        
        # 搜尋球員
        player_docs = [doc for doc in self.documents if doc['player_name'] == player_name]
        
        if not player_docs:
            return {
                'type': 'statcast',
                'error': '找不到球員',
                'answer': f'找不到球員 {player_name} 的數據'
            }
        
        # 取第一筆
        player = player_docs[0]
        statcast = player.get('statcast', None)
        
        # 生成回答
        if not statcast or statcast.get('note') == 'Statcast 數據待補充':
            answer = f"{player_name} 的 Statcast 數據尚未完全收集。\n"
            answer += "Statcast 數據收集需要較長時間，建議使用批量處理。"
        else:
            answer = f"{player_name} 的 Statcast 指標：\n\n"
            for metric, value in statcast.items():
                if metric not in ['note', 'years_available', 'metrics']:
                    answer += f"• {metric}: {value}\n"
        
        return {
            'type': 'statcast',
            'player': player_name,
            'statcast': statcast,
            'answer': answer
        }
    
    
    def extract_player_name(self, query: str) -> Optional[str]:
        """
        從查詢中提取球員名字
        
        使用 LLM 提取
        """
        
        system_prompt = """從查詢中提取球員名字。

只回傳球員名字，不要其他內容。
如果找不到球員名字，回傳 "NONE"。

範例：
查詢："Has Aaron Judge won MVP?"
回答：Aaron Judge

查詢："Who has the highest salary?"
回答：NONE"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                options={"temperature": 0.1}
            )
            
            player_name = response['message']['content'].strip()
            
            if player_name == "NONE" or not player_name:
                return None
            
            return player_name
            
        except Exception as e:
            print(f"提取球員名字失敗: {e}")
            return None
    
    
    def route(self, query: str, query_type: str) -> Dict:
        """
        路由查詢到對應的處理函數
        
        Args:
            query: 查詢字串
            query_type: 查詢類型
        
        Returns:
            查詢結果
        """
        
        if query_type == 'award':
            return self.handle_award_query(query)
        
        elif query_type == 'contract':
            return self.handle_contract_query(query)
        
        elif query_type == 'statcast':
            return self.handle_statcast_query(query)
        
        else:
            return {
                'type': query_type,
                'answer': f'查詢類型 {query_type} 的處理函數尚未實現（使用原有系統處理）'
            }


# ============================================
# 測試
# ============================================

if __name__ == "__main__":
    
    # 假設已有整合後的文檔
    documents_path = "./mlb_data/week5_mlb_documents_enhanced.json"
    
    router = EnhancedSmartRouter(documents_path)
    
    test_queries = [
        ("Has Aaron Judge won MVP?", "award"),
        ("What is Aaron Judge's salary?", "contract"),
        ("What is Aaron Judge's exit velocity?", "statcast"),
    ]
    
    print("=" * 80)
    print("測試擴展智能路由器")
    print("=" * 80)
    
    for query, query_type in test_queries:
        print(f"\n查詢: {query}")
        print(f"類型: {query_type}")
        print("-" * 80)
        
        result = router.route(query, query_type)
        print(result['answer'])
