from __future__ import annotations

import argparse
import sys
from typing import Any

from .graph import run_clarification_graph, run_outline_graph, run_report_graph
from .llm_client import LLMConfigError, LLMResponseError
from .models import ReportRequest
from .report_types import ReportTypeConfig, get_report_type_config

__title__ = "agent-report-demo"
__version__ = "0.2.0"

REPORT_TYPE_MENU = [
    "overseas_market",
    "meeting_minutes",
    "monthly_report",
    "due_diligence",
    "topic_research",
]


def main() -> None:
    parser = argparse.ArgumentParser(prog=__title__)
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("command", nargs="?", default="start", choices=["start"], help="Command to run")
    args = parser.parse_args()

    if args.command == "start":
        config = _choose_report_type()
        country = ""
        industry = ""
        topic = ""
        if config.scenario == "overseas":
            country = _read_required_text("请输入目标国家或地区：")
            industry = _read_required_text("请输入目标行业：")
        else:
            topic = _read_required_text("请输入报告主题/对象/输入材料概述：")
        try:
            start_demo(
                country=country,
                industry=industry,
                report_type=config.report_type,
                topic=topic,
            )
        except (LLMConfigError, LLMResponseError) as exc:
            print_config_error("LLM 调用失败", str(exc), [
                "OPENAI_API_KEY=你的 DeepSeek API Key",
                "OPENAI_MODEL=deepseek-chat",
                "OPENAI_BASE_URL=https://api.deepseek.com",
            ])
            sys.exit(1)
        except ValueError as exc:
            print_config_error("流程执行失败", str(exc), [])
            sys.exit(1)


def print_config_error(title: str, message: str, examples: list[str]) -> None:
    print()
    print(f"=== {title} ===")
    print(message)
    if examples:
        print()
        print("请先在 .env 中配置，例如：")
        for example in examples:
            print(example)


def _read_required_text(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("不能为空，请重新输入。")


def _choose_report_type() -> ReportTypeConfig:
    print("=== 请选择报告类型 ===")
    for index, report_type in enumerate(REPORT_TYPE_MENU, start=1):
        config = get_report_type_config(report_type)
        print(f"{index}. {config.label}")
    print()

    while True:
        raw = input(f"请输入 1-{len(REPORT_TYPE_MENU)} 选择报告类型：").strip()
        if raw.isdigit():
            selected = int(raw)
            if 1 <= selected <= len(REPORT_TYPE_MENU):
                return get_report_type_config(REPORT_TYPE_MENU[selected - 1])
        print(f"请输入 1 到 {len(REPORT_TYPE_MENU)} 之间的数字。")


def _read_answer(question: dict[str, Any]) -> str:
    options = list(question.get("options", []))
    parameter_key = question["parameter_key"]

    while True:
        raw = input(f"请回答 {parameter_key}（输入 1-{len(options)} 选择选项，或直接输入自定义内容）：").strip()
        if not raw:
            print("请输入选项编号，或直接输入自定义答案。")
            continue
        if raw.isdigit():
            selected = int(raw)
            if 1 <= selected <= len(options):
                return options[selected - 1]
            print(f"请输入 1 到 {len(options)} 之间的数字，或直接输入自定义答案。")
            continue
        return raw


def collect_answers(questions: list[dict[str, Any]]) -> dict[str, str]:
    answers: dict[str, str] = {}
    print("=== 需求澄清问题 ===")
    print("请输入选项编号；如果选项不合适，也可以直接输入自定义答案。")
    print()

    for index, question in enumerate(questions, start=1):
        print(f"{index}. [{question['parameter_key']}] {question['question']}")
        for option_index, option in enumerate(question["options"], start=1):
            print(f"   {option_index}. {option}")
        print(f"   为什么问：{question['impact_reason']}")
        answers[question["parameter_key"]] = _read_answer(question)
        print()

    return answers


def confirm_outline(parts: list[str]) -> list[str]:
    print("=== AI 规划大纲 ===")
    for index, part in enumerate(parts, start=1):
        print(f"{index}. {part}")
    print()
    print("=== 请确认大纲 ===")
    print("直接按回车：确认并继续生成报告")
    print("输入 n：手动重写大纲")
    choice = input("你的选择：").strip().lower()
    if choice not in {"n", "no", "否"}:
        return parts

    print("请逐行输入新的章节标题，输入空行结束：")
    custom_parts: list[str] = []
    while True:
        line = input(f"章节 {len(custom_parts) + 1}：").strip()
        if not line:
            break
        custom_parts.append(line)
    if not custom_parts:
        print("未输入新大纲，继续使用 AI 规划大纲。")
        return parts
    return custom_parts


def start_demo(country: str, industry: str, report_type: str = "overseas_market", topic: str = "") -> None:
    config = get_report_type_config(report_type)
    initial_request = ReportRequest(
        country=country,
        industry=industry,
        scenario=config.scenario,
        report_type=config.report_type,
        topic=topic,
    )

    print("=== Agent Report Demo ===")
    print(f"报告类型：{config.label}")
    if initial_request.country:
        print(f"国家/地区：{initial_request.country}")
    if initial_request.industry:
        print(f"行业：{initial_request.industry}")
    if initial_request.topic:
        print(f"主题/对象：{initial_request.topic}")
    print()

    clarification_state = run_clarification_graph(initial_request)
    answers = collect_answers(clarification_state.clarification_questions)

    print("=== 用户补充答案 ===")
    for key, value in answers.items():
        print(f"{key}: {value}")
    print()

    outline_request = ReportRequest(
        country=initial_request.country,
        industry=initial_request.industry,
        scenario=initial_request.scenario,
        report_type=initial_request.report_type,
        topic=initial_request.topic,
        clarification_answers=answers,
    )
    outline_state = run_outline_graph(outline_request)
    confirmed_parts = confirm_outline(outline_state.parts)

    report_request = ReportRequest(
        country=initial_request.country,
        industry=initial_request.industry,
        scenario=initial_request.scenario,
        report_type=initial_request.report_type,
        topic=initial_request.topic,
        clarification_answers=answers,
        confirmed_parts=confirmed_parts,
    )
    final_state = run_report_graph(report_request)

    print("=== Final Report ===")
    print(final_state.final_report)

    print("=== Traces ===")
    for trace in final_state.traces:
        print(f"- {trace.tool_name}: {trace.summary}")


if __name__ == "__main__":
    main()

