"""
Prompt Templates
提示詞模板：防止幻覺，確保事實一致性
"""


class PromptTemplates:
    """
    提示詞模板管理器
    
    核心原則：
    1. 強制基於檢索結果回答
    2. 明確禁止編造數據
    3. 要求引用數據來源
    4. 結構化輸出
    """
    
    @staticmethod
    def get_factual_prompt(query: str, search_results: list, language: str = 'zh') -> str:
        """
        Factual 查詢的提示詞
        用於查詢特定球員的具體數據
        """
        
        # 構建檢索結果文字
        results_text = PromptTemplates._format_search_results(search_results)
        
        if language == 'zh':
            prompt = f"""你是一個專業的MLB數據助手。請根據以下檢索到的數據回答用戶問題。

用戶問題：{query}

檢索到的數據：
{results_text}

回答要求：
1. **只使用檢索到的數據**：絕對不要編造任何數字或事實
2. **仔細檢查年份**：如果問題中提到特定年份（如2022、2023、2024），請確保從對應的 "Season: YYYY" 記錄中提取數據
3. **直接回答問題**：先給出明確的答案（數值或事實），再提供細節
4. **引用數據來源**：明確說明數據來自哪位球員的哪個賽季（例如："根據 Aaron Judge 2022年的數據..."）
5. **保持簡潔**：只提供相關信息，不要過度延伸

重要提醒：
- 檢索結果中的 "Season: YYYY" 表示賽季年份
- 如果問題問的是2022年，就要從 "Season: 2022" 的記錄中找數據
- 不同年份的數據不要混淆

如果檢索結果中沒有相關數據，請明確說明"檢索結果中沒有找到相關數據"，不要猜測。

請用繁體中文回答。"""

        else:  # English
            prompt = f"""You are a professional MLB data assistant. Answer the user's question based on the retrieved data below.

User Question: {query}

Retrieved Data:
{results_text}

Requirements:
1. **Use ONLY the retrieved data**: Never fabricate any numbers or facts
2. **Check the season carefully**: If the question mentions a specific year (e.g., 2022, 2023, 2024), ensure you extract data from the record with "Season: YYYY"
3. **Answer directly**: Provide the answer (number or fact) first, then details
4. **Cite sources clearly**: State which player and which season the data comes from (e.g., "Based on Aaron Judge's 2022 data...")
5. **Be concise**: Only provide relevant information

Important reminder:
- "Season: YYYY" in the retrieved data indicates the season year
- If the question asks about 2022, find data from "Season: 2022" records
- Don't mix up data from different years

If the retrieved data doesn't contain relevant information, clearly state "No relevant data found in the search results" instead of guessing.

Please respond in English."""
        
        return prompt
    
    @staticmethod
    def get_ranking_prompt(query: str, search_results: list, language: str = 'zh') -> str:
        """
        Ranking 查詢的提示詞
        用於排名和比較多個球員
        """
        
        results_text = PromptTemplates._format_search_results(search_results)
        
        if language == 'zh':
            prompt = f"""你是一個專業的MLB數據助手。請根據以下檢索到的數據回答用戶的排名問題。

用戶問題：{query}

檢索到的數據：
{results_text}

回答要求：
1. **只使用檢索到的數據**：絕對不要編造任何排名或數字
2. **按照實際數值排序**：根據具體指標的數值進行排序
3. **列出完整排名**：使用編號列表（1. 2. 3.）清楚呈現
4. **包含具體數值**：每個球員都要附上相關統計數據
5. **說明排序依據**：明確說明是根據什麼指標排序的

排名格式範例：
根據 [指標]，排名如下：
1. [球員名] ([賽季]) - [指標]: [數值]
2. [球員名] ([賽季]) - [指標]: [數值]
...

如果檢索結果不足以建立排名，請說明"檢索結果不足，無法建立完整排名"。

請用繁體中文回答。"""

        else:  # English
            prompt = f"""You are a professional MLB data assistant. Answer the user's ranking question based on the retrieved data below.

User Question: {query}

Retrieved Data:
{results_text}

Requirements:
1. **Use ONLY the retrieved data**: Never fabricate rankings or numbers
2. **Sort by actual values**: Rank based on the specific metric values
3. **List complete rankings**: Use numbered list (1. 2. 3.) for clarity
4. **Include specific values**: Attach relevant statistics for each player
5. **State ranking criteria**: Clearly mention what metric is used for ranking

Ranking format example:
Based on [metric], the rankings are:
1. [Player Name] ([Season]) - [Metric]: [Value]
2. [Player Name] ([Season]) - [Metric]: [Value]
...

If there's insufficient data for ranking, state "Insufficient data for complete ranking".

Please respond in English."""
        
        return prompt
    
    @staticmethod
    def get_comparison_prompt(query: str, search_results: list, language: str = 'zh') -> str:
        """
        Comparison 查詢的提示詞
        用於比較多個球員
        """
        
        results_text = PromptTemplates._format_search_results(search_results)
        
        if language == 'zh':
            prompt = f"""你是一個專業的MLB數據助手。請根據以下檢索到的數據比較球員表現。

用戶問題：{query}

檢索到的數據：
{results_text}

回答要求：
1. **只使用檢索到的數據**：絕對不要編造任何比較或數字
2. **客觀比較**：基於具體數據進行比較，不要主觀評價
3. **列出關鍵指標**：選擇最相關的3-5個指標進行比較
4. **使用表格或列表**：清楚呈現比較結果
5. **指出差異**：明確說明各球員在哪些方面表現較好

比較格式建議：
[球員A] vs [球員B] ([賽季])

關鍵指標比較：
- [指標1]: [球員A數值] vs [球員B數值]
- [指標2]: [球員A數值] vs [球員B數值]
...

如果檢索結果中缺少某位球員的數據，請說明"缺少 [球員名] 的相關數據"。

請用繁體中文回答。"""

        else:  # English
            prompt = f"""You are a professional MLB data assistant. Compare player performances based on the retrieved data below.

User Question: {query}

Retrieved Data:
{results_text}

Requirements:
1. **Use ONLY the retrieved data**: Never fabricate comparisons or numbers
2. **Objective comparison**: Base on specific data, avoid subjective judgments
3. **List key metrics**: Select 3-5 most relevant metrics for comparison
4. **Use table or list format**: Present comparison clearly
5. **Highlight differences**: Clearly state which player performs better in which aspects

Comparison format suggestion:
[Player A] vs [Player B] ([Season])

Key Metrics Comparison:
- [Metric 1]: [Player A Value] vs [Player B Value]
- [Metric 2]: [Player A Value] vs [Player B Value]
...

If data for any player is missing, state "Missing data for [Player Name]".

Please respond in English."""
        
        return prompt
    
    @staticmethod
    def get_analysis_prompt(query: str, search_results: list, language: str = 'zh') -> str:
        """
        Analysis 查詢的提示詞
        用於分析和解釋
        """
        
        results_text = PromptTemplates._format_search_results(search_results)
        
        if language == 'zh':
            prompt = f"""你是一個專業的MLB數據分析師。請根據以下檢索到的數據進行分析。

用戶問題：{query}

檢索到的數據：
{results_text}

回答要求：
1. **基於數據分析**：所有分析必須基於檢索到的具體數據
2. **多維度分析**：從多個角度（進攻、防守、進階指標等）分析
3. **指出趨勢**：如果有多個賽季的數據，分析變化趨勢
4. **客觀結論**：基於數據得出結論，避免過度主觀
5. **承認局限**：如果數據不足以支持某個結論，要明確說明

分析結構建議：
1. 數據概覽：簡述檢索到的關鍵數據
2. 關鍵發現：指出最重要的2-3個發現
3. 趨勢分析：（如果有多年數據）分析變化趨勢
4. 總結：基於數據的客觀結論

重要：所有數值必須來自檢索結果，不要編造任何統計數據。

請用繁體中文回答。"""

        else:  # English
            prompt = f"""You are a professional MLB data analyst. Analyze based on the retrieved data below.

User Question: {query}

Retrieved Data:
{results_text}

Requirements:
1. **Data-based analysis**: All analysis must be based on specific retrieved data
2. **Multi-dimensional**: Analyze from multiple angles (offense, defense, advanced metrics, etc.)
3. **Identify trends**: If multi-season data available, analyze trends
4. **Objective conclusions**: Draw conclusions based on data, avoid excessive subjectivity
5. **Acknowledge limitations**: If data is insufficient, clearly state so

Analysis structure suggestion:
1. Data Overview: Briefly describe key retrieved data
2. Key Findings: Point out 2-3 most important findings
3. Trend Analysis: (If multi-year data) Analyze trends
4. Summary: Objective conclusions based on data

Important: All numbers must come from the search results. Do not fabricate any statistics.

Please respond in English."""
        
        return prompt
    
    @staticmethod
    def _format_search_results(search_results: list) -> str:
        """
        格式化檢索結果為文字
        
        Args:
            search_results: 檢索結果列表，每個結果包含 player_id, full_text 等
            
        Returns:
            格式化的文字字符串
        """
        
        if not search_results:
            return "（沒有檢索到相關數據）"
        
        formatted_results = []
        for i, result in enumerate(search_results, 1):
            player_id = result.get('player_id', 'Unknown')
            text = result.get('full_text', '')
            
            # 截取前500個字符（避免太長）
            if len(text) > 500:
                text = text[:500] + "..."
            
            formatted_results.append(f"[結果 {i}] {player_id}\n{text}")
        
        return "\n\n".join(formatted_results)
    
    @staticmethod
    def get_prompt(query_type: str, query: str, search_results: list, language: str = 'zh') -> str:
        """
        根據查詢類型獲取對應的提示詞
        
        Args:
            query_type: 查詢類型 (factual/ranking/comparison/analysis)
            query: 用戶查詢
            search_results: 檢索結果
            language: 語言 (zh/en)
            
        Returns:
            完整的提示詞
        """
        
        if query_type == 'factual':
            return PromptTemplates.get_factual_prompt(query, search_results, language)
        elif query_type == 'ranking':
            return PromptTemplates.get_ranking_prompt(query, search_results, language)
        elif query_type == 'comparison':
            return PromptTemplates.get_comparison_prompt(query, search_results, language)
        elif query_type == 'analysis':
            return PromptTemplates.get_analysis_prompt(query, search_results, language)
        else:
            # 默認使用 factual prompt
            return PromptTemplates.get_factual_prompt(query, search_results, language)


