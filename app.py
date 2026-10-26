"""智能家居售后服务助手的 FastAPI 入口点。

本地运行方式：：

python app.py

应用工厂将基于模型的智能体排除在导入时之外，这也使得 HTTP 层可以借助一个假的智能体轻松进行测试。
"""

import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from smart_agent.utils.log_tool import logger

#获取当前文件的路径对象,转成绝对路径并解析符号链接/../ 等,取父目录
BASE_DIR = Path(__file__).resolve().parent  #获取根目录
WEB_DIR = BASE_DIR / "web"  #获取web目录的绝对路径

"""
Pydantic 请求校验
定义一个类 ChatRequest，继承自 BaseModel（Pydantic 的基类）。
继承 BaseModel 后，这个类就自动具备了数据校验和类型转换的能力
"""
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="web_user_001", max_length=100)


def create_app(agent: Any = None) -> FastAPI: #agent默认为空
    """创建 FastAPI 应用。

    agent 是可选参数，测试时用于注入一个确定性的假智能体。
    """

    """
    @asynccontextmanager ：把带 yield 的 async 函数变成异步上下文管理器，
    FastAPI 拿到这个对象后，会在启动时执行 yield 之前的部分，关闭时执行 yield 之后的部分
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.agent is None:
            from smart_agent.agent.react_agent import ReactAgent
            app.state.agent = ReactAgent()
        yield

    app = FastAPI(
        title="智能家居售后助手",    #应用标题，显示在自动生成的 Swagger 文档（/docs）顶部
        description="知识库问答、设备使用报告与售后工具调用示例", #应用描述，显示在文档里，支持 Markdown
        lifespan=lifespan, #注意，uvicorn 启动后，FastAPI 才调用 lifespan(app)
    )
    #app.state 是 FastAPI 自带的储物柜
    app.state.agent = agent
    #线程锁，用来保证同一时刻只有一个线程能进入某段代码
    app.state.agent_lock = threading.Lock()

    @app.get("/", include_in_schema=False)  #设为 False：这个接口不会出现在 API 文档中
    def home():
        return FileResponse(WEB_DIR / "index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/chat")         #发送信息
    def chat(request: ChatRequest):
        """
        Pydantic 只校验长度，" "（纯空格）能通过，所以再 strip 一下手动挡回去。
        """
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="问题不能为空")

        session_config = {
            "configurable": {
                "thread_id": request.session_id,
            }
        }

        def stream_answer():  ## 这是一个生成器
            try:
                #加锁后：同一时刻只有一个请求能进入 with 块，其他请求排队等待 → 串行化，安全。
                #with 写法,自动 release(释放锁)
                with app.state.agent_lock:
                    for event in app.state.agent.work.stream(   #LangGraph 的流式 API，逐条消息产出
                        {"input": message},
                        session_config,
                        stream_mode="messages",
                    ):
                        chunk, _metadata = event  #每个事件是 (消息块, 元数据) 二元组
                        content = getattr(chunk, "content", "")  #安全取 content 属性，没有就返回空串
                        if content:
                            yield content  ## ← 每产出一段就发一段
            except Exception:
                logger.exception("聊天接口执行失败")
                yield "\n\n抱歉，服务暂时出错了，请稍后再试。"

        return StreamingResponse(
            stream_answer(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache", #别缓存
                "X-Accel-Buffering": "no",  #告诉 Nginx 等反向代理别缓冲，否则流式会变成一次性
            },
        )

    #mount = "把一整个子应用/目录挂到某个 URL 前缀下"，StaticFiles = "帮你自动服务一个目录的组件"。
    #所以加上 mount 后，静态文件不需要再写，但 /api/chat、/api/health 这些动态接口仍然要写。
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    return app


#app = create_app()
app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
