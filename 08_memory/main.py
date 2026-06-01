import json
import os
import readline  # noqa: F401 — enables proper CJK backspace in input()

import truststore
import time
import re


from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

truststore.inject_into_ssl()
load_dotenv(override=True)
WORKDIR = Path.cwd()
SKILLS_DIR = WORKDIR / "skills"
MEMORY_DIR = WORKDIR / ".memory"
MEMORY_INDEX = MEMORY_DIR / "MEMORY.md"
MEMORY_DIR.mkdir(exist_ok=True)
MODEL = os.environ.get("OPENAI_MODEL")
SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."
SUB_SYSTEM = (
    f"You are a coding agent at {WORKDIR}. "
    "Complete the task you were given, then return a concise summary. "
    "Do not delegate further."
)

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
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": "Useful for when you want to load skill content",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the skill to load",
                    },
                },
            },
        },
    },
]

TOOLS.append(
    {
        "type": "function",
        "function": {
            "name": "task",
            "description": "Launch a subagent to complete a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The description of the task",
                    },
                },
            },
        },
    },
)

SUB_TOOLS = [
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
    "task": lambda args: spawn_subagent(args["description"]),
    "load_skill": lambda args: load_skill(args["name"]),
}

SUB_TOOL_HANDLERS = {
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


def spawn_subagent(description: str) -> str:
    """Spawn a subagent."""
    messages = [
        {"role": "system", "content": SUB_SYSTEM},
        {"role": "user", "content": description},
    ]

    for _ in range(20):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=SUB_TOOLS,
            max_tokens=1024,
        )
        msg = response.choices[0].message
        assistant_msg = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        messages.append(assistant_msg)
        if response.choices[0].finish_reason != "tool_calls":
            break
        results = []
        for choice in msg.tool_calls:
            name = choice.function.name
            args = json.loads(choice.function.arguments)
            blocked = trigger_hook("PreToolUse", name, args)
            if blocked:
                results.append({
                    "role": "tool",
                    "tool_call_id": choice.id,
                    "content": f"Error: permission denied for {name}({args})",
                })
                continue
            handler = SUB_TOOL_HANDLERS.get(name)
            if handler is None:
                output = f"Error: unknown tool '{name}'"
            else:
                try:
                    output = handler(args)
                    trigger_hook("PostToolUse", output)
                except Exception as e:
                    output = f"Error: {e}"
            results.append({
                "role": "tool",
                "tool_call_id": choice.id,
                "content": output,
            })
        messages.append({"role": "user", "content": "\n".join(results)})

    return "Subagent spawned"


register_hook("UserPromptSubmit", context_inject_hook)
register_hook("PreToolUse", log_hook)
register_hook("PreToolUse", permission_hook)
register_hook("PostToolUse", large_output_hook)
register_hook("Stop", summary_hook)

