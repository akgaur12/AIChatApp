import os, logging
import multiprocessing
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrockConverse
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_community.chat_models import ChatLlamaCpp

from src.utils import load_config

load_dotenv()
cfg = load_config()
logger = logging.getLogger(__name__)

llm_cfg = cfg["LLM"]
inference_type = llm_cfg["Provider"].lower()

AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if inference_type == "ollama":
    ollama_cfg = llm_cfg["ollama"]
    llm_model = ChatOllama(
        model = ollama_cfg["MODEL"],
        base_url = ollama_cfg["BASE_URL"],
        temperature = ollama_cfg["TEMPERATURE"],
        reasoning_effort = ollama_cfg["REASONING_EFFORT"] if ollama_cfg["MODEL_TYPE"] == "reasoning" else None,
    )

elif inference_type == "vllm":
    vllm_cfg = llm_cfg["vllm"]
    llm_model = ChatOpenAI(
        model_name = vllm_cfg["MODEL"],
        openai_api_key = vllm_cfg["API_KEY"],
        openai_api_base = vllm_cfg["BASE_URL"],
        temperature = vllm_cfg["TEMPERATURE"],
        reasoning_effort = vllm_cfg["REASONING_EFFORT"] if vllm_cfg["MODEL_TYPE"] == "reasoning" else None,
    )

elif inference_type == "aws_bedrock":
    aws_bedrock_cfg = llm_cfg["aws_bedrock"]
    llm_model = ChatBedrockConverse(
        aws_access_key_id = AWS_KEY,
        aws_secret_access_key = AWS_SECRET,
        model_id = aws_bedrock_cfg["MODEL"],
        region_name = aws_bedrock_cfg["AWS_REGION"],
        temperature = aws_bedrock_cfg["TEMPERATURE"],
        additional_model_request_fields = {"reasoning_effort": aws_bedrock_cfg["REASONING_EFFORT"] if aws_bedrock_cfg["MODEL_TYPE"] == "reasoning" else None},
    )

elif inference_type == "groq":
    groq_cfg = llm_cfg["groq"]
    llm_model = ChatGroq(
        api_key = GROQ_API_KEY,
        model = groq_cfg["MODEL"],
        temperature = groq_cfg["TEMPERATURE"],
        reasoning_effort = groq_cfg["REASONING_EFFORT"] if groq_cfg["MODEL_TYPE"] == "reasoning" else None,
    )

elif inference_type == "nvidia":
    nvidia_cfg = llm_cfg["nvidia"]
    llm_model = ChatNVIDIA(
        api_key = NVIDIA_API_KEY,
        model = nvidia_cfg["MODEL"],
        temperature = nvidia_cfg["TEMPERATURE"],
    )

elif inference_type == "google":
    google_cfg = llm_cfg["google"]
    llm_model = ChatGoogleGenerativeAI(
        api_key = GOOGLE_API_KEY,
        model = google_cfg["MODEL"],
        temperature = google_cfg["TEMPERATURE"],
        max_retries = google_cfg["MAX_RETRIES"]
    )

elif inference_type == "huggingface":
    hf_cfg = llm_cfg["huggingface"]
    llm = HuggingFaceEndpoint(
        huggingfacehub_api_token = HUGGINGFACE_API_KEY,
        repo_id = hf_cfg["MODEL"],
        task = hf_cfg["MODEL_TYPE"],
        max_new_tokens = hf_cfg["MAX_TOKENS"],
        do_sample = False,
        repetition_penalty = 1.03,
        provider = hf_cfg["PROVIDER"],
        streaming = hf_cfg["STREAMING"],
    )
    llm_model = ChatHuggingFace(llm=llm)

elif inference_type == "llamacpp":
    llamacpp_cfg = llm_cfg["llamacpp"]
    llm_model = ChatLlamaCpp(
        model_path = llamacpp_cfg["MODEL"],
        temperature = llamacpp_cfg["TEMPERATURE"],
        n_ctx = llamacpp_cfg["N_CTX"],
        n_gpu_layers = llamacpp_cfg["N_GPU_LAYERS"],
        n_batch = llamacpp_cfg["N_BATCH"],
        max_tokens = llamacpp_cfg["MAX_TOKENS"],
        n_threads = multiprocessing.cpu_count() - 1,
        repeat_penalty = llamacpp_cfg["REPEAT_PENALTY"],
        top_p = llamacpp_cfg["TOP_P"],
        verbose = llamacpp_cfg["VERBOSE"],
    )
else:
    raise ValueError(f"Invalid inference type: {inference_type}")

    
