
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
def extract_structured_data(first_name: str, last_name: str, age: int, email: str) -> dict:
    """Extract structured data from a given text"""
    return {"first_name": first_name, "last_name": last_name, "age": age, "email": email}

tools = [extract_structured_data]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    tools,
    system_prompt="You are a structured data extractor. You are given a first name, last name, age, and email. You need to extract the structured data from the text.",
)

user_query = "I am John Doe and I am 30 years old. My email is john.doe@example.com."

def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config={
            "run_name": "structured_data_extractor",
            "tags": ["structured_data", "tool-calling"],
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