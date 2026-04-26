from typing import Any

from uuid import UUID
import time
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatGeneration, LLMResult
import logging
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

class LlmCallMetricsHandler(BaseCallbackHandler):
    """Per chat-model call: wall latency, model id, and token usage (from the response)."""

    def __init__(self) -> None:
        super().__init__()
        self._t0: dict[UUID, float] = {}

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._t0[run_id] = time.perf_counter()
        _id = (serialized or {}).get("id") or (serialized or {}).get("name", "chat_model")
        logger.info("llm_request_start run_id=%s serialized_id=%s", run_id, _id)

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        elapsed_ms: float | None = None
        if run_id in self._t0:
            elapsed_ms = (time.perf_counter() - self._t0.pop(run_id)) * 1000.0

        usage: Any = None
        model_name: Any = None
        finish_reason: Any = None
        try:
            gen = response.generations[0][0]
            if isinstance(gen, ChatGeneration) and isinstance(gen.message, AIMessage):
                usage = gen.message.usage_metadata
                model_name = (gen.message.response_metadata or {}).get("model_name")
                finish_reason = (gen.message.response_metadata or {}).get("finish_reason")
        except (IndexError, AttributeError):
            pass

        logger.info(
            "llm_request_end run_id=%s latency_ms=%s model=%s finish_reason=%s usage_metadata=%s",
            run_id,
            f"{elapsed_ms:.1f}" if elapsed_ms is not None else None,
            model_name,
            finish_reason,
            usage,
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self._t0.pop(run_id, None)
        logger.exception("llm_request_error run_id=%s: %s", run_id, error)


from langchain_openai import ChatOpenAI
# utility function to get the llm
def get_llm(model_name: str, temperature: float = 0, base_url: str = "http://10.193.0.48:8000/v1") -> ChatOpenAI:
    return ChatOpenAI(model=model_name, temperature=temperature, base_url=base_url)