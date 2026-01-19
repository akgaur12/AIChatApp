from typing import Any, Optional, Dict
from langchain_core.messages import AIMessage
from src.utils import load_config

cfg = load_config()
llm_cfg = cfg.get("LLM", {})
default_inference_type = llm_cfg.get("Provider", "").lower()


def parse_response(llm_response: Any, inference_type: str = default_inference_type) -> AIMessage:
    content: str = ""
    reasoning_content: Optional[str] = None
    metadata: Dict[str, Any] = {}

    if inference_type == "openai":
        content = llm_response.choices[0].message.content
        reasoning_content = getattr(llm_response.choices[0].message, "reasoning_content", None)
        metadata = getattr(llm_response, "usage", {}) or {}

    elif inference_type == "aws_bedrock":
        content = llm_response.content[1].get("text", "")
        reasoning_content = llm_response.content[0].get("reasoning_content", {}).get("text")
        metadata = getattr(llm_response, "usage_metadata", {}) or {}

    elif inference_type == "nvidia":
        content = getattr(llm_response, "content", "")
        reasoning_content = getattr(
            llm_response, "response_metadata", {}
        ).get("reasoning_content")
        metadata = getattr(llm_response, "usage_metadata", {}) or {}

    else:  # ollama, vllm, groq, google, huggingface
        content = getattr(llm_response, "content", str(llm_response))
        reasoning_content = getattr(llm_response, "reasoning_content", None)
        metadata = getattr(llm_response, "usage_metadata", {}) or {}

    return AIMessage(
        content=content or "",
        additional_kwargs={"reasoning_content": reasoning_content},
        response_metadata=metadata,
    )
