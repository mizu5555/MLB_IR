# ============================================================
# 事實增強生成 (Fact-Consistency Enhanced Generation)
#
# 提供 3 種回覆模板：
#   1. factual_answer
#   2. comparison_answer
#   3. ranking_answer
#
# 支援中／英語 + 解說員語氣、球探語氣
# ============================================================


# ------------------------------------------------------------
# 通用系統 Prompt（System Prompt）
# ------------------------------------------------------------
SYSTEM_PROMPT = """
You are an MLB analytics expert.  
You must answer strictly based on the supplied FACT BLOCK.  
Never hallucinate numbers not in the FACT BLOCK.  
"""


# ------------------------------------------------------------
# Factual 查詢
# ------------------------------------------------------------
FACTUAL_TEMPLATE = """
You are an MLB analytics expert.

ANSWER LANGUAGE: {language}
STYLE: {style}

USER QUESTION:
{query}

FACT BLOCK (ONLY USE THESE FACTS):
{facts}

TASK:
Provide a precise stat-based answer.
Do NOT invent numbers.
Do NOT guess missing data.

For single-player factual questions, include:
- Player name
- Season
- Team
- The exact metric value
- 1–2 lines of short explanation (if needed)

Begin your answer.
"""


# ------------------------------------------------------------
# Comparison 問題
# ------------------------------------------------------------
COMPARISON_TEMPLATE = """
You are an MLB analytics analyst.

ANSWER LANGUAGE: {language}
STYLE: {style}

USER QUESTION:
{query}

FACT BLOCK (ONLY USE THESE FACTS):
{facts}

TASK:
The user wants comparison results (e.g., who is better than Ohtani in HR).

Rules:
- List all players meeting the condition.
- Sort from highest to lowest (metric).
- Include exact values from FACT BLOCK.
- Provide a short analytical summary at the end.
- Do NOT invent missing players.
- If no players qualify, clearly state so.

Begin your answer.
"""


# ------------------------------------------------------------
# Ranking（Top N）問題
# ------------------------------------------------------------
RANKING_TEMPLATE = """
You are an MLB analyst.

ANSWER LANGUAGE: {language}
STYLE: {style}

USER QUESTION:
{query}

FACT BLOCK (ONLY USE THESE FACTS):
{facts}

TASK:
Provide a ranked list based on the metric.
Rules:
- Output exactly N players (if N players exist).
- Include player, team, season, metric value.
- Use bullet points or table format.
- End with a short summary.
- NO hallucinated numbers.

Begin your answer.
"""


# ------------------------------------------------------------
# Low-level 工具：Fact Block 格式化
# ------------------------------------------------------------
def format_fact_block(records):
    """
    將 hybrid_search + lookup_engine 的結果轉成乾淨 Fact Block，
    保證 LLM 不會幻覺。
    """
    lines = []
    for r in records:
        metric_lines = []
        stats = r.get("stats", {})

        for k, v in stats.items():
            metric_lines.append(f"{k}: {v}")

        block = f"""
[Record]
player: {r['player_name']}
team: {r['team']}
season: {r['season']}
type: {r['type']}
record_key: {r['record_key']}
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
        style=style,
    )


def build_comparison_prompt(query, facts, language="zh", style="analyst"):
    return COMPARISON_TEMPLATE.format(
        query=query,
        facts=facts,
        language=language,
        style=style,
    )


def build_ranking_prompt(query, facts, language="zh", style="analyst"):
    return RANKING_TEMPLATE.format(
        query=query,
        facts=facts,
        language=language,
        style=style,
    )


# ------------------------------------------------------------
# 語氣設定
# ------------------------------------------------------------
STYLE_PRESETS = {
    "analyst": "客觀解說、數據導向、簡潔清楚，如 ESPN 或 MLB Network 分析師。",
    "scout": "球探語氣，著重工具組、動作機制、潛力、表現評估。",
}

LANG_PRESETS = {
    "zh": "中文回答",
    "en": "English Answer",
}
