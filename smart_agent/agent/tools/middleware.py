
from typing import Callable

from langchain.agents.middleware import (
    AgentState,
    ModelRequest,
    before_model,
    dynamic_prompt,
    wrap_tool_call,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command

from smart_agent.utils.log_tool import logger
from smart_agent.utils.promptloader_tool import load_report_prompt, load_sys_prompt

@wrap_tool_call
def monitor_model(
    request: ToolCallRequest, #request：本次工具调用的请求信息
    handler: Callable[[ToolCallRequest], ToolMessage | Command],  #真正的工具执行函数，由框架提供
) -> ToolMessage | Command:
    logger.info(f"[tool monitor]执行工具: {request.tool_call['name']}")
    logger.info(f"[tool monitor]传入参数: {request.tool_call['args']}")

    try:
        result = handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")
        if request.tool_call["name"] == "fill_context_for_report":
            request.runtime.context["report"] = True
        return result
    except Exception:
        logger.exception("工具%s调用失败", request.tool_call["name"])
        raise

@before_model
def log_before_model(
    state: AgentState,
    runtime: Runtime,
):
    logger.info("模型调用前，消息数=%s", len(state["messages"]))
    logger.debug("最后一条消息=%s", state["messages"][-1].content.strip())

#切换提示词
@dynamic_prompt
def report_prompt_switch(
    request: ModelRequest,
):
    is_report = request.runtime.context.get("report", False)
    if is_report:
        return load_report_prompt()
    return load_sys_prompt()
    
