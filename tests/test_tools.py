import json

from smart_agent.agent.tools.agent_tools import (
    fetch_external_data,
    get_cur_month,
    get_location,
    get_user_id,
    get_weather,
)


def test_demo_profile_is_deterministic():
    assert get_user_id.invoke({}) == "1001"
    assert get_location.invoke({}) == "北京"
    assert get_cur_month.invoke({}) == "2025-01"


def test_weather_is_labeled_as_demo_data():
    result = get_weather.invoke({"city": "上海"})
    assert result.startswith("上海：")
    assert "演示数据" in result


def test_usage_record_is_json_serializable():
    result = fetch_external_data.invoke({"user_id": "1001", "cur_month": "2025-01"})
    payload = json.loads(result)
    assert payload["product_model"] == "H1"
    assert payload["profile"]


def test_missing_usage_record_returns_empty_string():
    result = fetch_external_data.invoke({"user_id": "9999", "cur_month": "2025-01"})
    assert result == ""
