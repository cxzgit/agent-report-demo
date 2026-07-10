from __future__ import annotations

import re
from typing import Any

from langchain.tools import tool

from .llm_client import call_chat_json
from .prompts import build_clarification_prompt, build_search_prompt, build_section_prompt
from .report_types import describe_request, get_report_type_config


PARAM_LABELS = {
    "location_scope": "落地区域",
    "business_model": "经营模式",
    "budget_level": "投资规模",
    "customer_segment": "目标客群",
    "report_focus": "报告重点",
}


def _copy_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "request": dict(state["request"]),
        "agent_plan": dict(state.get("agent_plan", {})),
        "clarification_questions": list(state.get("clarification_questions", [])),
        "clarified_params": dict(state.get("clarified_params", {})),
        "assumptions": list(state.get("assumptions", [])),
        "parts": list(state.get("parts", [])),
        "keywords": dict(state.get("keywords", {})),
        "search_prompts": dict(state.get("search_prompts", {})),
        "search_results": dict(state.get("search_results", {})),
        "references": dict(state.get("references", {})),
        "section_references": dict(state.get("section_references", {})),
        "section_prompts": dict(state.get("section_prompts", {})),
        "sections": dict(state.get("sections", {})),
        "review_results": dict(state.get("review_results", {})),
        "delivery_summary": dict(state.get("delivery_summary", {})),
        "final_report": state.get("final_report", ""),
    }


