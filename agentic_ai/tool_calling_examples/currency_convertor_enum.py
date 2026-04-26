from __future__ import annotations

import logging
from enum import StrEnum

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_openai import ChatOpenAI

from utility import LlmCallMetricsHandler

logger = logging.getLogger(__name__)


class Currency(StrEnum):
    """Supported currencies for the mock exchange table."""

    DOLLAR = "dollar"
    RUPEES = "rupees"
    DINAR = "dinar"


_CURRENCY_EXCHANGE_RATE: dict[str, dict[str, float]] = {
    Currency.DOLLAR: {
        Currency.RUPEES: 100.0,
        Currency.DINAR: 120.0,
    },
    Currency.RUPEES: {
        Currency.DOLLAR: 0.8,
        Currency.DINAR: 0.4,
    },
    Currency.DINAR: {
        Currency.DOLLAR: 0.9,
        Currency.RUPEES: 20.0,
    },
}


@tool
def currency_converter(
    currency_name: Currency,
    currency_to_be_converted: Currency,
    currency_value: float = 1.0,
) -> dict[str, float]:
    """Convert an amount from one currency to another using a fixed mock rate table.

    Args:
        currency_name: Source currency.
        currency_to_be_converted: Target currency (what you want to convert to).
        currency_value: Amount in the source currency; defaults to 1.0 if omitted.
    """
    rate = _CURRENCY_EXCHANGE_RATE[currency_name][currency_to_be_converted]
    return {"rate": rate, "exchange_value": rate*currency_value}


tools = [currency_converter]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

agent = create_agent(
    llm,
    tools,
    system_prompt=(
        "You are an expert on mock exchange rates between dollar, rupees, and dinar. "
        "If the user has not given enough to convert, ask: "
        "'Please provide the currency name, the currency you want to convert to, and the amount you wish to convert. "
        "If you don't specify an amount, I will assume it is 1.0.' "
        "When you know the source currency, target currency, and amount (use 1.0 if the amount is missing), "
        "call currency_converter and explain the result clearly."
    ),
)


def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    user_query = "Convert 3 dollars to rupees."
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_query}]},
        config={
            "run_name": "currency_convertor_enum",
            "tags": ["currency_converter", "tool-calling"],
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
