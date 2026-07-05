# Agent Report Demo

一个基于 LangChain tools 的报告生成场景 demo。当前版本不调用真实搜索、数据库或模型 API，所有资料来自本地 mock 知识库，便于稳定演示“工具拆分 + 可插拔编排”。

## 项目结构

```text
agent-report-demo/
├── pyproject.toml
├── README.md
└── src/
    ├── __init__.py
    ├── __main__.py          # CLI 入口
    ├── models.py            # ReportRequest / ReportState
    ├── orchestrator.py      # Agent 编排
    ├── sample_data.py       # 本地 mock 知识库
    └── tools.py             # LangChain tools
```

## 运行

和现有 `overseas-bases` Python 服务保持一致，从项目根目录执行：

```powershell
python -m src start
```

`start` 是默认命令，也可以简写为：

```powershell
python -m src
```

## 工具拆分

- `plan_report_tool`: 规划报告章节
- `generate_keywords_tool`: 为章节生成检索关键词
- `mock_search_tool`: 检索本地 mock 知识库
- `build_references_tool`: 整理 `ref-*` 引用
- `write_section_tool`: 生成章节正文
- `review_section_tool`: 检查正文长度和引用覆盖
- `assemble_report_tool`: 组装最终 Markdown 报告

后续接入 LangGraph 时，可以把这些 tool 对应的函数直接迁移为 graph node，`ReportState` 作为图状态。