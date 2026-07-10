from __future__ import annotations

from typing import Any

from ..report_types import get_report_type_config


def build_section_prompt(
    request: dict[str, Any],
    part: str,
    reference_ids: list[str],
    references: dict[str, dict[str, Any]],
) -> str:
    config = get_report_type_config(request.get("report_type"))
    reference_text = "\n".join(
        f"[{ref_id}] {references[ref_id]['title']}: {references[ref_id]['snippet']}"
        for ref_id in reference_ids
        if ref_id in references
    )
    context = request.get("business_context", "暂无补充上下文。")
    title = request.get("request_title") or config.label
    request_lines = []
    if request.get("country"):
        request_lines.append(f"国家/地区：{request['country']}")
    if request.get("industry"):
        request_lines.append(f"行业：{request['industry']}")
    if request.get("topic"):
        request_lines.append(f"主题/对象：{request['topic']}")
    request_text = "\n".join(request_lines) or "暂无基础输入"
    requirements = "\n".join(f"- {item}" for item in config.output_requirements)
    writing_lens = "\n".join(f"- {item}" for item in config.writing_lens)
    evidence_lanes = "、".join(config.evidence_lanes)
    reference_text = reference_text or "暂无参考资料。"

    return f"""# Role Definition
你是一名{config.role}。

# Context
我们正在撰写一份「{title}」。
报告场景：{config.scenario}
报告类型：{config.label}
{request_text}
已澄清上下文：{context}

# Current Task
请撰写当前章节：「{part}」。
第一行必须是 Markdown 二级标题，格式为：## {part}

参考资料：
{reference_text}

# Depth Requirement
这是报告正文，不是简单摘要。请确保当前章节有明确判断、依据和面向用户的下一步含义。
如果参考资料较少，可以补充通用行业知识、管理框架或办公文档写作规范，但必须明确这是基于上下文的分析，不要伪造具体数据。

# Report-Type Lens
{writing_lens}

# Evidence Direction
本章节优先围绕这些资料方向展开：{evidence_lanes}。

# Output Requirements
{requirements}

# Formatting Rules
- 只能使用简体中文输出。
- 第一行必须是 Markdown 二级标题：## {part}
- 正文中必须保留引用标记，例如 [ref-1]。
- 若出现对比信息、清单、行动项、风险项或多维度指标，优先使用 Markdown 表格或清晰列表呈现。
- 不要输出空泛套话，不要只写 2-3 句话。
""".strip()
