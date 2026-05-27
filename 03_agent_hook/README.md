# 02_agent_permission

在 [../01_agent_loop/](../01_agent_loop/) 的基础上加入**权限系统**,演示一个生产级 Agent 在执行工具前应该做哪些校验。

## 三层权限模型

模型每次发起 tool call,都会先经过 `check_permission()`,流程:

```
tool_call
   │
   ├── 1. Deny list   ── 命中 → 直接拒绝(无需询问)
   │
   ├── 2. Rule check  ── 命中 → 询问用户(y/N)
   │
   └── 3. 通过         ── 执行工具
```

### 1. Deny list — 硬性禁止

`DENY_LIST` 中的危险模式(`rm -rf /`、`sudo`、`reboot`、`shutdown`)一旦命中,**直接拒绝**,不询问用户。

### 2. Rule check — 询问用户

`PERMISSION_RULES` 描述「敏感但不至于禁止」的操作,例如 `bash` 命令含 `rm`、写入 `/etc/`、`chmod 777`。命中后会在终端打印警告并等待用户输入 `y/N`。

```python
PERMISSION_RULES = [
    {
        "tools": ["bash"],
        "check": lambda args: any(
            kw in args.get("command", "") for kw in ["rm", "> /etc/", "chmod 777"]
        ),
        "message": "bash command violates permission rule",
    }
]
```

### 3. 路径沙箱

`safe_path()` 把所有路径解析到 `WORKDIR` 下,防止 `../../etc/passwd` 之类的越权访问。

> 注:当前 `read_file` / `write_file` 还**没用上** `safe_path`,这是已知 TODO。

## 被拒绝时如何反馈给模型

权限不通过时,不是简单地中断 loop,而是往 `messages` 里塞一条 `role="tool"` 的错误回执:

```python
{"role": "tool", "tool_call_id": ..., "content": "Error: permission denied for ..."}
```

这样模型能"看到"拒绝原因,从而调整下一步策略,而不是反复重试同一个命令。

## 运行

```bash
uv run 02_agent_permission/main.py
```

`.env` 同 [../01_agent_loop/](../01_agent_loop/)。

试一下下面这种会触发权限询问的指令:

```
User: 帮我删掉当前目录下所有 .log 文件
```

## TODO

- `read_file` / `write_file` 接入 `safe_path` 真正做沙箱
- 把权限规则做成可插拔(读 YAML / JSON)
- 支持"记住这次选择"(类似 Claude Code 的 always-allow)
