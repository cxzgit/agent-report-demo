from __future__ import annotations

from typing import Any

from ..report_types import get_report_type_config


def build_clarification_prompt(request: dict[str, Any]) -> str:
    config = get_report_type_config(request.get("report_type"))
    request_lines = []
    if request.get("country"):
        request_lines.append(f"- 国家/地区：{request['country']}")
    if request.get("industry"):
        request_lines.append(f"- 行业：{request['industry']}")
    if request.get("topic"):
        request_lines.append(f"- 主题/对象：{request['topic']}")
    request_text = "\n".join(request_lines) or "- 用户尚未提供完整主题"
    focus_text = "、".join(config.clarification_focus)
    provided_fields = "、".join(config.required_fields)

    return f"""你是一个擅长{config.label}需求澄清的咨询型 Agent。

用户当前只提供了：
{request_text}

报告场景：{config.scenario}
报告类型：{config.label}
建议优先澄清维度：{focus_text}

你的任务不是生成报告，而是生成一组用于终端交互的澄清问题，目标是用最少问题最快收缩用户诉求边界。

请在内部执行以下步骤：
1. 拆解关键参数：找出会显著影响报告结构、搜索关键词、落地建议的参数。
2. 过滤参数：能从国家、行业或其他参数推导的不要问；低影响参数不要问。
3. 敏感度排序：优先选择对最终报告差异影响最大的参数。
4. 生成问题：最多 5 个问题；每个问题 3-4 个互斥选项；必须允许用户自定义输入。
5. 输出中文：问题、选项、影响原因都用简体中文。

只输出一个 JSON 对象，不要 Markdown，不要解释。JSON 必须符合以下结构：
{{
  "questions": [
    {{
      "parameter_key": "英文 snake_case 参数名，例如 location_scope",
      "question": "中文问题",
      "options": ["中文选项1", "中文选项2", "中文选项3"],
      "allow_custom": true,
      "impact_reason": "为什么这个问题会显著影响报告"
    }}
  ],
  "assumptions": ["当前可暂定的中文假设"]
}}

硬性规则：
- questions 数量必须在 3 到 5 之间。
- 每个 options 数量必须在 3 到 4 之间。
- parameter_key 必须稳定、简短、英文 snake_case。
- 不要重复询问用户已经提供的字段：{provided_fields}。
""".strip()
