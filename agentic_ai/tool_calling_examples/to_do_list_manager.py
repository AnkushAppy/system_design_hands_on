from __future__ import annotations

import logging
from enum import StrEnum

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_openai import ChatOpenAI

from utility import LlmCallMetricsHandler

logger = logging.getLogger(__name__)

my_todo_list = []

@tool
def add_to_todo(task: str):
    """Add a task to the to do list"""
    my_todo_list.append(task)

@tool
def read_todos() -> list[str]:
    """Read the to do list"""
    return my_todo_list

tools = [add_to_todo, read_todos]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    tools,
    system_prompt="You are a to do list manager. You are given a task and you need to add it to the to do list.",
)

user_query = "Add a task to the to do list: 'Buy groceries'"
user_query2 = "Read the to do list"

def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config={
            "run_name": "to_do_list_manager",
            "tags": ["to_do_list", "tool-calling"],
            "callbacks": [usage_callback, metrics_handler],
        },
    )

    if usage_callback.usage_metadata:
        logger.info("cumulative_usage_by_model=%s", usage_callback.usage_metadata)
    for message in result["messages"]:
        if hasattr(message, "pretty_print"):
            message.pretty_print()
        else:
            print(message)
    
    result2 = agent.invoke(
        {"messages": [{"role": "user", "content": user_query2}]},
        config={
            "run_name": "to_do_list_manager",
            "tags": ["to_do_list", "tool-calling"],
            "callbacks": [usage_callback, metrics_handler],
        },
    )
    if usage_callback.usage_metadata:
        logger.info("cumulative_usage_by_model=%s", usage_callback.usage_metadata)
    for message in result2["messages"]:
        if hasattr(message, "pretty_print"):
            message.pretty_print()
        else:
            print(message)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()