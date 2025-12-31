import os, logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrockConverse

from src.utils import load_config

load_dotenv()
cfg = load_config()
logger = logging.getLogger(__name__)

llm_cfg = cfg["LLM"]
inference_type = llm_cfg["Provider"].lower()

AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if inference_type == "ollama":
    ollama_cfg = llm_cfg["ollama"]
    llm_model = ChatOllama(
        model = ollama_cfg["MODEL"],
        base_url = ollama_cfg["BASE_URL"],
        temperature = ollama_cfg["TEMPERATURE"],
        reasoning_effort = ollama_cfg["REASONING_EFFORT"],
    )

elif inference_type == "vllm":
    vllm_cfg = llm_cfg["vllm"]
    llm_model = ChatOpenAI(
        model_name = vllm_cfg["MODEL"],
        openai_api_key = vllm_cfg["API_KEY"],
        openai_api_base = vllm_cfg["BASE_URL"],
        temperature = vllm_cfg["TEMPERATURE"],
        reasoning_effort = vllm_cfg["REASONING_EFFORT"],
    )

elif inference_type == "aws_bedrock":
    aws_bedrock_cfg = llm_cfg["aws_bedrock"]
    llm_model = ChatBedrockConverse(
        aws_access_key_id = AWS_KEY,
        aws_secret_access_key = AWS_SECRET,
        model_id = aws_bedrock_cfg["MODEL"],
        region_name = aws_bedrock_cfg["AWS_REGION"],
        temperature = aws_bedrock_cfg["TEMPERATURE"],
        additional_model_request_fields = {"reasoning_effort": aws_bedrock_cfg["REASONING_EFFORT"]},
    )

elif inference_type == "groq":
    groq_cfg = llm_cfg["groq"]
    llm_model = ChatGroq(
        api_key = GROQ_API_KEY,
        model = groq_cfg["MODEL"],
        temperature = groq_cfg["TEMPERATURE"],
        reasoning_effort = groq_cfg["REASONING_EFFORT"],
    )

else:
    raise ValueError(f"Invalid inference type: {inference_type}")

    
