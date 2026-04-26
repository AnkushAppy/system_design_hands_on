"""
The Multi-Step Travel Planner
Why it's great: This tests "Agentic" reasoning.
The LLM has to use multiple independent tools, combine their results,
and do math to give you a final answer.

The Tools: Write two tools:
get_flight_cost(destination: str) (returns a mock cost of $400)
and
get_hotel_cost(destination: str, nights: int) (returns a mock cost of $150 * nights).

The Test Prompt: "I want to go to Paris for 4 nights. What will be the total cost of my flight and hotel?"
"""

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


from utility import LlmCallMetricsHandler

logger = logging.getLogger(__name__)

@tool
def get_flight_cost(destination: str) -> float:
    """Get the cost of a flight to a destination"""
    return 400.0


@tool
def get_hotel_cost(destination: str, nights: int) -> float:
    """Get the cost of a hotel stay for a given destination and number of nights"""
    return 150.0 * nights


tools = [get_flight_cost, get_hotel_cost]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    tools,
    system_prompt=(
        "You are a travel agent. You are given a destination and a number of nights. "
        "You need to return the total cost of the flight and the hotel."
    ),
)

user_query = (
    "I want to go to Paris for 4 nights. "
    "What will be the total cost of my flight and hotel?"
)


def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config={
            "run_name": "travel_planner",
            "tags": ["travel", "tool-calling"],
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
