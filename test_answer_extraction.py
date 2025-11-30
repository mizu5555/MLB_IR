"""
測試答案提取功能
"""

import re

def test_extract_answer():
    """測試答案提取"""
    
    # 模擬的檢索結果
    test_cases = [
        {
            'query': 'Aaron Judge 2022年打了幾支全壘打？',
            'player_id': 'Aaron Judge_2022',
            'full_text': 'Player: Aaron Judge. Full Name: Aaron Judge. Season: 2022. Type: batter. HR: 62. BA: 0.311. OPS: 1.111. Exit Velocity: 95.8 mph.',
            'expected': 'Aaron Judge 在 2022 年打了 62 支全壘打'
        },
        {
            'query': 'What was Juan Soto batting average in 2024?',
            'player_id': 'Juan Soto_2024',
            'full_text': 'Player: Juan Soto. Full Name: Juan Soto. Season: 2024. Type: batter. BA: 0.288. AVG: 0.288. OPS: 0.989.',
            'expected': "Juan Soto's batting average in 2024 was 0.288"
        },
        {
            'query': 'Shohei Ohtani 2023年的ERA是多少？',
            'player_id': 'Shohei Ohtani_2023',
            'full_text': 'Player: Shohei Ohtani. Season: 2023. Type: pitcher. ERA: 3.14. WHIP: 1.06. K%: 28.5%.',
            'expected': 'Shohei Ohtani 在 2023 年的防禦率為 3.14'
        }
    ]
    
    print("測試答案提取功能")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n測試 {i}: {test['query']}")
        print(f"數據: {test['full_text'][:100]}...")
        
        # 提取球員名和賽季
        player_match = re.search(r'Player: ([^.]+)\.', test['full_text'])
        season_match = re.search(r'Season: (\d+)', test['full_text'])
        
        player_name = player_match.group(1) if player_match else test['player_id'].split('_')[0]
        season = season_match.group(1) if season_match else 'Unknown'
        
        print(f"球員: {player_name}, 賽季: {season}")
        
        # 測試統計提取
        query_lower = test['query'].lower()
        
        # 全壘打測試
        if '全壘打' in query_lower or 'home run' in query_lower:
            patterns = [
                r'HR[:\s]+(\d+)',
                r'Home Runs[:\s]+(\d+)',
            ]
            for p in patterns:
                match = re.search(p, test['full_text'], re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if '全壘打' in query_lower:
                        answer = f"{player_name} 在 {season} 年打了 {value} 支全壘打"
                    else:
                        answer = f"{player_name} hit {value} home runs in {season}"
                    print(f"✅ 提取答案: {answer}")
                    print(f"   預期答案: {test['expected']}")
                    break
        
        # 打擊率測試
        elif 'batting average' in query_lower or '打擊率' in query_lower:
            patterns = [
                r'BA[:\s]+([0-9.]+)',
                r'AVG[:\s]+([0-9.]+)',
                r'Batting Average[:\s]+([0-9.]+)',
            ]
            for p in patterns:
                match = re.search(p, test['full_text'], re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if '打擊率' in query_lower:
                        answer = f"{player_name} 在 {season} 年的打擊率為 {value}"
                    else:
                        answer = f"{player_name}'s batting average in {season} was {value}"
                    print(f"✅ 提取答案: {answer}")
                    print(f"   預期答案: {test['expected']}")
                    break
        
        # ERA 測試
        elif 'era' in query_lower or '防禦率' in query_lower:
            pattern = r'ERA[:\s]+([0-9.]+)'
            match = re.search(pattern, test['full_text'], re.IGNORECASE)
            if match:
                value = match.group(1)
                if '防禦率' in query_lower:
                    answer = f"{player_name} 在 {season} 年的防禦率為 {value}"
                else:
                    answer = f"{player_name}'s ERA in {season} was {value}"
                print(f"✅ 提取答案: {answer}")
                print(f"   預期答案: {test['expected']}")
    
    print("\n" + "=" * 80)
    print("✅ 測試完成")


if __name__ == "__main__":
    test_extract_answer()
