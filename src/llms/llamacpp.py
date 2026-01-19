import multiprocessing
from langchain_community.chat_models import ChatLlamaCpp
from .base import BaseLLMProvider

class LlamaCppProvider(BaseLLMProvider):
    def create_model(self, config: dict, **kwargs):
        return ChatLlamaCpp(
            model_path=config["MODEL"],
            temperature=config["TEMPERATURE"],
            n_ctx=config["N_CTX"],
            n_gpu_layers=config["N_GPU_LAYERS"],
            n_batch=config["N_BATCH"],
            max_tokens=config["MAX_TOKENS"],
            n_threads=multiprocessing.cpu_count() - 1,
            repeat_penalty=config["REPEAT_PENALTY"],
            top_p=config["TOP_P"],
            verbose=config["VERBOSE"],
        )
