"""
暴露给售后智能体的工具。
演示工具刻意从 config/agent_config.yaml 中读取确定性的值。这使得本地演示可复现，并让工具层易于在没有真实用户或天气服务的情况下进行测试。
"""

import csv
import json
import os
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from smart_agent.rag.rag_service import RAGService
from smart_agent.utils.config_tool import agent_config
from smart_agent.utils.log_tool import logger
from smart_agent.utils.path_tool import get_abs_path


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """延迟创建向量存储服务，以保持导入轻量。"""
    """全局单例：多个地方调用 get_rag_service() 拿到的是同一个对象，避免重复初始化、浪费内存"""
    return RAGService()


@tool(description="从智能家居售后知识库中检索产品手册、保修政策和故障排查资料")
def rag_summarize(query: str) -> str:
    """检索相关段落并返回有依据的摘要。"""

    return get_rag_service().rag_summarize(query)


@tool(description="获取演示环境中的天气信息；生产环境应替换为真实天气 API")
def get_weather(city: str) -> str:
    weather = agent_config.get("demo_weather",
                               "晴，22℃，湿度 45%" #默认值
                               )    #从字典里取一个值，取不到就用默认值。
    return f"{city}：{weather}（演示数据）"


@tool(description="获取当前演示用户所在城市")
def get_location() -> str:
    return os.getenv("DEMO_CITY") or str(agent_config.get("demo_city", "北京"))


@tool(description="获取当前演示用户的 ID")
def get_user_id() -> str:
    #“优先用环境变量，没有就用配置，再没有就用默认值”
    return os.getenv("DEMO_USER_ID") or str(agent_config.get("demo_user_id", "1002"))


@tool(description="获取当前演示月份，格式为 YYYY-MM")
def get_cur_month() -> str:
    return os.getenv("DEMO_MONTH") or str(agent_config.get("demo_month", "2025-01"))


_external_data: dict[str, dict[str, dict[str, str]]] = {}
#加载所有用户的使用，加载到_external_data中
def _load_external_data() -> dict[str, dict[str, dict[str, str]]]:
    """一次性加载合成用量记录，以用户和月份为键。"""

    if _external_data:
        return _external_data

    data_path = Path(get_abs_path(agent_config["external_data_path"]))
    if not data_path.exists():
        raise FileNotFoundError(f"External data file not found: {data_path}")
    ##Path.open() 是 pathlib 提供的实例方法,和内置函数open一样
    with data_path.open("r", encoding="utf-8", newline="") as handle: #csv.DictReader 会把第一行当作表头。
        for row in csv.DictReader(handle): #就是一行一行处理。
            user_id = (row.get("user_id") or "").strip()
            month = (row.get("month") or "").strip()
            if not user_id or not month:
                continue

            if user_id not in _external_data:
                _external_data[user_id] = {}
            _external_data[user_id][month] = {
                "profile": row["profile"].strip(),
                "efficiency": row["efficiency"].strip(),
                "consumables": row["consumables"].strip(),
                "benchmark": row["benchmark"].strip(),
                "product_model": row["product_model"].strip(),
            }
    return _external_data


@tool(description="查询指定用户在指定月份的设备使用记录，未找到时返回空字符串")
def fetch_external_data(user_id: str, cur_month: str) -> str:
    records = _load_external_data()
    record = records.get(user_id, {}).get(cur_month)
    if record is None:
        logger.warning("No usage record for user=%s month=%s", user_id, cur_month)
        return ""
    r"""
    json.dumps(...)：把 Python 对象（dict/list 等）转成 JSON 格式的字符串（s = string）
    ensure_ascii=False 的作用是：保留中文等非 ASCII 字符原样输出，不转成 \uXXXX 转义序列
    """
    return json.dumps(record, ensure_ascii=False)


@tool(description="标记当前会话为报告生成场景，供动态提示词切换使用")
def fill_context_for_report() -> str:
    return "report_context_enabled"

print(get_user_id.invoke({}))
