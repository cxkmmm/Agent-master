"""Model factories driven by environment variables and YAML defaults."""

import os
from abc import ABC, abstractmethod
from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from smart_agent.utils.config_tool import rag_config


def _dashscope_api_key() -> str | None:
    # Keep the old variable name as a fallback for existing local setups.
    return os.getenv("DASHSCOPE_API_KEY") or os.getenv("aliQwenapi")


deepseek_model = init_chat_model(
    model=os.getenv("CHAT_MODEL") or rag_config.get("chat_model", "deepseek-chat"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    temperature=float(os.getenv("CHAT_TEMPERATURE", "0.1")),
)


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[BaseChatModel]:
        return deepseek_model


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings]:
        model = os.getenv("EMBEDDING_MODEL") or rag_config.get(
            "embedding_model", "text-embedding-v4"
        )
        return DashScopeEmbeddings(
            model=model,
            dashscope_api_key=_dashscope_api_key(),
        )


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
