from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


class ReportGraphState(TypedDict):
    request: dict[str, Any]
    agent_plan: dict[str, Any]
    clarification_questions: list[dict[str, Any]]
    clarified_params: dict[str, Any]
    assumptions: list[str]
    parts: list[str]
    keywords: dict[str, list[str]]
    search_prompts: dict[str, str]
    search_results: dict[str, list[dict[str, Any]]]
    references: dict[str, dict[str, Any]]
    section_references: dict[str, list[str]]
    section_prompts: dict[str, str]
    sections: dict[str, str]
    review_results: dict[str, dict[str, Any]]
    delivery_summary: dict[str, Any]
    final_report: str
    traces: list[dict[str, str]]


@dataclass
class ReportRequest:
    country: str = ""
    industry: str = ""
    scenario: str = "overseas"
    report_type: str = "overseas_market"
    topic: str = ""
    clarification_answers: dict[str, str] = field(default_factory=dict)
    confirmed_parts: list[str] = field(default_factory=list)


@dataclass
class ToolTrace:
    tool_name: str
    summary: str


@dataclass
class ReportState:
    request: ReportRequest
    agent_plan: dict[str, Any] = field(default_factory=dict)
    clarification_questions: list[dict[str, Any]] = field(default_factory=list)
    clarified_params: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    parts: list[str] = field(default_factory=list)
    keywords: dict[str, list[str]] = field(default_factory=dict)
    search_prompts: dict[str, str] = field(default_factory=dict)
    search_results: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    references: dict[str, dict[str, Any]] = field(default_factory=dict)
    section_references: dict[str, list[str]] = field(default_factory=dict)
    section_prompts: dict[str, str] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)
    review_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    delivery_summary: dict[str, Any] = field(default_factory=dict)
    final_report: str = ""
    traces: list[ToolTrace] = field(default_factory=list)

    def to_graph_state(self) -> ReportGraphState:
        return {
            "request": {
                "country": self.request.country,
                "industry": self.request.industry,
                "scenario": self.request.scenario,
                "report_type": self.request.report_type,
                "topic": self.request.topic,
                "clarification_answers": dict(self.request.clarification_answers),
                "confirmed_parts": list(self.request.confirmed_parts),
            },
            "agent_plan": self.agent_plan,
            "clarification_questions": self.clarification_questions,
            "clarified_params": self.clarified_params,
            "assumptions": self.assumptions,
            "parts": self.parts,
            "keywords": self.keywords,
            "search_prompts": self.search_prompts,
            "search_results": self.search_results,
            "references": self.references,
            "section_references": self.section_references,
            "section_prompts": self.section_prompts,
            "sections": self.sections,
            "review_results": self.review_results,
            "delivery_summary": self.delivery_summary,
            "final_report": self.final_report,
            "traces": [trace.__dict__ for trace in self.traces],
        }

    @classmethod
    def from_graph_output(cls, payload: ReportGraphState) -> "ReportState":
        request_data = payload["request"]
        return cls(
            request=ReportRequest(
                country=request_data.get("country", ""),
                industry=request_data.get("industry", ""),
                scenario=request_data.get("scenario", "overseas"),
                report_type=request_data.get("report_type", "overseas_market"),
                topic=request_data.get("topic", ""),
                clarification_answers=dict(request_data.get("clarification_answers", {})),
                confirmed_parts=list(request_data.get("confirmed_parts", [])),
            ),
            agent_plan=dict(payload.get("agent_plan", {})),
            clarification_questions=list(payload.get("clarification_questions", [])),
            clarified_params=dict(payload.get("clarified_params", {})),
            assumptions=list(payload.get("assumptions", [])),
            parts=list(payload.get("parts", [])),
            keywords=dict(payload.get("keywords", {})),
            search_prompts=dict(payload.get("search_prompts", {})),
            search_results=dict(payload.get("search_results", {})),
            references=dict(payload.get("references", {})),
            section_references=dict(payload.get("section_references", {})),
            section_prompts=dict(payload.get("section_prompts", {})),
            sections=dict(payload.get("sections", {})),
            review_results=dict(payload.get("review_results", {})),
            delivery_summary=dict(payload.get("delivery_summary", {})),
            final_report=payload.get("final_report", ""),
            traces=[ToolTrace(**trace) for trace in payload.get("traces", [])],
        )
