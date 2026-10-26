"""面向售后服务助手的 LangGraph 编排。"""

import sqlite3
from pathlib import Path
from typing import Annotated, TypedDict

from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph, add_messages

from smart_agent.agent.tools.agent_tools import (
    fetch_external_data,
    fill_context_for_report,
    get_cur_month,
    get_location,
    get_user_id,
    get_weather,
    rag_summarize,
)
from smart_agent.agent.tools.middleware import (
    log_before_model,
    monitor_model,
    report_prompt_switch,
)
from smart_agent.model.factory import chat_model
from smart_agent.utils.promptloader_tool import load_sys_prompt


class State(TypedDict):
    input: str
    messages: Annotated[list, add_messages]


class ReactAgent:
    """围绕工具调用智能体和 SQLite 检查点器的一层小型封装。

    agent 和 checkpointer_path 都是可注入的，因此测试可以用一个确定性的假实现替换基于模型的智能体，并使用临时数据库。
    """

    def __init__(
        self,
        agent=None,
        checkpointer_path: str | Path = r"storage\checkpoints.sqlite",
        tools: list | None = None,
        system_prompt: str | None = None,
    ):
        self.agent = agent or create_agent(
            model=chat_model,
            tools=tools
            or [
                rag_summarize,
                get_weather,
                get_location,
                get_user_id,
                get_cur_month,
                fetch_external_data,
                fill_context_for_report,
            ],
            system_prompt=system_prompt or load_sys_prompt(),
            middleware=[monitor_model, log_before_model, report_prompt_switch],
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以下是用户历史对话，仅用于理解上下文：\n{history}"),
                ("user", "{input}"),
            ]
        )

        self.workflow = StateGraph(State)
        self.workflow.add_node("exec_stream", self.exec_stream)
        self.workflow.add_edge(START, "exec_stream")
        self.workflow.add_edge("exec_stream", END)

        db_path = Path(checkpointer_path).expanduser().resolve() #把 checkpointer_path（字符串路径）转成一个规范化的绝对路径对象：
        db_path.parent.mkdir(parents=True, exist_ok=True)  #递归创建所有缺失的上级目录
        memory = SqliteSaver(
            sqlite3.connect(str(db_path), check_same_thread=False)
        )
        self.work = self.workflow.compile(checkpointer=memory)

    def exec_stream(self, state: State):
        prompt_value = self.prompt_template.invoke(
            {
                "input": state["input"],
                "history": state["messages"],
            }
        )
        response = self.agent.invoke(prompt_value, context={"report": False})
        last_message = response["messages"][-1]
        return {"messages": [state["input"], last_message]}

if __name__ == "__main__":
    path = r"storage\checkpoints.sqlite"
    print(Path(path).expanduser().resolve())