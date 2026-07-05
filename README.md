# Agent Report Demo

一个基于 LangGraph + LangChain tools 的报告生成场景 demo。当前版本不调用真实搜索、数据库或模型 API，所有资料来自本地 mock 知识库，便于稳定演示“图编排 + 工具拆分 + 可插拔节点”。

## 项目结构

```text
agent-report-demo/
├── pyproject.toml
├── README.md
└── src/
    ├── __init__.py
    ├── __main__.py          # CLI 入口，保持 python -m src start 风格
    ├── models.py            # ReportRequest / ReportState / ReportGraphState
    ├── graph.py             # LangGraph StateGraph 编排与运行入口`r`n    ├── nodes.py             # graph node，负责调用 LangChain tools
    ├── tools.py             # LangChain tools 定义
    ├── prompts.py           # 章节写作提示词构造
    └── mock_knowledge_base.py  # 本地 mock 知识库
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

## 流程

```text
START
  -> plan
  -> keywords
  -> search
  -> references
  -> prompts
  -> write
  -> review
  -> assemble
  -> END
```

## 工具拆分

- `plan_report_tool`: 规划报告章节
- `generate_keywords_tool`: 为章节生成检索关键词
- `mock_search_tool`: 检索本地 mock 知识库
- `build_references_tool`: 整理 `ref-*` 引用
- `build_section_prompts_tool`: 构造章节写作提示词
- `write_section_tool`: 生成章节正文
- `review_section_tool`: 检查正文长度和引用覆盖
- `assemble_report_tool`: 组装最终 Markdown 报告

后续替换真实能力时，可以按节点替换：`search` 接真实搜索服务，`write` 接真实 LLM，`review` 接质量评估模型。

