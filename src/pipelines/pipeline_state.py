from typing import TypedDict, Annotated, Literal, Optional, List, Dict, Any


class PipelineState(TypedDict):
    service_name: str
    user_input: str
    llm_messages: List[Dict[str, Any]]
    llm_response: Optional[str] = None
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0
    response_time: Optional[float] = 0.0

    