# m-agents

学习与实践 AI Agent 的示例集合,按主题分目录,每个子目录是一个独立可运行的最小示例。

## 子项目

| 目录 | 说明 | 依赖 |
| --- | --- | --- |
| [01_agent_loop/](01_agent_loop/) | 用 OpenAI SDK 手写一个最小 Agent Loop,支持 `bash` / `read` / `write` / `glob` / `web_search` 等工具调用 | `openai`、`dotenv`、`truststore` |
| [01_langchain_agent/](01_langchain_agent/) | 用 LangChain `create_agent` 搭建 Agent,演示自定义工具与 `TodoListMiddleware` 流式输出 | `langchain`、`langchain-openai` |
| [02_agent_permission/](02_agent_permission/) | 在 Agent Loop 之上加入权限系统:deny list、规则匹配、运行时询问用户授权 | 同 `01_agent_loop` |

## 环境

- Python `>=3.12`
- 包管理:[uv](https://github.com/astral-sh/uv)

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量(在各子项目目录下创建 .env)
# OPENAI_API_KEY=...
# OPENAI_BASE_URL=...
# OPENAI_MODEL=...

# 3. 运行任意子项目
uv run 01_agent_loop/main.py
uv run 01_langchain_agent/main.py
uv run 02_agent_permission/main.py
```

## 目录约定

- 每个子项目独立维护 `main.py` 与自己的 `README.md`
- `.env` 不入库,参考根目录 [.gitignore](.gitignore)
