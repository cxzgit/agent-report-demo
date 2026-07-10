from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportTypeConfig:
    scenario: str
    report_type: str
    label: str
    role: str
    required_fields: tuple[str, ...]
    clarification_focus: tuple[str, ...]
    default_sections: tuple[str, ...]
    evidence_lanes: tuple[str, ...]
    output_requirements: tuple[str, ...]
    writing_lens: tuple[str, ...]


REPORT_TYPES: dict[str, ReportTypeConfig] = {
    "overseas_market": ReportTypeConfig(
        scenario="overseas",
        report_type="overseas_market",
        label="出海市场调研报告",
        role="出海行业研究分析师",
        required_fields=("country", "industry"),
        clarification_focus=("落地区域", "经营模式", "投资规模", "目标客群", "报告重点"),
        default_sections=(
            "{country}{industry}面向{customer_segment}的市场机会判断",
            "{location_scope}的准入条件与合规路径",
            "{business_model}的运营模型与资源配置",
            "围绕{report_focus}的风险假设与行动清单",
        ),
        evidence_lanes=("政策与准入", "市场与企业案例", "风险与落地建议"),
        output_requirements=("包含市场判断、依据和落地建议", "保留引用标记，例如 [ref-1]"),
        writing_lens=(
            "采用商业咨询视角，关注机会规模、准入门槛、合规成本和落地路径",
            "遇到政策、成本、风险类信息时，要尽量转化为企业可执行的判断",
            "避免泛泛描述国家大势，必须映射到具体行业和出海动作",
        ),
    ),
    "meeting_minutes": ReportTypeConfig(
        scenario="office",
        report_type="meeting_minutes",
        label="会议纪要",
        role="企业会议纪要整理 Agent",
        required_fields=("topic",),
        clarification_focus=("会议目标", "参会角色", "决议口径", "待办责任人", "交付格式"),
        default_sections=(
            "会议背景与目标",
            "关键讨论要点",
            "已形成决议",
            "行动项、负责人和截止时间",
        ),
        evidence_lanes=("会议输入材料", "决议与待办", "风险与跟进事项"),
        output_requirements=("突出结论、决议、行动项", "行动项需包含负责人和时间要求，未知则标注待确认"),
        writing_lens=(
            "采用企业会议秘书视角，优先提炼结论、分歧、决议和行动项",
            "不要写成行业研究报告，也不要扩展无关背景",
            "对责任人、截止时间、待确认事项要明确标注",
        ),
    ),
    "monthly_report": ReportTypeConfig(
        scenario="office",
        report_type="monthly_report",
        label="月报",
        role="经营月报分析 Agent",
        required_fields=("topic",),
        clarification_focus=("汇报周期", "业务范围", "核心指标", "受众对象", "下月重点"),
        default_sections=(
            "本月核心结论",
            "关键指标与进展复盘",
            "问题、风险与原因分析",
            "下月计划与资源需求",
        ),
        evidence_lanes=("指标与进展", "问题与风险", "计划与资源"),
        output_requirements=("体现环比变化、关键进展和问题归因", "给出下月重点和需要协同的事项"),
        writing_lens=(
            "采用经营复盘视角，突出本月结果、变化原因和下月动作",
            "对指标、项目进展、风险问题要形成管理层可读的判断",
            "避免流水账，重点说明结果背后的原因和资源诉求",
        ),
    ),
    "due_diligence": ReportTypeConfig(
        scenario="office",
        report_type="due_diligence",
        label="尽调报告",
        role="商业尽调分析 Agent",
        required_fields=("topic",),
        clarification_focus=("尽调对象", "交易目的", "关注维度", "风险偏好", "资料完整度"),
        default_sections=(
            "尽调对象与交易背景",
            "业务、财务和组织关键事实",
            "核心风险与待核验事项",
            "初步结论与后续尽调清单",
        ),
        evidence_lanes=("主体与业务事实", "财务与组织线索", "风险与待核验事项"),
        output_requirements=("区分事实、判断和待核验假设", "输出后续资料清单和访谈问题"),
        writing_lens=(
            "采用商业尽调视角，严格区分事实、判断、假设和待核验事项",
            "风险描述要落到可能影响交易、估值、整合或合规的具体后果",
            "不得把资料不足的内容写成确定结论",
        ),
    ),
    "topic_research": ReportTypeConfig(
        scenario="office",
        report_type="topic_research",
        label="主题研究报告",
        role="主题研究分析 Agent",
        required_fields=("topic",),
        clarification_focus=("研究问题", "时间范围", "分析维度", "目标读者", "输出深度"),
        default_sections=(
            "研究问题与结论摘要",
            "背景、现状与关键变量",
            "主要观点、证据与反方约束",
            "建议、风险和后续研究方向",
        ),
        evidence_lanes=("背景与现状", "观点与案例", "风险与后续研究"),
        output_requirements=("先给结论，再展开依据", "明确证据边界和后续可验证方向"),
        writing_lens=(
            "采用研究分析视角，先给核心判断，再展开背景、证据和约束条件",
            "观点必须对应证据或可解释的推理链条",
            "需要说明反方约束、适用边界和后续研究方向",
        ),
    ),
}


def get_report_type_config(report_type: str | None) -> ReportTypeConfig:
    key = report_type or "overseas_market"
    if key not in REPORT_TYPES:
        allowed = ", ".join(sorted(REPORT_TYPES))
        raise ValueError(f"未知报告类型：{key}。可选值：{allowed}")
    return REPORT_TYPES[key]


def describe_request(request: dict[str, object]) -> str:
    config = get_report_type_config(str(request.get("report_type") or "overseas_market"))
    country = str(request.get("country") or "").strip()
    industry = str(request.get("industry") or "").strip()
    topic = str(request.get("topic") or "").strip()

    if config.scenario == "overseas":
        return f"{country}{industry}{config.label}"
    if topic:
        return f"{topic}{config.label}"
    return config.label
