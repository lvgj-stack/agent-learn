# 01_agent_loop

这是一个最基础的 **Agent 循环** 示例，用来演示：

- 如何让模型调用工具
- 如何把工具结果回传给模型
- 如何持续迭代，直到模型完成任务

这个目录是后续所有示例的基础版本。

## 核心流程

整个 Agent 的工作方式可以概括为：

1. 接收用户输入
2. 将输入和系统提示词发送给模型
3. 如果模型请求工具，就执行工具
4. 将工具执行结果再发回模型
5. 循环直到模型不再请求工具

```text
User -> Model -> Tool -> Model -> Tool -> ... -> Final Answer
```

## 提供的工具

当前示例里注册了这些工具：

- `bash`：执行命令行操作
- `read`：读取文件
- `write`：写入文件
- `web_search`：模拟联网搜索
- `glob`：匹配文件
- `todo_write`：写入任务列表
- `task`：启动子代理

## 运行方式

```bash
uv run 01_agent_loop/main.py
```

运行前请先配置 `.env`：

```env
OPENAI_API_KEY=你的key
OPENAI_MODEL=你的模型名
OPENAI_BASE_URL=可选，自定义接口地址
```

## 代码说明

`main.py` 中最重要的部分是：

- `agent_loop(...)`：主循环
- `TOOL_HANDLERS`：工具名到实现函数的映射
- `spawn_subagent(...)`：子代理入口
- `run_bash_command(...)` / `read_file(...)` / `write_file(...)` 等工具实现

## 安全提示

这个示例用于学习 Agent 机制，不适合直接在不受控环境中运行。尤其是 `bash` 工具，建议只在可信工作目录内测试。

## 可扩展方向

- 增加权限控制
- 增加 hook 机制
- 增加子代理协作
- 增加技能系统
- 增加上下文压缩

如果你想先理解 Agent 的基本工作方式，建议从这个目录开始阅读。