from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.app.use_cases.utterance_classifier import classify


def test_classifier_returns_label():
    label, report = classify(FakeLLM([{"label": "chat"}]), "오늘 날씨 어때")
    assert label == "chat"
    assert report.role == "classifier"


def test_classifier_fallback_is_none():
    label, report = classify(FakeLLM([]), "왜 안어")
    assert label is None
    assert report.fallback_used
