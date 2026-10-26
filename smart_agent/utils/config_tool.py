"""YAML configuration loaders."""

from pathlib import Path

import yaml
from dotenv import load_dotenv

from smart_agent.utils.path_tool import get_abs_path, get_proj_root


#在模型工厂读取环境变量之前，先加载本地开发密钥。已有的环境变量不会被覆盖。
"""
load_dotenv() 做的事情是：读取 .env 文件，然后把里面的键值对注入到当前 Python 进程的 os.environ 字典中。
生命周期：程序一结束，这些注入的变量就消失了，不会写回系统注册表或配置文件
如果系统里已经存在同名变量，load_dotenv() 默认不会覆盖它（override=False）
"""
load_dotenv(Path(get_proj_root()) / ".env")


def _load_yaml(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Configuration must be a mapping: {path}")
    return data


def load_rag_config(config_path: str | None = None) -> dict:
    return _load_yaml(config_path or get_abs_path("config/rag_config.yaml"))


def load_chroma_config(config_path: str | None = None) -> dict:
    return _load_yaml(config_path or get_abs_path("config/chroma_config.yaml"))


def load_prompt_config(config_path: str | None = None) -> dict:
    return _load_yaml(config_path or get_abs_path("config/prompt_config.yaml"))


def load_agent_config(config_path: str | None = None) -> dict:
    return _load_yaml(config_path or get_abs_path("config/agent_config.yaml"))

#返回YAML文件对象
rag_config = load_rag_config()
chroma_config = load_chroma_config()
prompt_config = load_prompt_config()
agent_config = load_agent_config()

