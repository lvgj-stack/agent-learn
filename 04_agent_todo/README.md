# 04_agent_todo

这个示例展示了如何让 Agent 维护一份 **任务清单（todo）**，用于跟踪当前工作进度。

## 目标

当 Agent 在处理较复杂任务时，往往需要把大目标拆成若干子任务。例如：

- 先读取项目结构
- 再定位问题文件
- 再修改代码
- 最后验证结果

`todo_write` 工具就是用来把这些步骤显式记录下来。

## 这个示例的价值

相比只会“聊天”的 Agent，带 todo 的 Agent 更像一个真正的执行者，因为它可以：

- 记录当前计划
- 标记任务状态
- 让用户看到执行进度
- 在长任务中保持上下文清晰

## 运行方式

```bash
uv run 04_agent_todo/main.py
```

## 你会看到什么

当模型调用 `todo_write` 时，程序会打印类似这样的内容：

```text
## Current Tasks
-   读取项目文件
- > 修改 README
- ✓ 验证结果
```

其中：

- 空格表示 `pending`
- `>` 表示 `in_progress`
- `✓` 表示 `completed`

## 关键实现

- `CURRENT_TODOS`：当前任务缓存
- `run_todo_write(...)`：更新并打印任务列表
- `TOOL_HANDLERS`：将 `todo_write` 接入 Agent 工具系统

## 适合重点观察的地方

- Agent 如何把一个任务拆成多个步骤
- todo 状态如何变化
- todo 工具如何帮助人类理解 Agent 的执行路径

## 延伸方向

- 支持自动根据上下文生成 todo
- 支持任务优先级
- 支持任务依赖关系
- 将 todo 持久化到文件或数据库

如果你的 Agent 项目比较复杂，建议尽早加入类似 todo 的任务管理能力。