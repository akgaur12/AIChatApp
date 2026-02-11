from typing import Any, TypedDict


class PipelineState(TypedDict):
    service_name: str
    user_input: str
    llm_messages: list[dict[str, Any]]
    llm_response: str | None = None
    input_tokens: int | None = 0
    output_tokens: int | None = 0
    response_time: float | None = 0.0

    