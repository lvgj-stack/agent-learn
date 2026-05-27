# 01_langchain_agent

用 LangChain 1.x 的 `create_agent` 快速搭建一个 Agent,对比 [../01_agent_loop/](../01_agent_loop/) 自行实现循环的方案,体会框架替我们做了哪些事。

## 关键 API

- `langchain.agents.create_agent`:一行代码组装好「模型 + 工具 + 系统提示 + 中间件」。
- `@tool` 装饰器:把普通函数注册成可被 LLM 调用的工具。
- `TodoListMiddleware`:内置的中间件,让模型自动维护任务清单,适合多步骤任务。
- `agent.stream(..., stream_mode="values")`:按状态流式输出,每个 chunk 是当前完整 state。

## 提供的工具

| 工具 | 作用 |
| --- | --- |
| `get_weather` | 假数据,返回 "It's always sunny in {city}!" |
| `run_bash_command` | 执行 shell 命令 |
| `fetch_text_from_url` | 用 `urllib` 抓取 URL 文本内容 |

## 运行

```bash
uv run 01_langchain_agent/main.py
```

需要的 `.env`:

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://...
OPENAI_MODEL=gpt-4o-mini
```

当前 `main.py` 写死了用户输入(`"分析这个项目"`),会流式打印 Agent 的工具调用与回复。要换问题直接改 `main.py` 末尾的 `messages`。

## 与 01_agent_loop 的对比

| 维度 | 手写 loop | LangChain |
| --- | --- | --- |
| 控制粒度 | 完全可控,易于学习 | 框架约定,改造成本高 |
| 代码量 | ~200 行 | ~70 行 |
| 流式 / 中间件 / 多模型路由 | 需自己实现 | 开箱即用 |
| 适用场景 | 学习原理、定制 loop | 快速搭原型、需要生态集成 |