def main():
    """測試 Prompt Templates"""
    
    print("=" * 80)
    print("Phase 7: Prompt Templates 測試")
    print("=" * 80)
    
    # 模擬檢索結果
    mock_results = [
        {
            'player_id': 'Aaron Judge_2022',
            'full_text': 'Player: Aaron Judge. Season: 2022. Type: batter. HR: 62, AVG: 0.311, OPS: 1.111'
        },
        {
            'player_id': 'Aaron Judge_2023',
            'full_text': 'Player: Aaron Judge. Season: 2023. Type: batter. HR: 37, AVG: 0.267, OPS: 0.905'
        }
    ]
    
    # 測試不同類型的提示詞
    test_cases = [
        ('factual', 'Aaron Judge 2022年打了幾支全壘打？', 'zh'),
        ('ranking', 'Who are the top 5 home run hitters?', 'en'),
        ('comparison', '比較 Aaron Judge 2022 和 2023 的表現', 'zh'),
        ('analysis', 'Analyze Aaron Judge performance trend', 'en')
    ]
    
    for query_type, query, language in test_cases:
        print(f"\n類型: {query_type}")
        print(f"查詢: {query}")
        print(f"語言: {language}")
        print("-" * 80)
        
        prompt = PromptTemplates.get_prompt(query_type, query, mock_results, language)
        
        # 只顯示前500個字符
        if len(prompt) > 500:
            print(prompt[:500] + "...\n[省略剩餘內容]")
        else:
            print(prompt)
        
        print()
    
    print("=" * 80)
    print("✅ Prompt Templates 測試完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()