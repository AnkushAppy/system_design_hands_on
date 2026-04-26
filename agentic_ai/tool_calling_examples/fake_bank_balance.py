
from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.callbacks import BaseCallbackHandler, UsageMetadataCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)
from utility import LlmCallMetricsHandler

@tool
def get_bank_balance(account_holder_name: str) -> float:
    """Get the balance of a bank account"""

    bank_database = {
        "John Doe": 1000.0,
        "Jane Smith": 2000.0,
        "Jim Beam": 3000.0,
        "Jill Johnson": 4000.0,
        "Jack Johnson": 5000.0,
        "Jill Smith": 6000.0,
        "Jack Smith": 7000.0,
        "Jill Johnson": 8000.0,
    }
    
    return bank_database.get(account_holder_name, 0.0)


tools = [get_bank_balance]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    tools,
    system_prompt="You are a bank agent. You are given a name and you need to return the balance of the account.",
)

user_query = "What is the balance of John Doe's account?"   

def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config={
            "run_name": "bank_balance",
            "tags": ["bank", "tool-calling"],
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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    # Keep LLM/metrics lines front-and-center; set httpx to DEBUG to log HTTP calls.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()