SKILL_REGISTRY: dict[str, dict] = {}


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from SKILL.md. Returns (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, parts[2].strip()


def _scan_skills():
    if not SKILLS_DIR.exists():
        return
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir():
            continue
        manifest = d / "SKILL.md"
        if manifest.exists():
            raw = manifest.read_text()
            meta, body = _parse_frontmatter(raw)
            name = meta.get("name", d.name)
            desc = meta.get("description", raw.split("\n")[0].lstrip("#").strip())
            SKILL_REGISTRY[name] = {"name": name, "description": desc, "content": raw}
            continue


_scan_skills()


def list_skill() -> str:
    return "\n".join([
        f"- **{skill['name']}**: {skill['description']}"
        for skill in SKILL_REGISTRY.values()
    ])


def read_memory_index() -> str:
    """Read MEMORY.md index (injected into SYSTEM every turn)."""
    if not MEMORY_INDEX.exists():
        return ""
    return MEMORY_INDEX.read_text().strip()


def build_system() -> str:
    catalog = list_skill()
    index = read_memory_index()
    memories_section = f"\n\nMemories available:\n{index}" if index else ""
    return f"""You are a helpful assistant that can use the following skills:
{catalog}
Use load_skill to get full details when needed.{memories_section}

Relevant memory content is injected into the user turn below. Respect user
preferences from memory. When the user says 'remember' or expresses a clear
preference, it will be extracted into memory after the turn."""


def load_skill(name: str) -> str:
    """Load full skill content. Lookup via registry — no path traversal."""
    skill = SKILL_REGISTRY.get(name)
    if not skill:
        return f"Skill not found: {name}"
    return skill["content"]


SYSTEM = build_system()


def snip_compact(messages: list, max_messages: int = 50):
    """Keep head + tail, snip middle tool-call exchanges as atomic units."""
    if len(messages) <= max_messages:
        return messages

    head_keep = 3
    keep_tail = max_messages - head_keep - 1  # -1 for the placeholder

    # Head must not end with an assistant that has pending tool_calls
    while head_keep > 2 and messages[head_keep - 1].get("tool_calls"):
        head_keep -= 1

    tail_start = len(messages) - keep_tail
    if tail_start <= head_keep:
        return messages

    # Tail must not start on an orphaned tool response
    while tail_start < len(messages) and messages[tail_start]["role"] == "tool":
        tail_start -= 1

    if tail_start <= head_keep:
        return messages

    middle = messages[head_keep:tail_start]
    snipped = len(middle)

    if snipped <= 0:
        return messages

    placeholder = {
        "role": "user",
        "content": f"[Earlier context snipped — {snipped} messages removed]",
    }
    return messages[:head_keep] + [placeholder] + messages[tail_start:]


KEEP_RECENT_TOOL_RESULTS = 3
CONTEXT_LIMIT = 50000
KEEP_RECENT = 3
PERSIST_THRESHOLD = 30000
TOOL_RESULTS_DIR = WORKDIR / ".task_outputs" / "tool-results"
TRANSCRIPT_DIR = WORKDIR / ".transcripts"


def collect_tool_results(messages: list):
    blocks = []
    for mi, msg in enumerate(messages):
        if msg["role"] == "tool":
            blocks.append(msg)
    return blocks


def micro_compact(messages: list):
    tool_results = collect_tool_results(messages)
    if len(tool_results) <= KEEP_RECENT_TOOL_RESULTS:
        return messages
    for msg in tool_results[:-KEEP_RECENT_TOOL_RESULTS]:
        if len(msg.get("content", "")) > 120:
            msg["content"] = "[Earlier tool result compacted. Re-run if needed.]"
    return messages


def tool_result_budget(messages, max_bytes=200_00):
    last = messages[-1] if messages else None
    if not last or last.get("role") != "tool":
        return messages
    total = len(last.get("content", ""))
    if total <= max_bytes:
        return messages
    if total > max_bytes:
        content = str(last.get("content", ""))
        tid = last.get("tool_call_id", "unknown")
        last["content"] = persist_large_output(tid, content)
        total = len(last.get("content", ""))
    return messages


def persist_large_output(tool_use_id, output):
    if len(output) <= PERSIST_THRESHOLD:
        return output
    TOOL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = TOOL_RESULTS_DIR / f"{tool_use_id}.txt"
    if not path.exists():
        path.write_text(output)
    return f"<persisted-output>\nFull output: {path}\nPreview:\n{output[:2000]}\n</persisted-output>"


def write_transcript(messages):
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    path = TRANSCRIPT_DIR / f"transcript_{int(time.time())}.jsonl"
    with path.open("w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    return path


def summarize_history(messages):
    conversation = json.dumps(messages, default=str)[:80000]
    prompt = (
        "Summarize this coding-agent conversation so work can continue.\n"
        "Preserve: 1. current goal, 2. key findings/decisions, 3. files read/changed, "
        "4. remaining work, 5. user constraints.\nBe compact but concrete.\n\n"
        + conversation
    )
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}], max_tokens=8000
    )
    return (
        "\n".join(
            getattr(block.message, "content", "")
            for block in response.choices
            if getattr(block, "message", None)
            and getattr(block.message, "content", None) is not None
        ).strip()
        or "(empty summary)"
    )


def compact_history(messages: list):
    transcript_path = write_transcript(messages)
    print(f"[transcript saved: {transcript_path}]")
    summary = summarize_history(messages)
    return [{"role": "user", "content": f"[Compacted]\n\n{summary}"}]


CONTEXT_LIMIT = 1 * 1024 * 1024 * 0.8


def estimate_size(msgs):
    return len(str(msgs))


MEMORY_TYPES = ["user", "feedback", "project", "reference"]


