from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .models import ReportGraphState, ReportRequest, ReportState
from .nodes import (
    assemble_node,
    keywords_node,
    plan_node,
    prompts_node,
    references_node,
    review_node,
    search_node,
    write_node,
)


def build_report_graph():
    graph = StateGraph(ReportGraphState)

    graph.add_node("plan", plan_node)              # 规划报告章节
    graph.add_node("keywords", keywords_node)      # 为每个章节生成检索关键词
    graph.add_node("search", search_node)          # 使用 mock 知识库检索资料
    graph.add_node("references", references_node)  # 将检索结果整理成 ref-* 引用
    graph.add_node("prompts", prompts_node)        # 为每个章节构造写作提示词
    graph.add_node("write", write_node)            # 根据资料和提示词生成章节正文
    graph.add_node("review", review_node)          # 对章节正文做基础质量检查
    graph.add_node("assemble", assemble_node)      # 组装最终 Markdown 报告

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "keywords")
    graph.add_edge("keywords", "search")
    graph.add_edge("search", "references")
    graph.add_edge("references", "prompts")
    graph.add_edge("prompts", "write")
    graph.add_edge("write", "review")
    graph.add_edge("review", "assemble")
    graph.add_edge("assemble", END)

    return graph.compile()


def run_report_graph(request: ReportRequest) -> ReportState:
    initial_state = ReportState(request=request).to_graph_state()
    final_state = build_report_graph().invoke(initial_state)
    return ReportState.from_graph_output(final_state)