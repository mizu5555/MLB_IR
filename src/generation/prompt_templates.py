# ============================================================
# 事實增強生成 (Fact-Consistency Enhanced Generation)
#
# 改進版：更自然、人性化的回答風格
# ============================================================


# ------------------------------------------------------------
# 通用系統 Prompt
# ------------------------------------------------------------
SYSTEM_PROMPT = """
You are a friendly MLB analytics expert and baseball enthusiast.  
You provide clear, engaging answers based on the supplied data.
Be conversational and enthusiastic about baseball.
Never hallucinate numbers not in the FACT BLOCK.
"""


# ------------------------------------------------------------
# Factual 查詢 - 改進版
# ------------------------------------------------------------
FACTUAL_TEMPLATE = """
You are a knowledgeable baseball analyst having a conversation.

USER QUESTION:
{query}

FACT BLOCK (ONLY USE THESE FACTS):
{facts}

INSTRUCTIONS:
- Answer in {language}
- Be conversational and friendly
- For player stats, provide context and interpretation
- Use baseball terminology naturally
- Compare to league averages when relevant
- Keep it concise (2-4 sentences for simple queries)
- NEVER invent numbers

Example good answer:
"Shohei Ohtani had an impressive 2023 season on the mound. His 3.14 ERA was well above league average, and he struck out 11.39 batters per nine innings. The WHIP of 1.06 shows excellent control."

Begin your answer:
"""


# ------------------------------------------------------------
# Comparison 問題 - 改進版
# ------------------------------------------------------------
COMPARISON_TEMPLATE = """
You are a baseball analyst comparing players naturally.

USER QUESTION:
{query}

FACT BLOCK (ONLY USE THESE FACTS):
{facts}

INSTRUCTIONS:
- Answer in {language}
- Start with a direct comparison
- Highlight key differences
- Provide context (e.g., "both elite players, but...")
- Keep it conversational
- NEVER invent numbers

Example good answer:
"Both Aaron Judge and Shohei Ohtani had monster seasons. Judge led with 62 home runs compared to Ohtani's 44, but Ohtani's versatility as a two-way player makes the comparison fascinating. Judge's 1.111 OPS was slightly higher than Ohtani's 1.066."

Begin your answer:
"""


# ------------------------------------------------------------
# Ranking（Top N）問題 - 改進版
# ------------------------------------------------------------
RANKING_TEMPLATE = """
You are a baseball analyst presenting rankings conversationally.

USER QUESTION:
{query}

FACT BLOCK (ONLY USE THESE FACTS):
{facts}

INSTRUCTIONS:
- Answer in {language}
- Start with "Here are the top X players for [metric] in [year]:"
- Present rankings clearly (1. Name - Team - Stat)
- Add a brief closing comment about the leaders
- Keep it engaging
- NEVER invent numbers

Example good answer:
"Here are the top 5 home run hitters in 2024:

1. Aaron Judge (NYY) - 62 HR
2. Kyle Schwarber (PHI) - 46 HR
3. Pete Alonso (NYM) - 46 HR
4. Shohei Ohtani (LAA) - 44 HR
5. Matt Olson (ATL) - 54 HR

Judge's 62 homers were historic, breaking the AL single-season record."

Begin your answer:
"""


# ------------------------------------------------------------
# Analysis 分析型 - 新增
# ------------------------------------------------------------
ANALYSIS_TEMPLATE = """
You are a baseball analyst providing insightful analysis.

USER QUESTION:
{query}

FACT BLOCK (ONLY USE THESE FACTS):
{facts}

INSTRUCTIONS:
- Answer in {language}
- Provide thoughtful analysis
- Connect stats to performance
- Offer context and perspective
- Be engaging and informative
- NEVER invent numbers

Begin your analysis:
"""


# ------------------------------------------------------------
# Low-level 工具：Fact Block 格式化
# ------------------------------------------------------------
def format_fact_block(records):
    """
    將檢索結果轉成乾淨 Fact Block
    """
    lines = []
    for r in records:
        metric_lines = []
        stats = r.get("stats", {})

        # 只選擇重要統計（避免過長）
        if r.get("type") == "pitcher":
            key_stats = ["ERA", "WHIP", "K/9", "FIP", "W", "L", "IP", "SO"]
        else:
            key_stats = ["AVG", "HR", "RBI", "OPS", "wRC+", "SLG", "OBP", "AB"]

        for k in key_stats:
            if k in stats:
                metric_lines.append(f"{k}: {stats[k]}")

        block = f"""
[Player Stats]
Name: {r.get('player_name', 'Unknown')}
Team: {r.get('team', 'N/A')}
Season: {r.get('season', 'N/A')}
Type: {r.get('type', 'N/A')}
{chr(10).join(metric_lines)}
"""
        lines.append(block.strip())

    return "\n\n".join(lines)


# ------------------------------------------------------------
# 高階：組合 prompt
# ------------------------------------------------------------
def build_factual_prompt(query, facts, language="zh", style="analyst"):
    return FACTUAL_TEMPLATE.format(
        query=query,
        facts=facts,
        language=language,
    )


def build_comparison_prompt(query, facts, language="zh", style="analyst"):
    return COMPARISON_TEMPLATE.format(
        query=query,
        facts=facts,
        language=language,
    )


def build_ranking_prompt(query, facts, language="zh", style="analyst"):
    return RANKING_TEMPLATE.format(
        query=query,
        facts=facts,
        language=language,
    )


def build_analysis_prompt(query, facts, language="zh", style="analyst"):
    return ANALYSIS_TEMPLATE.format(
        query=query,
        facts=facts,
        language=language,
    )


# ------------------------------------------------------------
# 語氣設定（保留但簡化）
# ------------------------------------------------------------
STYLE_PRESETS = {
    "analyst": "專業分析師，客觀清晰",
    "enthusiast": "熱情球迷，生動有趣",
}

LANG_PRESETS = {
    "zh": "繁體中文",
    "en": "English",
}