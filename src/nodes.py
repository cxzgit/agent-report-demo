from __future__ import annotations

from typing import Any

from .models import ReportGraphState
from .tools import (
    assemble_report_tool,
    build_clarification_questions_tool,
    build_delivery_summary_tool,
    build_references_tool,
    build_section_prompts_tool,
    generate_keywords_tool,
    plan_report_tool,
    prepare_agent_context_tool,
    resolve_clarification_answers_tool,
    review_section_tool,
    web_search_tool,
    write_section_tool,
)


def _summarize(tool_name: str, payload: dict[str, Any]) -> str:
    if tool_name == "prepare_agent_context_tool":
        return f"prepared {payload['request'].get('report_label', 'report')} agent context"
    if tool_name == "build_clarification_questions_tool":
        return f"built {len(payload['clarification_questions'])} clarification questions"
    if tool_name == "resolve_clarification_answers_tool":
        return f"resolved {len(payload['clarified_params'])} clarified parameters"
    if tool_name == "plan_report_tool":
        return f"planned {len(payload['parts'])} report sections"
    if tool_name == "generate_keywords_tool":
        return f"generated {sum(len(items) for items in payload['keywords'].values())} keywords"
    if tool_name == "web_search_tool":
        return f"fetched {sum(len(items) for items in payload['search_results'].values())} web search results"
    if tool_name == "build_references_tool":
        return f"built {len(payload['references'])} deduplicated references"
    if tool_name == "build_section_prompts_tool":
        return f"built {len(payload['section_prompts'])} section prompts"
    if tool_name == "write_section_tool":
        return f"wrote {len(payload['sections'])} sections"
    if tool_name == "review_section_tool":
        passed = sum(1 for result in payload["review_results"].values() if result["passed"])
        return f"review passed {passed}/{len(payload['review_results'])} sections"
    if tool_name == "build_delivery_summary_tool":
        return f"built delivery summary for {payload['delivery_summary']['section_count']} sections"
    if tool_name == "assemble_report_tool":
        return f"assembled final report, length {len(payload['final_report'])} chars"
    return "completed"


def _run_tool(tool_obj: Any, state: ReportGraphState) -> ReportGraphState:
    tool_input = dict(state)
    tool_input.pop("traces", None)
    payload = tool_obj.invoke({"state": tool_input})
    traces = list(state.get("traces", []))
    trace = {"tool_name": tool_obj.name, "summary": _summarize(tool_obj.name, payload)}
    traces.append(trace)
    payload["traces"] = traces
    print(f"[node] {tool_obj.name}: {trace['summary']}")
    return payload


def prepare_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(prepare_agent_context_tool, state)


def clarify_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(build_clarification_questions_tool, state)


def resolve_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(resolve_clarification_answers_tool, state)


def plan_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(plan_report_tool, state)


def keywords_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(generate_keywords_tool, state)


def search_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(web_search_tool, state)


def references_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(build_references_tool, state)


def prompts_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(build_section_prompts_tool, state)


def write_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(write_section_tool, state)


def review_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(review_section_tool, state)


def delivery_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(build_delivery_summary_tool, state)


def assemble_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(assemble_report_tool, state)


