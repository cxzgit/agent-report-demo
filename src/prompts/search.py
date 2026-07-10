from __future__ import annotations

from typing import Any

from ..report_types import get_report_type_config


def build_search_prompt(request: dict[str, Any], part: str) -> str:
    config = get_report_type_config(request.get("report_type"))
    title = request.get("request_title") or config.label
    context = request.get("business_context", "暂无补充上下文。")
    base_lines = []
    if request.get("country"):
        base_lines.append(f"国家/地区：{request['country']}")
    if request.get("industry"):
        base_lines.append(f"行业：{request['industry']}")
    if request.get("topic"):
        base_lines.append(f"主题/对象：{request['topic']}")
    base_text = "\n".join(base_lines) or "暂无基础输入"
    evidence_lanes = "、".join(config.evidence_lanes)

    language_rule = (
        "如果目标国家或资料源以英文为主，优先输出英文关键词；如果资料源以中文为主，输出中文关键词。"
        if config.scenario == "overseas"
        else "优先输出中文关键词；如主题包含英文产品名、公司名或专有名词，可以保留英文。"
    )

    return f"""# Role
你是专业的信息检索规划员。

# Context
我们要撰写「{title}」中的「{part}」章节。
报告类型：{config.label}
{base_text}
已澄清上下文：{context}

# Task
提取最多 3 个核心搜索关键词，用于获取高质量资料、原始信息、案例、数据或可引用依据。

# Optimization Rules
1. 组合策略：优先使用「报告主题 + 章节核心问题 + 资料方向」的组合。
2. 资料方向：{evidence_lanes}。
3. 语言策略：{language_rule}
4. 专业度：关键词应具体，避免只输出宽泛词，如“市场”“报告”“分析”。

# Output Format
仅输出 3 个关键词，用空格分隔，不要解释，不要 Markdown。
""".strip()
