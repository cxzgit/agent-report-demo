from __future__ import annotations

from typing import Any

from .models import ReportGraphState
from .tools import (
    assemble_report_tool,
    build_references_tool,
    build_section_prompts_tool,
    generate_keywords_tool,
    mock_search_tool,
    plan_report_tool,
    review_section_tool,
    write_section_tool,
)


def _summarize(tool_name: str, payload: dict[str, Any]) -> str:
    if tool_name == "plan_report_tool":
        return f"规划 {len(payload['parts'])} 个章节"
    if tool_name == "generate_keywords_tool":
        return f"生成 {sum(len(items) for items in payload['keywords'].values())} 个关键词"
    if tool_name == "mock_search_tool":
        return f"匹配 {sum(len(items) for items in payload['search_results'].values())} 条本地资料"
    if tool_name == "build_references_tool":
        return f"整理 {len(payload['references'])} 条去重引用"
    if tool_name == "build_section_prompts_tool":
        return f"构造 {len(payload['section_prompts'])} 个章节提示词"
    if tool_name == "write_section_tool":
        return f"生成 {len(payload['sections'])} 个章节正文"
    if tool_name == "review_section_tool":
        passed = sum(1 for result in payload["review_results"].values() if result["passed"])
        return f"质检通过 {passed}/{len(payload['review_results'])} 个章节"
    if tool_name == "assemble_report_tool":
        return f"组装最终报告，长度 {len(payload['final_report'])} 字符"
    return "完成"


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


def plan_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(plan_report_tool, state)


def keywords_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(generate_keywords_tool, state)


def search_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(mock_search_tool, state)


def references_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(build_references_tool, state)


def prompts_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(build_section_prompts_tool, state)


def write_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(write_section_tool, state)


def review_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(review_section_tool, state)


def assemble_node(state: ReportGraphState) -> ReportGraphState:
    return _run_tool(assemble_report_tool, state)