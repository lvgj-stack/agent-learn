# 01_agent_loop

用 OpenAI SDK 手写一个最小可用的 **Agent Loop**,理解 Agent 框架背后的核心机制。

## 核心思路

```
User → LLM → [tool_calls?]
              │
              ├── yes → 调用工具 → 把结果塞回 messages → 再问 LLM
              └── no  → 返回最终回答
```

整个循环就是反复地把工具结果追加到 `messages`,直到模型不再请求工具调用(`finish_reason != "tool_calls"`)。

## 提供的工具

| 工具 | 作用 |
| --- | --- |
| `bash` | 执行 shell 命令(无任何限制) |
| `read` | 读取文件 |
| `write` | 写入文件 |
| `glob` | 按 glob 模式列出文件,限制在 `WORKING_DIR` 内 |
| `web_search` | 占位实现,只是把 query 回显 |

## 运行

```bash
# 在仓库根目录
uv run 01_agent_loop/main.py
```

需要在该目录下放 `.env`:

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://...
OPENAI_MODEL=gpt-4o-mini
```

启动后输入需求,例如:

```
User: 列出当前目录下所有 .py 文件并统计行数
```

## 已知限制 / 下一步

- 工具执行**没有权限校验**,模型可以任意 `rm -rf`。下一步见 [../02_agent_permission/](../02_agent_permission/)。
- 只支持单轮输入,不是交互式多轮对话。
- `web_search` 是 stub,未接入真实搜索。
