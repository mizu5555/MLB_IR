"""
src/generation/prompt_templates.py
提示詞模板：防止幻覺，確保事實一致性，並支援多義性檢查與對話歷史
"""

class PromptTemplates:
    """
    提示詞模板管理器
    """
    
    @staticmethod
    def _get_core_rules(language: str = 'zh') -> str:
        """
        核心規則 - 優化版
        加入「全名匹配例外」邏輯，防止無限迴圈
        """
        if language == 'zh':
            return """
【重要核心規則】(CRITICAL RULES):
1. **多義性檢查 (Ambiguity Check)**：
   - 檢查檢索結果是否包含多位【不同】的球員（例如 "Luis Garcia" 和 "Luis Garcia Jr."）。
   - **例外狀況**：如果用戶的查詢（或對話歷史）已經明確指出了球員的【完整姓名】（例如用戶說 "Luis Garcia Jr."），這時**不需要**反問，請直接鎖定該球員的數據回答。
   - 只有在用戶只說了模糊的姓氏（如 "Garcia"）且無法確定是誰時，才列出選項並反問。

2. **事實準確性**：
   - 絕對不要編造數字。如果檢索結果沒有該數據，就說找不到。
   - 不要混淆不同年份的數據。
"""
        else:
            return """
[CRITICAL RULES]:
1. **AMBIGUITY CHECK**: 
   - Check if results contain multiple DIFFERENT players.
   - **EXCEPTION**: If the user's query (or history) strictly matches a specific player's FULL NAME (e.g., "Luis Garcia Jr."), **DO NOT** ask for clarification. Proceed with that player's data.
   - Only ask for clarification if the query is ambiguous (e.g., just "Garcia").

2. **FACTUAL ACCURACY**: 
   - Never fabricate numbers.
"""

    @staticmethod
    def _format_history(history: list) -> str:
        """格式化對話歷史"""
        if not history:
            return "（無歷史對話）"
        
        history_text = []
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            content = msg.get('content', '')
            history_text.append(f"{role}: {content}")
        
        return "\n".join(history_text)

    @staticmethod
    def _format_search_results(search_results: list) -> str:
        """格式化檢索結果"""
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
    def get_prompt(query_type: str, query: str, search_results: list, language: str = 'zh', history: list = None) -> str:
        """
        通用 Prompt 生成入口，支援歷史對話
        """
        results_text = PromptTemplates._format_search_results(search_results)
        core_rules = PromptTemplates._get_core_rules(language)
        history_text = PromptTemplates._format_history(history or [])
        
        # 根據類型選擇特定指令
        task_instruction = ""
        if query_type == 'ranking':
            task_instruction = "Task: Rank players based on actual values." if language != 'zh' else "任務：根據實際數值對球員進行排名。"
        elif query_type == 'comparison':
            task_instruction = "Task: Compare players objectively." if language != 'zh' else "任務：客觀比較球員數據。"
        elif query_type == 'analysis':
            task_instruction = "Task: Analyze trends and data." if language != 'zh' else "任務：分析數據趨勢與含義。"
        else: # factual
            task_instruction = "Task: Extract specific facts/stats." if language != 'zh' else "任務：提取具體的事實或統計數據。"

        if language == 'zh':
            prompt = f"""你是一個專業的MLB數據助手。
{core_rules}

=== 對話歷史 (Context) ===
{history_text}

=== 檢索到的數據 (Data) ===
{results_text}

=== 用戶最新問題 (Current Query) ===
{query}

回答要求：
1. 結合「對話歷史」來理解用戶意圖（例如若用戶只輸入名字，可能是為了回應上一輪的問題）。
2. {task_instruction}
3. 優先執行核心規則。

請用繁體中文回答。"""
        
        else:  # English
            prompt = f"""You are a professional MLB data assistant.
{core_rules}

=== CONVERSATION HISTORY ===
{history_text}

=== RETRIEVED DATA ===
{results_text}

=== CURRENT QUERY ===
{query}

Requirements:
1. Use History to understand context (e.g., if user enters a name, it might be answering the previous question).
2. {task_instruction}
3. Follow Core Rules.

Please respond in English."""
        
        return prompt

    # 保留舊接口以兼容測試代碼（可選）
    @staticmethod
    def get_factual_prompt(query, search_results, language='zh'):
        return PromptTemplates.get_prompt('factual', query, search_results, language)

    @staticmethod
    def get_ranking_prompt(query, search_results, language='zh'):
        return PromptTemplates.get_prompt('ranking', query, search_results, language)

    @staticmethod
    def get_comparison_prompt(query, search_results, language='zh'):
        return PromptTemplates.get_prompt('comparison', query, search_results, language)
    
    @staticmethod
    def get_analysis_prompt(query, search_results, language='zh'):
        return PromptTemplates.get_prompt('analysis', query, search_results, language)


def main():
    """測試 Prompt Templates"""
    print("Prompt Templates 測試運行中...")
    # 簡單測試
    mock_results = [{'player_id': 'Test_Player', 'full_text': 'Data...'}]
    mock_history = [{'role': 'user', 'content': 'Garcia?'}, {'role': 'assistant', 'content': 'Which one?'}]
    print(PromptTemplates.get_prompt('factual', 'Luis Garcia Jr.', mock_results, history=mock_history))

if __name__ == "__main__":
    main()