# Agent Report Demo

一个独立的 LangGraph + LangChain tools 通用报告 Agent demo。

当前 demo 以“通用报告自动化生成”为主线：在现有出海报告基础上，前置增加通用 Agent 需求识别与任务规划，后置增加基础质检与交付摘要。检索节点使用内置 Demo 检索结果，不依赖外部 search 服务、数据库或知识库。

## 支持场景

- 出海场景：`overseas_market`，沿用国家/地区 + 行业输入，生成出海市场调研报告。
- 通用办公场景：
  - `meeting_minutes`：会议纪要
  - `monthly_report`：月报
  - `due_diligence`：尽调报告
  - `topic_research`：主题研究报告

## 项目结构

```text
agent-report-demo/
├── pyproject.toml
├── README.md
├── .env                 # 本地环境变量，填写 DeepSeek API Key
└── src/
    ├── __main__.py      # CLI 入口
    ├── models.py        # ReportRequest / ReportState / ReportGraphState
    ├── graph.py         # LangGraph 编排入口
    ├── nodes.py         # graph node
    ├── tools.py         # LangChain tools，包含前置/后置 Agent 自动化节点
    ├── report_types.py  # 报告类型与场景配置
    ├── llm_client.py    # OpenAI-compatible LLM client
    ├── env_loader.py    # .env loader
    └── prompts/
        ├── clarification.py
        └── sections.py
```

## 配置

在 `.env` 中填写：

```env
OPENAI_API_KEY=你的 DeepSeek API Key
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com
```

## 运行

```powershell
python -m src start
```

启动后先选择报告类型：

```text
=== 请选择报告类型 ===
1. 出海市场调研报告
2. 会议纪要
3. 月报
4. 尽调报告
5. 主题研究报告
```

选择报告类型后，程序会继续按场景询问必要输入。出海报告会询问目标国家/地区和目标行业；通用办公报告会询问报告主题、对象或输入材料概述。

## 流程

```text
Agent 前置识别报告类型与自动化任务
  -> LLM 生成澄清问题
  -> 用户终端回答
  -> AI 规划大纲
  -> 用户终端确认/重写大纲
  -> Demo 检索
  -> 整理 ref 引用
  -> 章节写作
  -> 基础质检与交付摘要
  -> 汇总成 Markdown 报告
```

## 说明

- `prepare` 阶段根据报告类型生成通用 Agent 自动化计划。
- `clarify` 阶段调用 DeepSeek 生成动态澄清问题；调用失败时会回退到内置通用澄清问题，方便离线演示。
- `search` 阶段不访问外部搜索服务，只生成结构化 Demo 检索结果，方便演示 Agent 工作流。
- `delivery` 阶段输出章节数、引用数、未通过章节和后续自动化建议。
- 最终 Markdown 会打印 Agent 自动化流程、大纲、章节正文、质检摘要和 Demo 检索引用。
