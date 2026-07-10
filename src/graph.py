from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .models import ReportGraphState, ReportRequest, ReportState
from .nodes import (
    assemble_node,
    clarify_node,
    delivery_node,
    keywords_node,
    plan_node,
    prepare_node,
    prompts_node,
    references_node,
    resolve_node,
    review_node,
    search_node,
    write_node,
)


def build_clarification_graph():
    graph = StateGraph(ReportGraphState)
    graph.add_node("prepare", prepare_node)
    graph.add_node("clarify", clarify_node)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "clarify")
    graph.add_edge("clarify", END)
    return graph.compile()


def build_outline_graph():
    graph = StateGraph(ReportGraphState)
    graph.add_node("prepare", prepare_node)
    graph.add_node("resolve", resolve_node)
    graph.add_node("plan", plan_node)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "resolve")
    graph.add_edge("resolve", "plan")
    graph.add_edge("plan", END)
    return graph.compile()


def build_report_graph():
    graph = StateGraph(ReportGraphState)

    graph.add_node("prepare", prepare_node)
    graph.add_node("resolve", resolve_node)
    graph.add_node("plan", plan_node)
    graph.add_node("keywords", keywords_node)
    graph.add_node("search", search_node)
    graph.add_node("references", references_node)
    graph.add_node("prompts", prompts_node)
    graph.add_node("write", write_node)
    graph.add_node("review", review_node)
    graph.add_node("delivery", delivery_node)
    graph.add_node("assemble", assemble_node)

    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "resolve")
    graph.add_edge("resolve", "plan")
    graph.add_edge("plan", "keywords")
    graph.add_edge("keywords", "search")
    graph.add_edge("search", "references")
    graph.add_edge("references", "prompts")
    graph.add_edge("prompts", "write")
    graph.add_edge("write", "review")
    graph.add_edge("review", "delivery")
    graph.add_edge("delivery", "assemble")
    graph.add_edge("assemble", END)

    return graph.compile()


def run_clarification_graph(request: ReportRequest) -> ReportState:
    initial_state = ReportState(request=request).to_graph_state()
    final_state = build_clarification_graph().invoke(initial_state)
    return ReportState.from_graph_output(final_state)


def run_outline_graph(request: ReportRequest) -> ReportState:
    initial_state = ReportState(request=request).to_graph_state()
    final_state = build_outline_graph().invoke(initial_state)
    return ReportState.from_graph_output(final_state)


def run_report_graph(request: ReportRequest) -> ReportState:
    initial_state = ReportState(request=request).to_graph_state()
    final_state = build_report_graph().invoke(initial_state)
    return ReportState.from_graph_output(final_state)
