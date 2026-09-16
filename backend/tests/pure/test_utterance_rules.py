import pytest
from apps.engine.domain.entities.utterance_rules import is_nonsense


@pytest.mark.parametrize("text", ["ㅋㅋㅋㅋ", "......", "……", "왜왜왜왜왜", "ㅠㅠ", "   ", "!!!!", "ㅇㅇㅇ", "아아아아"])
def test_nonsense_inputs_are_gated(text):
    assert is_nonsense(text)


@pytest.mark.parametrize("text", ["왜?", "응", "왜 안어", "밥 남겼어?", "채연아", "ㅋㅋ 왜 안 먹어", "왜왜 그래"])
def test_valid_inputs_pass(text):
    assert not is_nonsense(text)
