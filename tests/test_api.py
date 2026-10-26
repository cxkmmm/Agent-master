from types import SimpleNamespace
from fastapi.testclient import TestClient
from app import create_app


class FakeWork:
    def stream(self, state, config, stream_mode):
        yield SimpleNamespace(content="这是一个测试回答。"), {}


class FakeAgent:
    def __init__(self):
        self.work = FakeWork()


def make_client() -> TestClient:
    return TestClient(create_app(agent=FakeAgent()))

#响应码400 Bad Request：请求本身有语法错误或格式不对，服务器根本解析不了
#响应码422 Unprocessable Entity：格式没问题，服务器能解析，但里面的数据不符合规则。

def test_health():
    response = make_client().get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_streamed_text():
    response = make_client().post(
        "/api/chat",
        json={"message": "滤网多久更换？", "session_id": "test-session"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "测试回答" in response.text

def test_empty_message_is_rejected_by_schema():
    response = make_client().post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_whitespace_message_is_rejected():
    response = make_client().post("/api/chat", json={"message": "   "})
    assert response.status_code == 400


def test_oversized_message_is_rejected():
    response = make_client().post("/api/chat", json={"message": "x" * 4001})
    assert response.status_code == 422


def test_oversized_session_id_is_rejected():
    response = make_client().post(
        "/api/chat",
        json={"message": "你好", "session_id": "s" * 101},
    )
    assert response.status_code == 422
