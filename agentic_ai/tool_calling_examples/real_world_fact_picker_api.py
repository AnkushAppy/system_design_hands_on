from __future__ import annotations

import logging
from enum import StrEnum

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_openai import ChatOpenAI

from utility import LlmCallMetricsHandler

import requests

logger = logging.getLogger(__name__)

@tool
def real_world_fact_api() -> str:
    """API to fetch a real world fact"""
    resp = requests.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
    return resp.json()['text']


tools = [real_world_fact_api]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    tools,
    system_prompt = "Yor are a world fact expert. and can fetch a world fact when asked"
)

user_query = "tell me a world fact"


def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config={
            "run_name": "real_world_fact_picker_api",
            "tags": ["real_world_fact_api", "tool-calling"],
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
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()