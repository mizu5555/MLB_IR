import ollama
from typing import Dict, List, Optional
from src.web.stat_selection_config import detect_problem_type, get_analysis_stats

class AnalysisLLMEngine:
    """
    Analysis 查詢專用的 LLM 引擎
    
    專注於：
    1. 因果推理（為什麼 X 下降/上升）
    2. 跨指標關聯分析
    3. 個性化建議
    """
    
    def __init__(self, model="llama3.2"):
        self.model = model
        self.available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        try:
            ollama.list()
            return True
        except:
            return False
    
    def analyze(
        self,
        query: str,
        player_data: Dict,
        problem_type: str,
        league_avg: Optional[Dict] = None
    ) -> str:
        """
        深度分析主函數
        
        Args:
            query: 用戶原始問題
            player_data: 檢索到的球員數據（含 stats）
            problem_type: 問題類型（如 "壓制力不足"）
            league_avg: 聯盟平均數據（可選）
        
        Returns:
            分析報告（Markdown 格式）
        """
        # 1. 取得分析配置
        config = get_analysis_stats(problem_type)
        
        # 2. 準備結構化數據
        player_name = player_data.get("player_name")
        season = player_data.get("season")
        player_type = player_data.get("type")
        stats = player_data.get("stats", {})
        
        # 3. 建立 Fact Block
        fact_block = self._build_fact_block(
            player_name, season, player_type, stats, config, league_avg
        )
        
        # 4. 建立 Prompt
        prompt = self._build_analysis_prompt(
            query, fact_block, problem_type, config
        )
        
        # 5. 呼叫 LLM
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt(player_type)
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.3,  # 降低創造性，提高事實準確性
                "num_predict": 800   # Analysis 需要較長回答
            }
        )
        
        return response['message']['content']
    
    def _build_fact_block(
        self, 
        player_name: str,
        season: int,
        player_type: str,
        stats: Dict,
        config: Dict,
        league_avg: Optional[Dict]
    ) -> str:
        """
        建立結構化的 Fact Block
        
        格式：
        === PLAYER DATA ===
        Name: Shohei Ohtani
        Season: 2023
        Type: pitcher
        
        === KEY METRICS ===
        K% (三振率): 31.5% [League Avg: 23.1%] ✅ +8.4%
        K/9: 11.39 [League Avg: 9.2] ✅ +2.19
        ...
        
        === SUPPORTING METRICS ===
        HardHit%: 38.2%
        ...
        """
        lines = []
        
        # Player Info
        lines.append("=== PLAYER DATA ===")
        lines.append(f"Name: {player_name}")
        lines.append(f"Season: {season}")
        lines.append(f"Type: {player_type}")
        lines.append("")
        
        # Key Metrics（主要診斷指標）
        lines.append("=== KEY METRICS ===")
        for metric in config["main_stats"]:
            value = stats.get(metric)
            if value is None:
                continue
            
            line = f"{metric}: {value}"
            
            # 加入聯盟平均比較
            if league_avg and metric in league_avg:
                avg = league_avg[metric]
                diff = float(value) - float(avg)
                
                # 判斷好壞（考慮是否越低越好）
                from src.web.stat_selection_config import is_lower_better
                if is_lower_better(metric):
                    status = "✅" if diff < 0 else "⚠️"
                else:
                    status = "✅" if diff > 0 else "⚠️"
                
                line += f" [League Avg: {avg}] {status} {diff:+.2f}"
            
            lines.append(line)
        
        lines.append("")
        
        # Supporting Metrics（支援指標）
        lines.append("=== SUPPORTING METRICS ===")
        for metric in config["supporting_stats"]:
            value = stats.get(metric)
            if value is not None:
                lines.append(f"{metric}: {value}")
        
        return "\n".join(lines)
    
    def _build_analysis_prompt(
        self,
        query: str,
        fact_block: str,
        problem_type: str,
        config: Dict
    ) -> str:
        """
        建立 Analysis 專用的 Prompt
        """
        analysis_focus = config["analysis_focus"]
        
        prompt = f"""
You are an expert MLB analyst. A user asked:

USER QUESTION:
{query}

PROBLEM TYPE IDENTIFIED:
{problem_type}

VERIFIED PLAYER DATA:
{fact_block}

ANALYSIS FRAMEWORK:
Your analysis should focus on:
{chr(10).join([f"- {focus}" for focus in analysis_focus])}

CRITICAL INSTRUCTIONS:
1. **ONLY use numbers from the VERIFIED PLAYER DATA section**
2. Do NOT invent or estimate ANY numbers
3. Explain the "why" behind the data patterns
4. Connect multiple metrics to tell a coherent story
5. Provide specific, actionable insights
6. If a metric is marked with ✅, explain why it's good
7. If a metric is marked with ⚠️, explain what might be causing the issue

RESPONSE FORMAT:
### 🔍 診斷分析

[1-2 sentences: What does the data reveal?]

### 📊 關鍵發現

1. **[Metric 1]**: [Analysis]
2. **[Metric 2]**: [Analysis]
3. **[Cross-metric insight]**: [How metrics relate to each other]

### 💡 可能原因

[2-3 bullet points: Based on the data, what might be causing this?]

### 🎯 建議

[2-3 specific, actionable suggestions]

Now provide your analysis in Traditional Chinese (繁體中文):
"""
        return prompt
    
    def _get_system_prompt(self, player_type: str) -> str:
        """系統提示詞"""
        return f"""You are a professional MLB analytics expert specializing in {player_type} performance analysis.

Your expertise includes:
- Interpreting advanced metrics (K%, BB%, FIP, wRC+, etc.)
- Understanding cause-and-effect relationships in player performance
- Providing data-driven insights and recommendations

Core principles:
1. NEVER fabricate numbers
2. Base ALL conclusions on provided data
3. Explain technical concepts clearly
4. Be honest about data limitations
5. Provide actionable insights

Response style:
- Professional but conversational
- Use analogies when helpful
- Structure analysis logically
- Highlight key insights clearly
"""


# ============================================================
# 輔助函數：取得聯盟平均數據
# ============================================================
def get_league_averages(season: int, player_type: str) -> Dict:
    """
    取得聯盟平均數據（可以預先計算或即時計算）
    
    簡化版：先返回固定值，未來可以從資料庫計算
    """
    if player_type == "pitcher":
        return {
            "ERA": 3.50,     # ERA ≤ 3.50 → 好
            "WHIP": 1.20,    # WHIP ≤ 1.20 → 好
            "K%": 0.25,      # K% ≥ 25% → 好
            "BB%": 0.06,     # BB% ≤ 6% → 好
            "K/9": 9.5,      # K/9 ≥ 9.5 → 好
            "BB/9": 2.2,     # BB/9 ≤ 2.2 → 好
            "FIP": 3.70,     # FIP ≤ 3.70 → 好
        }
    else:  # batter
        return {
            "AVG": 0.270,    # AVG ≥ .270 → 好
            "OBP": 0.340,    # OBP ≥ .340 → 好
            "SLG": 0.450,    # SLG ≥ .450 → 好
            "OPS": 0.800,    # OPS ≥ .800 → 好
            "wRC+": 115,     # wRC+ ≥ 115 → 好
            "K%": 0.18,      # K% ≤ 18% → 好（越低越好）
            "BB%": 0.10,     # BB% ≥ 10% → 好
        }
