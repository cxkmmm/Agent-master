# SmartHome After-Sales Agent

一个轻量级的智能家居售后助手示例：用 **FastAPI + LangGraph + Chroma** 把知识库检索、工具调用、会话记忆和流式输出串起来。项目同时被改造成一个便于测试的工程样本，适合用来演示 RAG/Agent 的测试设计。

> 说明：本项目的业务资料和演示数据均为自建合成内容，不代表任何真实品牌或真实售后政策。项目在公开的 LangGraph/RAG 架构实践基础上，围绕智能家居售后场景完成了包结构、配置、提示词和可测试性重构。

## 功能

- 智能家居知识库问答：扫地机器人、空气净化器、智能门锁
- 工具调用：用户、城市、月份、使用记录、天气演示数据
- LangGraph + SQLite checkpoint 的多轮会话
- FastAPI 流式聊天接口和简单网页
- 文件 MD5 去重的增量知识库入库
- 可注入的 Agent 和 HTTP 层测试

## 目录

```text
smart_agent/          # 业务代码（agent / rag / model / utils）
config/               # YAML 配置
prompts/              # 系统提示词、RAG 提示词、报告提示词
data/knowledge/       # 自建知识库文档
data/external/        # 合成使用记录
web/                  # 原生 HTML/CSS/JS 聊天页
scripts/              # 知识库重建脚本
tests/                # pytest和黑盒测试
storage/              # Chroma 和入库状态（运行时生成）
```

## 快速启动

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

在 `.env` 中填写：

```text
DEEPSEEK_API_KEY=...
DASHSCOPE_API_KEY=...
```

重建知识库：

```powershell
python -m scripts.rebuild_knowledge --yes
```

启动服务：

```powershell
python app.py
```

打开 <http://127.0.0.1:8000>，接口文档在 <http://127.0.0.1:8000/docs>。

## 配置

- `config/agent_config.yaml`：演示用户、城市、月份和外部数据路径
- `config/rag_config.yaml`：聊天模型和 embedding 模型
- `config/chroma_config.yaml`：向量库路径、集合名、分片参数
- `config/prompt_config.yaml`：提示词文件路径

演示工具使用固定值，目的是让同一份使用报告可复现，方便测试断言。接入生产环境时，应替换为真实的用户、订单和天气服务。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/chat` | `{"message": "...", "session_id": "..."}`，返回 `text/plain` 流 |
| `GET` | `/docs` | FastAPI 自动生成的接口文档 |

## 测试

```powershell
pytest
```

当前包含 14 个离线测试，覆盖：

- API 健康检查、流式响应、空白输入、超长输入、session_id 边界
- 工具函数的确定性、JSON 序列化和缺失记录处理
- 文件 MD5、目录过滤和路径穿越防护

后续可以补充：

- 用临时 Chroma 测试重复入库和检索 top-k
- 用 Fake Model 测试报告流程的工具调用顺序
- 用 pytest marker 区分离线测试和真实模型 smoke test

## 已知限制

- SQLite checkpointer 适合单机演示，多 worker 部署应换成 Postgres/Redis 等共享存储。
- `get_weather` 返回演示数据，不是实时天气。
- 目前没有登录、权限隔离、限流和审计日志，不能直接作为生产客服系统使用。
- Chroma 和会话数据库在 `.gitignore` 中，不随仓库提交。

## 开发命令

```powershell
# 只跑测试
pytest

# 重建知识库
python -m scripts.rebuild_knowledge --yes

# Docker
docker compose up --build
```