def _validate_clarification_payload(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, list):
        raise ValueError("LLM JSON must contain a questions list.")
    if not 3 <= len(raw_questions) <= 5:
        raise ValueError("LLM must return 3 to 5 clarification questions.")

    questions: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for index, item in enumerate(raw_questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question {index} must be an object.")
        key = str(item.get("parameter_key", "")).strip()
        question = str(item.get("question", "")).strip()
        options = item.get("options")
        reason = str(item.get("impact_reason", "")).strip()

        if not re.fullmatch(r"[a-z][a-z0-9_]{1,40}", key):
            raise ValueError(f"Question {index} has invalid parameter_key: {key!r}.")
        if key in seen_keys:
            raise ValueError(f"Duplicate parameter_key from LLM: {key}.")
        if not question:
            raise ValueError(f"Question {index} is missing question text.")
        if not isinstance(options, list) or not 3 <= len(options) <= 4:
            raise ValueError(f"Question {index} must have 3 to 4 options.")
        normalized_options = [str(option).strip() for option in options if str(option).strip()]
        if len(normalized_options) != len(options):
            raise ValueError(f"Question {index} has an empty option.")
        if not reason:
            raise ValueError(f"Question {index} is missing impact_reason.")

        seen_keys.add(key)
        questions.append(
            {
                "parameter_key": key,
                "question": question,
                "options": normalized_options,
                "allow_custom": bool(item.get("allow_custom", True)),
                "impact_reason": reason,
            }
        )

    raw_assumptions = payload.get("assumptions", [])
    assumptions = [str(item).strip() for item in raw_assumptions if str(item).strip()] if isinstance(raw_assumptions, list) else []
    return questions, assumptions


def _demo_search_results(part: str, query: str, context: str, lanes: tuple[str, ...]) -> list[dict[str, Any]]:
    return [
        {
            "title": f"模拟资料检索：{part} {lane}",
            "url": f"demo-search://{index}/{abs(hash(part + lane + query)) % 100000}",
            "snippet": f"围绕查询“{query}”生成的演示证据。该线索用于说明“{lane}”相关事实、判断依据或后续核验方向。上下文：{context}",
        }
        for index, lane in enumerate(lanes, start=1)
    ]


def _format_default_section(template: str, req: dict[str, Any], params: dict[str, Any]) -> str:
    values = {
        "country": req.get("country") or "目标国家/地区",
        "industry": req.get("industry") or "目标行业",
        "topic": req.get("topic") or "当前主题",
        "customer_segment": params.get("customer_segment") or "目标客群",
        "location_scope": params.get("location_scope") or params.get("city") or params.get("region") or "目标市场",
        "business_model": params.get("business_model") or params.get("entry_model") or "进入模式",
        "report_focus": params.get("report_focus") or params.get("focus") or "核心诉求",
    }
    return template.format(**values)


def _fallback_clarification_questions(state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    req = state["request"]
    config = get_report_type_config(req.get("report_type"))
    questions = [
        {
            "parameter_key": "report_focus",
            "question": f"这份{config.label}最需要突出什么？",
            "options": ["结论摘要", "风险判断", "行动建议", "完整分析"],
            "allow_custom": True,
            "impact_reason": "报告重点会直接影响大纲顺序、证据选择和正文详略。",
        },
        {
            "parameter_key": "target_reader",
            "question": "主要读者是谁？",
            "options": ["管理层", "项目团队", "客户/外部伙伴", "投委会/决策会"],
            "allow_custom": True,
            "impact_reason": "读者对象决定表达粒度、风险披露方式和建议颗粒度。",
        },
        {
            "parameter_key": "output_depth",
            "question": "期望输出深度是什么？",
            "options": ["一页摘要", "标准报告", "详细分析", "可执行清单"],
            "allow_custom": True,
            "impact_reason": "输出深度会影响章节数量、正文长度和行动项密度。",
        },
    ]
    return questions, [f"按{config.label}的通用自动化流程推进。"]


@tool
def prepare_agent_context_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Prepare generic report-agent context before clarification and writing."""
    next_state = _copy_state(state)
    req = next_state["request"]
    config = get_report_type_config(req.get("report_type"))

    req["scenario"] = config.scenario
    req["report_type"] = config.report_type
    req["report_label"] = config.label
    req["request_title"] = describe_request(req)
    next_state["request"] = req
    next_state["agent_plan"] = {
        "scenario": config.scenario,
        "report_type": config.report_type,
        "report_label": config.label,
        "role": config.role,
        "request_title": req["request_title"],
        "missing_fields": [field for field in config.required_fields if not str(req.get(field) or "").strip()],
        "automation_steps": [
            "识别报告场景和交付目标",
            "生成高影响澄清问题",
            "规划报告大纲和检索关键词",
            "生成分章节正文并保留引用",
            "执行基础质检并输出交付摘要",
        ],
    }
    return next_state


@tool
def build_delivery_summary_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Build post-generation delivery summary and improvement hints."""
    next_state = _copy_state(state)
    review_results = next_state.get("review_results", {})
    failed = [part for part, result in review_results.items() if not result.get("passed")]
    ref_mentions = sum(int(result.get("reference_mentions", 0)) for result in review_results.values())
    next_state["delivery_summary"] = {
        "ready": not failed,
        "failed_sections": failed,
        "section_count": len(next_state.get("sections", {})),
        "reference_mentions": ref_mentions,
        "next_actions": [
            "补充真实业务材料或联网检索结果替换 demo 证据",
            "对未通过章节追加正文、引用或待核验信息",
            "按目标受众压缩成摘要版或扩展成正式版",
        ],
    }
    return next_state


@tool
def build_clarification_questions_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Build high-impact clarification questions before report generation."""
    next_state = _copy_state(state)
    prompt = build_clarification_prompt(next_state["request"])
    try:
        payload = call_chat_json(prompt)
        questions, assumptions = _validate_clarification_payload(payload)
    except Exception:
        questions, assumptions = _fallback_clarification_questions(next_state)
    next_state["clarification_questions"] = questions
    next_state["assumptions"] = assumptions
    next_state["clarification_prompt"] = prompt
    return next_state


@tool
def resolve_clarification_answers_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Resolve user clarification answers into structured report context."""
    next_state = _copy_state(state)
    req = next_state["request"]
    answers = {key: value for key, value in dict(req.get("clarification_answers", {})).items() if value}
    title = req.get("request_title") or describe_request(req)

    next_state["clarified_params"] = answers
    next_state["assumptions"] = [f"{PARAM_LABELS.get(key, key)}：{value}" for key, value in answers.items()]
    answer_text = "；".join(f"{PARAM_LABELS.get(key, key)}为{value}" for key, value in answers.items())
    req["business_context"] = f"针对{title}，用户补充条件为：{answer_text or '暂无补充答案'}。"
    next_state["request"] = req
    return next_state


@tool
def plan_report_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Plan report sections from report type and clarified context."""
    next_state = _copy_state(state)
    req = next_state["request"]
    config = get_report_type_config(req.get("report_type"))
    confirmed_parts = [part for part in req.get("confirmed_parts", []) if str(part).strip()]
    if confirmed_parts:
        next_state["parts"] = confirmed_parts
        return next_state

    params = next_state.get("clarified_params", {})
    next_state["parts"] = [
        _format_default_section(template, req, params)
        for template in config.default_sections
    ]
    return next_state


@tool
def generate_keywords_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Generate demo-search keywords for every report section."""
    next_state = _copy_state(state)
    req = next_state["request"]
    params = next_state.get("clarified_params", {})
    context_terms = [str(value) for value in params.values() if value]
    base_terms = [
        req.get("scenario", ""),
        req.get("report_label", ""),
        req.get("topic", ""),
        req.get("country", ""),
        req.get("industry", ""),
    ]
    next_state["keywords"] = {
        part: [*base_terms, part, *context_terms]
        for part in next_state["parts"]
    }
    next_state["search_prompts"] = {
        part: build_search_prompt(req, part)
        for part in next_state["parts"]
    }
    return next_state


@tool
def web_search_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Generate self-contained demo search results from generated keywords."""
    next_state = _copy_state(state)
    req = next_state["request"]
    config = get_report_type_config(req.get("report_type"))
    search_results: dict[str, list[dict[str, Any]]] = {}

    for part, keywords in next_state["keywords"].items():
        query = " ".join(str(keyword).strip() for keyword in keywords if str(keyword).strip())
        search_results[part] = _demo_search_results(
            part=part,
            query=query,
            context=req.get("business_context", "暂无补充上下文。"),
            lanes=config.evidence_lanes,
        )

    next_state["search_results"] = search_results
    return next_state


@tool
def build_references_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Convert search results into stable report references."""
    next_state = _copy_state(state)
    references: dict[str, dict[str, Any]] = {}
    section_references: dict[str, list[str]] = {}
    seen_urls: dict[str, str] = {}
    counter = 1

    for part, results in next_state["search_results"].items():
        section_references[part] = []
        for result in results:
            url = result["url"]
            ref_id = seen_urls.get(url)
            if ref_id is None:
                ref_id = f"ref-{counter}"
                counter += 1
                seen_urls[url] = ref_id
                references[ref_id] = {
                    "title": result["title"],
                    "url": url,
                    "snippet": result.get("snippet", ""),
                }
            section_references[part].append(ref_id)

    next_state["references"] = references
    next_state["section_references"] = section_references
    return next_state


@tool
def build_section_prompts_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Build writing prompts for every report section."""
    next_state = _copy_state(state)
    next_state["section_prompts"] = {
        part: build_section_prompt(
            request=next_state["request"],
            part=part,
            reference_ids=next_state["section_references"].get(part, []),
            references=next_state["references"],
        )
        for part in next_state["parts"]
    }
    return next_state


@tool
def write_section_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Write report sections from prompts, references, and demo evidence."""
    next_state = _copy_state(state)
    req = next_state["request"]
    config = get_report_type_config(req.get("report_type"))
    sections: dict[str, str] = {}

    for index, part in enumerate(next_state["parts"], start=1):
        ref_ids = next_state["section_references"].get(part, [])
        ref_text = " ".join(f"[{ref_id}]" for ref_id in ref_ids[:2])
        evidence = [
            next_state["references"][ref_id]["snippet"]
            for ref_id in ref_ids
            if ref_id in next_state["references"]
        ]
        evidence_text = " ".join(evidence[:2])
        requirement_text = "；".join(config.output_requirements)
        sections[part] = (
            f"## {index}. {part}\n\n"
            f"本节基于已澄清的业务上下文展开：{req.get('business_context', '暂无补充上下文')} "
            f"演示检索资料显示：{evidence_text} 写作上应满足：{requirement_text}。"
            f"建议先补充真实材料进行核验，再形成可对外交付版本。{ref_text}\n\n"
        )

    next_state["sections"] = sections
    return next_state


@tool
def review_section_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Review generated sections for basic quality signals."""
    next_state = _copy_state(state)
    review_results: dict[str, dict[str, Any]] = {}

    for part, content in next_state["sections"].items():
        ref_count = content.count("[ref-")
        char_count = len(content.replace(" ", "").replace("\n", ""))
        passed = char_count >= 120 and ref_count >= 1
        review_results[part] = {
            "passed": passed,
            "char_count": char_count,
            "reference_mentions": ref_count,
            "notes": "通过" if passed else "需要补充正文或引用",
        }

    next_state["review_results"] = review_results
    return next_state


@tool
def assemble_report_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Assemble final Markdown report from sections and references."""
    next_state = _copy_state(state)
    req = next_state["request"]
    parts = next_state["parts"]
    sections = "\n\n".join(next_state["sections"].get(part, "") for part in parts)
    outline = "\n".join(f"{index}. {part}" for index, part in enumerate(parts, start=1))
    assumptions = "\n".join(f"- {item}" for item in next_state.get("assumptions", [])) or "- 暂无"
    automation_steps = "\n".join(
        f"- {item}"
        for item in next_state.get("agent_plan", {}).get("automation_steps", [])
    )
    delivery = next_state.get("delivery_summary", {})
    next_actions = "\n".join(f"- {item}" for item in delivery.get("next_actions", [])) or "- 暂无"
    failed_sections = "、".join(delivery.get("failed_sections", [])) or "无"

    citation_blocks: list[str] = []
    for part in parts:
        citation_blocks.append(part)
        for ref_id in next_state["section_references"].get(part, []):
            ref = next_state["references"].get(ref_id)
            if not ref:
                continue
            citation_blocks.append(f"- [{ref_id}] {ref['title']} - {ref['url']}")
        citation_blocks.append("")
    citations = "\n".join(citation_blocks).strip()

    next_state["final_report"] = (
        f"# {req.get('request_title') or describe_request(req)}\n\n"
        f"## Agent 自动化流程\n\n{automation_steps}\n\n"
        f"## 用户补充条件\n\n{req.get('business_context', '暂无补充上下文。')}\n\n"
        f"## 当前假设\n\n{assumptions}\n\n"
        f"## 用户确认大纲\n\n{outline}\n\n"
        f"{sections}\n\n"
        f"## 交付质检摘要\n\n"
        f"- 章节数：{delivery.get('section_count', len(parts))}\n"
        f"- 引用标记数：{delivery.get('reference_mentions', 0)}\n"
        f"- 未通过章节：{failed_sections}\n\n"
        f"## 后续自动化建议\n\n{next_actions}\n\n"
        f"## 参考资料\n\n{citations}\n"
    )
    return next_state
