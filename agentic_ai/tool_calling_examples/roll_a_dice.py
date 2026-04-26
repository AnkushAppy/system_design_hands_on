
from __future__ import annotations

import logging
import random
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)
from utility import LlmCallMetricsHandler

@tool
def roll_a_dice() -> int:
    """Roll a dice"""
    return random.randint(1, 6)

tools = [roll_a_dice]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    tools,
    system_prompt="You are a dice agent. You are given a dice and you need to roll it.",
)

user_query = "Roll a dice"   

def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config={
            "run_name": "roll_a_dice",
            "tags": ["dice", "tool-calling"],
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