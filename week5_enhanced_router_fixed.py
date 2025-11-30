"""
Week 5: 修復版智能路由器
修復球員名字提取問題
"""

import json
import re
from typing import Dict, List, Optional
import requests


def extract_player_name(query: str) -> Optional[str]:
    """
    從查詢中提取球員名字
    
    改進的提取邏輯：
    1. 常見球員名字模式
    2. 姓氏模式
    3. 全名模式
    """
    
    query_lower = query.lower()
    
    # 知名球員快速匹配（優先級最高）
    known_players = {
        'judge': 'Aaron Judge',
        'aaron judge': 'Aaron Judge',
        'ohtani': 'Shohei Ohtani',
        'shohei ohtani': 'Shohei Ohtani',
        'trout': 'Mike Trout',
        'mike trout': 'Mike Trout',
        'soto': 'Juan Soto',
        'juan soto': 'Juan Soto',
        'acuna': 'Ronald Acuña Jr.',
        'ronald acuna': 'Ronald Acuña Jr.',
        'betts': 'Mookie Betts',
        'mookie betts': 'Mookie Betts',
        'freeman': 'Freddie Freeman',
        'freddie freeman': 'Freddie Freeman',
        'cole': 'Gerrit Cole',
        'gerrit cole': 'Gerrit Cole',
        'verlander': 'Justin Verlander',
        'justin verlander': 'Justin Verlander',
        'strider': 'Spencer Strider',
        'spencer strider': 'Spencer Strider',
    }
    
    for key, full_name in known_players.items():
        if key in query_lower:
            return full_name
    
    # 通用名字模式：First Last 或 Last
    # 匹配大寫開頭的連續詞
    patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',  # First Middle Last 或 First Last
        r'\b([A-Z][a-z]+)\b',  # Last name only
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, query)
        if matches:
            return matches[0]
    
    return None


def handle_award_query(query: str, awards_data: Dict) -> str:
    """處理獎項查詢"""
    
    player_name = extract_player_name(query)
    
    if not player_name:
        return "請指定球員名字，例如：\"Has Aaron Judge won MVP?\""
    
    # 查找球員獎項
    if player_name not in awards_data:
        return f"找不到 {player_name} 的獎項數據"
    
    player_awards = awards_data[player_name]
    
    # 格式化輸出
    result = f"{player_name} 的獎項：\n"
    
    total_count = 0
    for award_type, years in sorted(player_awards.items()):
        if award_type == 'total_count':
            total_count = years
            continue
        
        if isinstance(years, list) and years:
            count = len(years)
            years_str = ", ".join(map(str, sorted(years)))
            result += f"• {award_type}: {count} 次 ({years_str})\n"
    
    result += f"總計：{total_count} 個獎項"
    
    return result


def handle_contract_query(query: str, salary_data: Dict) -> str:
    """處理合約查詢"""
    
    player_name = extract_player_name(query)
    
    if not player_name:
        return "請指定球員名字，例如：\"What is Aaron Judge's salary?\""
    
    # 查找球員薪資
    if player_name not in salary_data:
        return f"找不到 {player_name} 的薪資數據"
    
    contract_info = salary_data[player_name]
    
    # 格式化輸出
    result = f"{player_name} 的合約資訊：\n"
    result += f"• 年薪: ${contract_info['current_salary']:,}\n"
    result += f"• 年份: {contract_info['year']}\n"
    result += f"• 球隊: {contract_info['team']}\n"
    result += f"• 合約年限: {contract_info['contract_years']} 年\n"
    result += f"• 合約總額: ${contract_info['total_value']:,}"
    
    return result


def handle_statcast_query(query: str) -> str:
    """處理 Statcast 查詢"""
    
    player_name = extract_player_name(query)
    
    if not player_name:
        return "請指定球員名字，例如：\"What is Aaron Judge's exit velocity?\""
    
    # 目前 Statcast 數據尚未收集
    return f"Statcast 數據收集中...\n球員: {player_name}\n即將在 Phase 4 加入！"


def classify_query(query: str) -> str:
    """分類查詢類型（簡化版）"""
    
    query_lower = query.lower()
    
    # 獎項關鍵字
    award_keywords = ['award', 'mvp', 'cy young', 'rookie', 'all-star', 
                      'gold glove', 'silver slugger', 'won', 'win']
    
    # 合約關鍵字
    contract_keywords = ['salary', 'contract', 'paid', 'money', 'aav', 
                         'deal', 'signing', 'extension']
    
    # Statcast 關鍵字
    statcast_keywords = ['exit velocity', 'launch angle', 'barrel', 
                        'sprint speed', 'spin rate', 'whiff', 'chase']
    
    if any(keyword in query_lower for keyword in award_keywords):
        return 'award'
    elif any(keyword in query_lower for keyword in contract_keywords):
        return 'contract'
    elif any(keyword in query_lower for keyword in statcast_keywords):
        return 'statcast'
    else:
        return 'factual'


def test_enhanced_router():
    """測試改進的路由器"""
    
    print("=" * 80)
    print("測試修復版智能路由器")
    print("=" * 80)
    
    # 載入數據
    try:
        with open('./mlb_data/week5_awards.json', 'r', encoding='utf-8') as f:
            awards_data = json.load(f)
        
        with open('./mlb_data/week5_salaries.json', 'r', encoding='utf-8') as f:
            salary_data = json.load(f)
    except Exception as e:
        print(f"❌ 載入數據失敗: {e}")
        return
    
    # 測試查詢
    test_queries = [
        "Has Aaron Judge won MVP?",
        "What is Aaron Judge's salary?",
        "What is Aaron Judge's exit velocity?",
        "List all awards for Shohei Ohtani",
        "What is Gerrit Cole's contract?",
        "Show me Mike Trout's barrel rate",
    ]
    
    for query in test_queries:
        print(f"\n查詢: {query}")
        
        # 分類
        query_type = classify_query(query)
        print(f"類型: {query_type}")
        print("-" * 80)
        
        # 路由
        if query_type == 'award':
            result = handle_award_query(query, awards_data)
        elif query_type == 'contract':
            result = handle_contract_query(query, salary_data)
        elif query_type == 'statcast':
            result = handle_statcast_query(query)
        else:
            result = "此查詢類型需要其他處理邏輯"
        
        print(result)
    
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)
    print("\n球員名字提取測試:")
    
    # 測試球員名字提取
    test_names = [
        "What is Aaron Judge's salary?",
        "Has Shohei Ohtani won MVP?",
        "Show me Judge's stats",
        "Tell me about Trout",
        "What about Cole's ERA?",
    ]
    
    for query in test_names:
        player = extract_player_name(query)
        print(f"  查詢: {query}")
        print(f"  提取: {player}\n")


if __name__ == "__main__":
    test_enhanced_router()
