import json
import pytest

from agents.chatbot_agent import ChatbotAgent


class FakeLLM:
    """Deterministic stand-in for ChatOpenAI."""

    def __init__(self, response_text: str = "Stub answer from LLM."):
        self.response_text = response_text
        self.invocations = []

    def invoke(self, messages):
        self.invocations.append(messages)

        class _Response:
            def __init__(self, content):
                self.content = content

        return _Response(self.response_text)


@pytest.fixture()
def temp_data_dir(tmp_path):
    """Writes minimal JSON files mimicking the production schema."""
    variable = {
        "crop": {"name": "Wheat", "season": "Rabi"},
        "location": {"city": "Pune", "state": "Maharashtra"},
        "day_of_cycle": 5,
        "soil": {"usda_texture_class": "Loam"},
        "climate": {
            "temperature_2m": 28,
            "relative_humidity_2m": 60,
            "precipitation": 2,
        },
    }
    calendar = {
        "days": [
            {"day": 5, "stage": "Vegetative", "tasks": ["Irrigation"]},
            {"day": 6, "stage": "Vegetative", "tasks": ["Weeding"]},
        ]
    }
    persistent = {
        "Wheat": {
            "Maharashtra": {
                "cycle_duration_days": 120,
                "stages": [{"name": "Vegetative"}],
                "source": "ICAR",
            }
        }
    }

    for filename, payload in (
        ("variable.json", variable),
        ("calendar.json", calendar),
        ("persistent.json", persistent),
    ):
        path = tmp_path / filename
        path.write_text(json.dumps(payload), encoding="utf-8")

    return tmp_path


@pytest.fixture()
def fake_llm(monkeypatch):
    instance = FakeLLM()
    monkeypatch.setattr(
        "agents.chatbot_agent.ChatOpenAI",
        lambda *args, **kwargs: instance,
    )
    return instance


def test_chat_returns_response_with_context(temp_data_dir, fake_llm):
    agent = ChatbotAgent(api_key="dummy", data_dir=str(temp_data_dir))

    result = agent.chat("Give me today's status")

    assert result["response"] == fake_llm.response_text
    assert result["context"]["crop"] == "Wheat"
    assert result["sources"] == ["General farming knowledge"]
    assert len(fake_llm.invocations) == 1


def test_chat_triggers_market_price_lookup(temp_data_dir, fake_llm, monkeypatch):
    calls = {}

    def _fake_price_prediction(crop, state, season, month):
        calls["args"] = (crop, state, season, month)
        return {
            "average_price": 2000.0,
            "price_range": {"min": 1800.0, "max": 2200.0},
            "trend": "steady",
            "confidence": "high",
        }

    monkeypatch.setattr(
        "agents.chatbot_agent.get_price_prediction",
        _fake_price_prediction,
    )

    agent = ChatbotAgent(api_key="dummy", data_dir=str(temp_data_dir))
    agent.chat("What is the market price today?")

    assert calls["args"] == ("Wheat", "Maharashtra", "Rabi", "March")


def test_conversation_history_capped(temp_data_dir, fake_llm):
    agent = ChatbotAgent(api_key="dummy", data_dir=str(temp_data_dir))

    for idx in range(12):
        agent.chat(f"Question number {idx}")

    assert len(agent.conversation_history) == 20
