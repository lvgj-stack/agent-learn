import json
import os

import truststore


from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

truststore.inject_into_ssl()
load_dotenv(override=True)
WORKDIR = Path.cwd()

MODEL = os.environ.get("OPENAI_MODEL")

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Useful for when you want to run bash commands",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Useful for when you want to read user file content",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename to read",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "Useful for when you want to write user file content",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Useful for when you want to search the web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Useful for when you want to glob files",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The pattern to glob",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "todo_write",
            "description": "Useful for when you want to write user todo list",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "The content of the todo",
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                },
                            },
                        },
                    },
                },
            },
        },
    },
]

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)


def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


def run_bash_command(command: str) -> str:
    """Run a bash command and return the output."""
    import subprocess

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout


def read_file(filename: str) -> str:
    """Read the content of a file."""
    pwd = os.getcwd()
    with open(os.path.join(pwd, filename), "r") as f:
        return f.read()


def run_glob(pattern: str) -> list:
    """Runlob files."""
    import glob as g

    try:
        results = []
        for match in g.glob(pattern, root_dir=WORKDIR):
            if (WORKDIR / match).resolve().is_relative_to(WORKDIR):
                results.append(match)
        return "\n".join(results) if results else "No files found"
    except Exception as e:
        return f"Error: {e}"


def write_file(filename: str, content: str) -> None:
    """Write the content of a file."""
    pwd = os.getcwd()
    with open(os.path.join(pwd, filename), "w") as f:
        f.write(content)
        return content


def web_search(query: str) -> str:
    """Search the web and return the results."""
    return f"Searching the web for {query}..."


TOOL_HANDLERS = {
    "bash": lambda args: run_bash_command(args["command"]),
    "glob": lambda args: run_glob(args["pattern"]),
    "read": lambda args: read_file(args["filename"]),
    "write": lambda args: write_file(args["filename"], args["content"]),
    "web_search": lambda args: web_search(args["query"]),
    "todo_write": lambda args: run_todo_write(args["todos"]),
}

DENY_LIST = ["rm -rf /", "sudo", "reboot", "shutdown"]


def check_deny_list(command: str) -> str:
    for pattern in DENY_LIST:
        if pattern in command:
            return f"Error: command '{command}' contains deny pattern '{pattern}'"
    return ""


PERMISSION_RULES = [
    {
        "tools": ["bash"],
        "check": lambda args: any(
            kw in args.get("command", "") for kw in ["rm", "> /etc/", "chmod 777"]
        ),
        "message": "bash command violates permission rule",
    }
]


def check_rules(tool_name: str, args: dict) -> str:
    for rule in PERMISSION_RULES:
        if tool_name in rule["tools"] and rule["check"](args):
            return rule["message"]
    return ""


def ask_user(tool_name: str, args: dict, reason: str) -> str:
    print(f"\n\033[33m⚠  {reason}\033[0m")
    print(f"   Tool: {tool_name}({args})")
    choice = input("   Allow? [y/N] ").strip().lower()
    return "allow" if choice in ("y", "yes") else "deny"


def permission_hook(tool_name: str, args: str) -> bool:
    if tool_name == "bash":
        command = args.get("command", "")
        reason = check_deny_list(command)
        if reason:
            print(f"\n\033[31m⛔ {reason}\033[0m")
            return True
    reason = check_rules(tool_name, args)
    if reason:
        choice = ask_user(tool_name, args, reason)
        if choice == "deny":
            return True
    return False


HOOKS = {
    "UserPromptSubmit": [],
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": [],
}


def register_hook(event: str, callback: callable):
    HOOKS[event].append(callback)


def trigger_hook(event: str, *args):
    for callback in HOOKS[event]:
        result = callback(*args)
        if result is not None:
            return result
    return None


def context_inject_hook(query: str) -> str | None:
    print(f"\033[90m[HOOK] UserPromptSubmit: working in {WORKDIR}\033[0m")
    return None  # return None = no modification, let prompt through


def log_hook(event: str, *args):
    print(f"\033[90m[HOOK] {event}: {args}\033[0m")


def large_output_hook(output: str) -> str | None:
    if len(output) > 100000:
        print(
            f"\033[90m[HOOK] PostToolUse: output truncated from {len(output)} to 1024 chars\033[0m"
        )
        return output[:1024]
    return None


def summary_hook(messages: list) -> str | None:
    total_chars = sum(len(msg.get("content") or "") for msg in messages)
    print(f"\033[90m[HOOK] Stop: {total_chars} chars in context\033[0m")


CURRENT_TODOS: list[dict] = []


def run_todo_write(todos: list) -> str:
    global CURRENT_TODOS
    CURRENT_TODOS = todos

    lines = ["\n ## Current Tasks"]
    for todo in CURRENT_TODOS:
        icon = {"pending": " ", "in_progress": ">", "completed": "✓"}[todo["status"]]
        lines.append(f"- {icon} {todo['content']}")
    print("\n".join(lines))
    return f"Update {len(CURRENT_TODOS)} tasks"


register_hook("UserPromptSubmit", context_inject_hook)
register_hook("PreToolUse", log_hook)
register_hook("PreToolUse", permission_hook)
register_hook("PostToolUse", large_output_hook)
register_hook("Stop", summary_hook)


def agent_loop(messages: list, max_iterations: int = 20):
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            max_tokens=1024,
        )

        msg = response.choices[0].message
        assistant_msg = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        messages.append(assistant_msg)

        if response.choices[0].finish_reason != "tool_calls":
            force = trigger_hook("Stop", messages)
            if force:
                messages.append({"role": "user", "content": force})
                continue
            return

        for choice in msg.tool_calls:
            name = choice.function.name
            args = json.loads(choice.function.arguments)
            blocked = trigger_hook("PreToolUse", name, args)
            if blocked:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": choice.id,
                        "content": f"Error: permission denied for {name}({args})",
                    }
                )
                continue

            handler = TOOL_HANDLERS.get(name)
            if handler is None:
                output = f"Error: unknown tool '{name}'"
            else:
                try:
                    output = handler(args)
                    modified = trigger_hook("PostToolUse", output)
                    if modified is not None:
                        output = modified
                except Exception as e:
                    output = f"Error: {e}"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": choice.id,
                    "content": output,
                }
            )

    raise RuntimeError(f"Agent exceeded {max_iterations} iterations")


if __name__ == "__main__":
    print("Starting agent loop. Type 'exit' or 'quit' to stop.")
    messages = [{"role": "system", "content": SYSTEM}]
    user_input = input("User: ")
    trigger_hook("UserPromptSubmit", user_input)
    messages.append({"role": "user", "content": user_input})
    agent_loop(messages)
    print(messages[-1]["content"])
