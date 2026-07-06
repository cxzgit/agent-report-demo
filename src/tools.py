from __future__ import annotations

from typing import Any

from langchain.tools import tool

from .mock_knowledge_base import LOCAL_KNOWLEDGE_BASE
from .prompts import build_section_prompt


def _copy_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "request": dict(state["request"]),
        "parts": list(state.get("parts", [])),
        "keywords": dict(state.get("keywords", {})),
        "search_results": dict(state.get("search_results", {})),
        "references": dict(state.get("references", {})),
        "section_references": dict(state.get("section_references", {})),
        "section_prompts": dict(state.get("section_prompts", {})),
        "sections": dict(state.get("sections", {})),
        "review_results": dict(state.get("review_results", {})),
        "final_report": state.get("final_report", ""),
    }

# 规划章节
@tool
def plan_report_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Plan report sections from country and industry."""
    next_state = _copy_state(state)
    req = next_state["request"]
    next_state["parts"] = [
        f"{req['country']}{req['industry']}市场机会判断",
        "政策准入与合规路径",
        "商业模式与落地建议",
        "主要风险与行动清单",
    ]
    return next_state

# 生成关键词
@tool
def generate_keywords_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Generate local-search keywords for every report section."""
    next_state = _copy_state(state)
    req = next_state["request"]
    next_state["keywords"] = {
        part: [req["country"], req["industry"], part]
        for part in next_state["parts"]
    }
    return next_state

# 搜索
@tool
def mock_search_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Search a local mock knowledge base using generated keywords."""
    next_state = _copy_state(state)
    search_results: dict[str, list[dict[str, Any]]] = {}
    for part, keywords in next_state["keywords"].items():
        matches = []
        for item in LOCAL_KNOWLEDGE_BASE:
            haystack = " ".join([item["title"], item["snippet"], " ".join(item["tags"])]).lower()
            score = sum(1 for keyword in keywords if keyword and keyword.lower() in haystack)
            if score > 0:
                matches.append({**item, "score": score})
        search_results[part] = sorted(matches, key=lambda item: item["score"], reverse=True)[:3]
    next_state["search_results"] = search_results
    return next_state

# 把搜索出来的资料整理成稳定的引用编号
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
                    "snippet": result["snippet"],
                }
            section_references[part].append(ref_id)

    next_state["references"] = references
    next_state["section_references"] = section_references
    return next_state

# 为每个章节构建提示词
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

# 写每个章节的正文
@tool
def write_section_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Write report sections from prompts, references, and local evidence."""
    next_state = _copy_state(state)
    req = next_state["request"]
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
        sections[part] = (
            f"## {index}. {part}\n\n"
            f"本节围绕{req['country']}{req['industry']}展开判断。{evidence_text} "
            f"因此，企业不应只看单点政策利好，而应把需求增长、准入审批、"
            f"合作伙伴执行能力和退出路径放进同一个投资模型中评估。{ref_text}\n\n"
            f"落地上，建议先用轻资产试点验证客户需求和电网接入条件，再根据"
            f"项目收益率、许可周期和本地运营能力决定是否扩大资本投入。\n\n"
        )

    next_state["sections"] = sections
    return next_state

# 检查生成出来的章节内容
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

# 把章节和引用拼接成Markdown格式的报告
@tool
def assemble_report_tool(state: dict[str, Any]) -> dict[str, Any]:
    """Assemble final Markdown report from sections and references."""
    next_state = _copy_state(state)
    req = next_state["request"]
    sections = "\n\n".join(next_state["sections"].get(part, "") for part in next_state["parts"])
    references = "\n".join(
        f"- [{ref_id}] {ref['title']} - {ref['url']}"
        for ref_id, ref in next_state["references"].items()
    )
    next_state["final_report"] = (
        f"# {req['country']}{req['industry']}报告\n\n"
        f"{sections}\n\n"
        f"## 参考资料\n\n{references}\n"
    )
    return next_state
