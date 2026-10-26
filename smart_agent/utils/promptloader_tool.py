"""提示词文件加载器。"""

from pathlib import Path

from smart_agent.utils.config_tool import prompt_config
from smart_agent.utils.log_tool import logger
from smart_agent.utils.path_tool import get_abs_path

#传入一个YAML文件对象的键（key）
def _read_prompt(config_key: str) -> str:
    try:
        prompt_path = Path(get_abs_path(prompt_config[config_key]))
    except KeyError as exc:
        logger.error("提示词配置的键（key）缺失: %s", config_key)
        raise

    try:
        #Path.read_text() 就是 pathlib提供的实例方法,和内置函数read_text一样
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("提示词文件（Prompt file）没有找到: %s", prompt_path)
        raise


def load_sys_prompt() -> str:
    return _read_prompt("main_prompt_path")


def load_rag_prompt() -> str:
    return _read_prompt("rag_summarize_prompt_path")


def load_report_prompt() -> str:
    return _read_prompt("report_prompt_path")
    
