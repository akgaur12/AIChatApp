import os, logging
from dotenv import load_dotenv
from src.utils import load_config
from src.llms import LLMFactory

load_dotenv()
cfg = load_config()
logger = logging.getLogger(__name__)

def get_llm_model():
    llm_cfg = cfg.get("LLM", {})
    inference_type = llm_cfg.get("Provider", "").lower()

    if not inference_type:
        raise ValueError("LLM Provider not specified in configuration.")

    # Use Factory to get the appropriate provider
    provider = LLMFactory.get_provider(inference_type)
    
    # Collect necessary credentials/kwargs
    kwargs = {
        "aws_key": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "api_key": os.getenv(f"{inference_type.upper()}_API_KEY") 
                   or os.getenv("HUGGINGFACEHUB_API_TOKEN") 
                   or os.getenv("NVIDIA_API_KEY")
                   or os.getenv("GOOGLE_API_KEY")
                   or os.getenv("GROQ_API_KEY")
    }

    return provider.create_model(llm_cfg.get(inference_type, {}), **kwargs)

# Maintain compatibility or provide a singleton if needed
llm_model = get_llm_model()
