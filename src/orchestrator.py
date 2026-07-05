from __future__ import annotations

from typing import Any

from .models import ReportRequest, ReportState, ToolTrace
from .tools import REPORT_TOOLS


class ReportAgentOrchestrator:

    def __init__(self) -> None:
        self.tools = REPORT_TOOLS

    def run(self, request: ReportRequest) -> ReportState:
        traces: list[ToolTrace] = []
        state = ReportState(request=request)
        payload = state.to_tool_input()

        for tool_obj in self.tools:
            payload = tool_obj.invoke({"state": payload})
            trace = ToolTrace(tool_name=tool_obj.name, summary=self._summarize(tool_obj.name, payload))
            traces.append(trace)
            self._print_trace(trace)

        return ReportState.from_tool_output(payload, traces)

    @staticmethod
    def _summarize(tool_name: str, payload: dict[str, Any]) -> str:
        if tool_name == "plan_report_tool":
            return f"规划 {len(payload['parts'])} 个章节"
        if tool_name == "generate_keywords_tool":
            return f"生成 {sum(len(items) for items in payload['keywords'].values())} 个关键词"
        if tool_name == "mock_search_tool":
            return f"匹配 {sum(len(items) for items in payload['search_results'].values())} 条本地资料"
        if tool_name == "build_references_tool":
            return f"整理 {len(payload['references'])} 条去重引用"
        if tool_name == "write_section_tool":
            return f"生成 {len(payload['sections'])} 个章节正文"
        if tool_name == "review_section_tool":
            passed = sum(1 for result in payload["review_results"].values() if result["passed"])
            return f"质检通过 {passed}/{len(payload['review_results'])} 个章节"
        if tool_name == "assemble_report_tool":
            return f"组装最终报告，长度 {len(payload['final_report'])} 字符"
        return "完成"

    @staticmethod
    def _print_trace(trace: ToolTrace) -> None:
        print(f"[tool] {trace.tool_name}: {trace.summary}")