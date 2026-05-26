import json
import os

import truststore


from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

truststore.inject_into_ssl()
load_dotenv(override=True)
WORKING_DIR = Path.cwd()

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
]

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)


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
        for match in g.glob(pattern, root_dir=WORKING_DIR):
            if (WORKING_DIR / match).resolve().is_relative_to(WORKING_DIR):
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
}


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
            return

        for choice in msg.tool_calls:
            name = choice.function.name
            args = json.loads(choice.function.arguments)
            print(f"[{name}] {args}")
            handler = TOOL_HANDLERS.get(name)
            if handler is None:
                output = f"Error: unknown tool '{name}'"
            else:
                try:
                    output = handler(args)
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
    messages.append({"role": "user", "content": user_input})
    agent_loop(messages)
    print(messages[-1]["content"])