def _rebuild_index():
    """Rebuild memory index."""
    lines = []
    for f in sorted(MEMORY_DIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        raw = f.read_text()
        meta, body = _parse_frontmatter(raw)
        name = meta.get("name", f.stem)
        desc = meta.get("description", raw.split("\n")[0][:80])
        lines.append(f"- [{name}]({f.name}) - {desc}")
    MEMORY_INDEX.write_text("\n".join(lines))


def write_memory_file(name: str, mem_type: str, description: str, body: str):
    """Write memory file.

    Args:
        name (str): _description_
        mem_type (str): _description_
        description (str): _description_
        body (str): _description_
    """
    slug = name.lower().replace(" ", "-").replace("/", "-")
    filename = f"{slug}.md"
    filepath = MEMORY_DIR / filename
    filepath.write_text(
        f"---\nname: {name}\ndescription: {description}\ntype: {mem_type}\n---\n\n{body}\n"
    )
    _rebuild_index()
    return filepath


def extract_text(content) -> str:
    """Extract text from a string."""
    if not isinstance(content, list):
        return str(content)
    return " ".join(
        str(getattr(b, "text", ""))
        for b in content
        if getattr(b, "type", None) == "text"
    )


def list_memory_files() -> list:
    """List memory files."""
    results = []
    for f in sorted(MEMORY_DIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        raw = f.read_text()
        meta, body = _parse_frontmatter(raw)
        results.append({
            "filename": f.name,
            "name": meta.get("name", f.stem),
            "description": meta.get("description", ""),
            "type": meta.get("type", "user"),
            "body": body,
        })
    return results


def _content_to_text(content) -> str:
    """Flatten an OpenAI message `content` (str or list of parts) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # OpenAI multimodal parts are dicts: {"type": "text", "text": "..."}
        return " ".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def select_relevant_memories(messages: list, max_item: int = 3) -> list:
    """Pick the memory files most relevant to the recent user turns.

    Uses an OpenAI chat completion to score the memory catalog against the
    recent conversation, falling back to keyword matching if the call fails.
    """
    files = list_memory_files()
    if not files:
        return []

    # Gather the last few user turns as context for relevance scoring.
    recent_texts = []
    for msg in reversed(messages):
        if msg.get("role") == "user":
            text = _content_to_text(msg.get("content", ""))
            if text:
                recent_texts.append(text)
            if len(recent_texts) >= 3:
                break
    recent = " ".join(reversed(recent_texts))[:2000]
    if not recent.strip():
        return []

    catalog = "\n".join(
        f"{i}: {f['name']} - {f['description']}" for i, f in enumerate(files)
    )
    prompt = (
        "Given the recent conversation and the memory catalog below, "
        "select the indices of memories that are clearly relevant. "
        "Return ONLY a JSON array of integers, e.g. [0, 3]. "
        "If none are relevant, return [].\n\n"
        f"Recent conversation:\n{recent}\n\n"
        f"Memory catalog:\n{catalog}"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000,
        )
        text = (response.choices[0].message.content or "").strip()
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            indices = json.loads(match.group())
            selected = []
            for idx in indices:
                if isinstance(idx, int) and 0 <= idx < len(files):
                    selected.append(files[idx]["filename"])
                    if len(selected) >= max_item:
                        break
            return selected
    except Exception:
        pass

    # Fallback: keyword overlap between the recent text and name + description.
    keywords = [w.lower() for w in recent.split() if len(w) > 3]
    selected = []
    for f in files:
        haystack = (f["name"] + " " + f["description"]).lower()
        if any(kw in haystack for kw in keywords):
            selected.append(f["filename"])
            if len(selected) >= max_item:
                break
    return selected


def read_memory_file(filename: str) -> str:
    """Read memory file."""
    filepath = MEMORY_DIR / filename
    if not filepath.exists():
        return f"Memory file not found: {filename}"
    return filepath.read_text()


def load_memory(messages: list) -> str:
    """Load memory index."""
    selected_files = select_relevant_memories(messages)
    if not selected_files:
        return ""

    parts = ["<relevant_memories>"]
    for f in selected_files:
        content = read_memory_file(f)
        if content:
            parts.append(content)
    parts.append("</relevant_memories>")
    return "\n\n".join(parts)


def _dialogue_text(messages: list, limit: int = 10) -> str:
    """Flatten recent messages into plain text for the memory LLM calls."""
    parts = []
    for msg in messages[-limit:]:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                str(getattr(b, "text", b)) for b in content
            )
        if isinstance(content, str) and content.strip():
            parts.append(f"{role}: {content}")
    return "\n".join(parts)


def extract_memories(messages: list):
    """Extract new memories from recent dialogue. Runs after each turn."""
    dialogue = _dialogue_text(messages, limit=10)
    if not dialogue.strip():
        return

    existing = list_memory_files()
    existing_desc = (
        "\n".join(f"- {m['name']}: {m['description']}" for m in existing)
        if existing
        else "(none)"
    )

    prompt = (
        "Extract user preferences, constraints, or project facts from this dialogue.\n"
        "Return a JSON array. Each item: {name, type, description, body}.\n"
        "- name: short kebab-case identifier (e.g. 'user-preference-tabs')\n"
        "- type: one of 'user' (user preference), 'feedback' (guidance), "
        "'project' (project fact), 'reference' (external pointer)\n"
        "- description: one-line summary for index lookup\n"
        "- body: full detail in markdown\n"
        "If nothing new or already covered by existing memories, return [].\n\n"
        f"Existing memories:\n{existing_desc}\n\n"
        f"Dialogue:\n{dialogue[:4000]}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000,
        )
        text = (response.choices[0].message.content or "").strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return
        items = json.loads(match.group())
        if not items:
            return
        count = 0
        for mem in items:
            name = mem.get("name", f"memory_{int(time.time())}")
            mem_type = mem.get("type", "user")
            desc = mem.get("description", "")
            body = mem.get("body", "")
            if desc and body:
                write_memory_file(name, mem_type, desc, body)
                count += 1
        if count:
            print(f"\n\033[33m[Memory: extracted {count} new memories]\033[0m")
    except Exception:
        pass


CONSOLIDATE_THRESHOLD = 10


def consolidate_memories():
    """Merge duplicate/stale memories. Triggered when file count >= threshold."""
    files = list_memory_files()
    if len(files) < CONSOLIDATE_THRESHOLD:
        return

    catalog = "\n\n".join(
        f"## {f['filename']}\nname: {f['name']}\ndescription: {f['description']}\n{f['body']}"
        for f in files
    )

    prompt = (
        "Consolidate the following memory files. Rules:\n"
        "1. Merge duplicates into one\n"
        "2. Remove outdated/contradicted memories\n"
        "3. Keep the total under 30 memories\n"
        "4. Preserve important user preferences above all\n"
        "Return a JSON array. Each item: {name, type, description, body}.\n\n"
        f"{catalog[:16000]}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000,
        )
        text = (response.choices[0].message.content or "").strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return
        items = json.loads(match.group())
        if not items:
            return

        # Remove old memory files (keep MEMORY.md)
        for f in MEMORY_DIR.glob("*.md"):
            if f.name != "MEMORY.md":
                f.unlink()

        for mem in items:
            name = mem.get("name", f"memory_{int(time.time())}")
            mem_type = mem.get("type", "user")
            desc = mem.get("description", "")
            body = mem.get("body", "")
            if desc and body:
                write_memory_file(name, mem_type, desc, body)

        print(
            f"\n\033[33m[Memory: consolidated {len(files)} -> {len(items)} memories]\033[0m"
        )
    except Exception:
        pass


def agent_loop(messages: list, max_iterations: int = 20):
    memories_content = load_memory(messages)
    memory_turn = (
        len(messages) - 1
        if messages and isinstance(messages[-1].get("content"), str)
        else None
    )
    while True:
        # Rebuild system each turn so it reflects the current memory index.
        system = build_system()
        if messages and messages[0].get("role") == "system":
            messages[0]["content"] = system
        else:
            messages.insert(0, {"role": "system", "content": system})

        # Snapshot before compression for full-fidelity memory extraction.
        pre_compress = [
            m if isinstance(m, dict) else {"role": m.get("role", ""),
                                           "content": str(m.get("content", ""))}
            for m in messages
        ]

        messages[:] = tool_result_budget(messages)
        messages[:] = snip_compact(messages)
        messages[:] = micro_compact(messages)
        if estimate_size(messages) > CONTEXT_LIMIT:
            print(f"[context size: {estimate_size(messages)} chars] compacting...")
            messages[:] = compact_history(messages)

        # Inject relevant memory content into the current user turn (non-destructive).
        request_messages = messages
        if (
            memories_content
            and memory_turn is not None
            and memory_turn < len(messages)
            and isinstance(messages[memory_turn].get("content"), str)
        ):
            request_messages = list(messages)
            request_messages[memory_turn] = {
                **messages[memory_turn],
                "content": memories_content
                + "\n\n"
                + messages[memory_turn]["content"],
            }

        response = client.chat.completions.create(
            model=MODEL,
            messages=request_messages,
            tools=TOOLS,
            max_tokens=8000,
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
            # Turn finished: mine the dialogue for new memories, then consolidate.
            extract_memories(pre_compress)
            consolidate_memories()
            return

        for choice in msg.tool_calls:
            name = choice.function.name
            args = json.loads(choice.function.arguments)
            blocked = trigger_hook("PreToolUse", name, args)
            if blocked:
                messages.append({
                    "role": "tool",
                    "tool_call_id": choice.id,
                    "content": f"Error: permission denied for {name}({args})",
                })
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

            messages.append({
                "role": "tool",
                "tool_call_id": choice.id,
                "content": output,
            })


if __name__ == "__main__":
    print("s08: Memory — persistent cross-session knowledge")
    print("Type a request and press enter. Type 'exit' or 'quit' to stop.\n")
    messages = [{"role": "system", "content": SYSTEM}]
    while True:
        try:
            user_input = input("User: ")
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.strip().lower() in ("exit", "quit", "q", ""):
            break
        trigger_hook("UserPromptSubmit", user_input)
        messages.append({"role": "user", "content": user_input})
        agent_loop(messages)
        final = messages[-1].get("content")
        if final:
            print(f"\033[32m{final}\033[0m\n")
