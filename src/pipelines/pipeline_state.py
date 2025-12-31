from typing import TypedDict, Annotated, Literal, Optional, List, Dict, Any


class PipelineState(TypedDict):
    service_name: str
    user_input: str
    llm_messages: List[Dict[str, Any]]
    llm_response: Optional[str] = None

    