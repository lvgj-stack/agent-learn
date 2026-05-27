# 02_agent_permission

这个示例在基础 Agent 循环上增加了 **权限控制** 能力，用来演示：

- 如何在工具执行前做安全检查
- 如何拦截高风险命令
- 如何在必要时向用户申请确认

它适合用来理解“Agent 不只是会调用工具，还需要可控”这个概念。

## 这个示例做了什么

相较于 `01_agent_loop`，这里新增了权限相关逻辑：

- `DENY_LIST`：黑名单规则，直接拒绝高风险命令
- `PERMISSION_RULES`：命中规则后请求用户确认
- `permission_hook(...)`：统一权限入口

## 权限判断流程

```text
模型请求工具
   ↓
PreToolUse
   ↓
检查黑名单
   ↓
检查权限规则
   ↓
必要时询问用户
   ↓
允许执行 / 拒绝执行
```

## 示例中的安全策略

### 1. 黑名单拒绝

以下命令模式会直接拦截：

- `rm -rf /`
- `sudo`
- `reboot`
- `shutdown`

### 2. 交互式确认

对于一些可疑但未必绝对危险的操作，会提示用户：

```text
⚠  bash command violates permission rule
   Tool: bash({...})
   Allow? [y/N]
```

用户确认后才会继续执行。

## 运行方式

```bash
uv run 02_agent_permission/main.py
```

## 适合重点观察的地方

- 哪些命令会被直接拒绝
- 哪些命令会要求确认
- 权限逻辑和工具执行逻辑如何解耦

## 代码中的关键函数

- `check_deny_list(...)`
- `check_rules(...)`
- `ask_user(...)`
- `permission_hook(...)`

## 注意事项

这个示例仍然包含 `bash` 工具，因此即使加了权限控制，也建议在测试环境中运行，避免误操作生产环境文件。