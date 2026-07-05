from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


class ReportGraphState(TypedDict):
    request: dict[str, str]
    parts: list[str]
    keywords: dict[str, list[str]]
    search_results: dict[str, list[dict[str, Any]]]
    references: dict[str, dict[str, Any]]
    section_references: dict[str, list[str]]
    section_prompts: dict[str, str]
    sections: dict[str, str]
    review_results: dict[str, dict[str, Any]]
    final_report: str
    traces: list[dict[str, str]]


@dataclass
class ReportRequest:
    country: str
    industry: str


@dataclass
class ToolTrace:
    tool_name: str
    summary: str


@dataclass
class ReportState:
    request: ReportRequest
    parts: list[str] = field(default_factory=list)
    keywords: dict[str, list[str]] = field(default_factory=dict)
    search_results: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    references: dict[str, dict[str, Any]] = field(default_factory=dict)
    section_references: dict[str, list[str]] = field(default_factory=dict)
    section_prompts: dict[str, str] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)
    review_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    final_report: str = ""
    traces: list[ToolTrace] = field(default_factory=list)

    def to_graph_state(self) -> ReportGraphState:
        return {
            "request": {
                "country": self.request.country,
                "industry": self.request.industry,
            },
            "parts": self.parts,
            "keywords": self.keywords,
            "search_results": self.search_results,
            "references": self.references,
            "section_references": self.section_references,
            "section_prompts": self.section_prompts,
            "sections": self.sections,
            "review_results": self.review_results,
            "final_report": self.final_report,
            "traces": [trace.__dict__ for trace in self.traces],
        }

    @classmethod
    def from_graph_output(cls, payload: ReportGraphState) -> "ReportState":
        request_data = payload["request"]
        return cls(
            request=ReportRequest(
                country=request_data["country"],
                industry=request_data["industry"],
            ),
            parts=list(payload.get("parts", [])),
            keywords=dict(payload.get("keywords", {})),
            search_results=dict(payload.get("search_results", {})),
            references=dict(payload.get("references", {})),
            section_references=dict(payload.get("section_references", {})),
            section_prompts=dict(payload.get("section_prompts", {})),
            sections=dict(payload.get("sections", {})),
            review_results=dict(payload.get("review_results", {})),
            final_report=payload.get("final_report", ""),
            traces=[ToolTrace(**trace) for trace in payload.get("traces", [])],
        )