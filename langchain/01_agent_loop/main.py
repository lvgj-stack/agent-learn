import os
import urllib

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain.agents.middleware import TodoListMiddleware
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(
    model=os.environ.get("OPENAI_MODEL"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


@tool
def run_bash_command(command: str) -> str:
    """Run a bash command and return the output."""
    import subprocess

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout


@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch the document from a URL."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"
    text = raw.decode("utf-8", errors="replace")
    return text


agent = create_agent(
    model=model,
    tools=[get_weather, run_bash_command, fetch_text_from_url],
    system_prompt="You are a helpful assistant",
    middleware=[TodoListMiddleware()],
)


# messages = [{"role": "user", "content": "分析这个项目"}]
# result = agent.invoke({"messages": messages})

# print(result["messages"][-1].content)


for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "分析这个项目"}]},
    stream_mode="values",
):
    # Each chunk contains the full state at that point
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        if isinstance(latest_message, HumanMessage):
            print(f"User: {latest_message.content}")
        elif isinstance(latest_message, AIMessage):
            print(f"Agent: {latest_message.content}")
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
