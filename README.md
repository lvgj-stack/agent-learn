# agent-learn

一个用于学习和实践 **Agentic AI** 的示例仓库。

本项目按主题拆分成多个小示例，每个目录都聚焦一个 Agent 能力点，方便你逐个理解、运行和改造。

## 项目目标

- 理解 Agent 的基本执行循环
- 学习权限控制与安全边界
- 了解 Hook 的拦截与扩展方式
- 使用 Todo 管理复杂任务
- 理解 Subagent 的任务分工模式
- 掌握 Skills 的能力复用机制
- 认识上下文压缩在长期运行中的作用

## 目录总览

| 目录 | 主题 | 说明 |
| --- | --- | --- |
| `01_agent_loop` | Agent Loop | 演示 Agent 的基本思考-行动-观察循环 |
| `02_agent_permission` | Permission | 演示权限控制、确认与安全边界 |
| `03_agent_hook` | Hook | 演示事件钩子与流程拦截扩展 |
| `04_agent_todo` | Todo | 演示任务拆分、跟踪与状态管理 |
| `05_subagent` | Subagent | 演示将任务交给子代理并汇总结果 |
| `06_skills` | Skills | 演示如何加载和使用可复用技能 |
| `07_context_compact` | Context Compaction | 演示长上下文下的压缩与摘要 |

## 如何使用

每个示例目录通常都可以独立运行，进入对应目录后执行：

```bash
uv run <example>/main.py
```

例如：

```bash
uv run 05_subagent/main.py
```

如果你想快速理解某个能力点，建议按以下顺序阅读：

1. `01_agent_loop`
2. `02_agent_permission`
3. `03_agent_hook`
4. `04_agent_todo`
5. `05_subagent`
6. `06_skills`
7. `07_context_compact`

## 每个示例你能学到什么

### 01_agent_loop

理解 Agent 最核心的运行机制：

- 接收任务
- 规划下一步
- 调用工具
- 观察结果
- 继续迭代

### 02_agent_permission

理解 Agent 在执行高风险操作前，如何：

- 请求确认
- 限制权限
- 防止误操作

### 03_agent_hook

理解如何通过 Hook 机制：

- 在关键节点插入逻辑
- 记录事件
- 做审计、监控或改写行为

### 04_agent_todo

理解如何把复杂任务拆成待办项，并持续跟踪：

- 任务拆分
- 状态更新
- 完成确认
- 结果汇总

### 05_subagent

理解如何通过子代理完成分工协作：

- 主 Agent 负责调度
- 子代理负责局部任务
- 最后汇总结果

### 06_skills

理解如何把稳定能力封装成可复用模块：

- 按需加载
- 按场景执行
- 减少重复提示词

### 07_context_compact

理解长期运行 Agent 如何控制上下文增长：

- 检测上下文长度
- 摘要历史内容
- 保留关键状态
- 持续运行

## 推荐阅读顺序

如果你是第一次接触这个仓库，建议按下面路径学习：

1. 先看 `01_agent_loop`
2. 再看 `02_agent_permission` 和 `03_agent_hook`
3. 然后看 `04_agent_todo` 和 `05_subagent`
4. 接着看 `06_skills`
5. 最后看 `07_context_compact`

这样可以从“基础执行”逐步过渡到“工程化 Agent 能力”。

## 依赖与运行环境

本仓库示例通常基于 Python 和 `uv` 运行。

如果你的本地环境尚未安装 `uv`，请先安装再运行示例。

## 说明

这是一个学习型仓库，重点不是抽象完整产品，而是通过一个个小例子帮助你建立 Agentic AI 的工程理解。

如果你希望，我还可以继续帮你把：

- 每个子目录的 README 统一风格化
- 根 README 增加项目结构图
- 增加“快速开始”与“常见问题”部分
- 顺手补一个英文版 README
