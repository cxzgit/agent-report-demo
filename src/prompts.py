from __future__ import annotations

from typing import Any


def build_section_prompt(
    request: dict[str, str],
    part: str,
    reference_ids: list[str],
    references: dict[str, dict[str, Any]],
) -> str:
    reference_text = "\n".join(
        f"[{ref_id}] {references[ref_id]['title']}: {references[ref_id]['snippet']}"
        for ref_id in reference_ids
        if ref_id in references
    )
    return f"""你是一名出海行业研究分析师。
请基于国家、行业、章节和参考资料，撰写一段报告正文。

国家：{request['country']}
行业：{request['industry']}
章节：{part}

参考资料：
{reference_text}

写作要求：
1. 使用中文输出。
2. 使用 Markdown 二级标题。
3. 必须在正文中保留引用标记，例如 [ref-1]。
4. 内容需要包含判断、依据和落地建议。
""".strip()