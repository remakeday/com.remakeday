"""설명 규칙 대사가 장면이 보여 주지 않는 사실을 담게 하는 결정적 가드 (테스터9 F14 추가 사례 2).

`알고 있는 관찰을 설명한다`의 대사는 모델이 아니라 시나리오가 쓴 explanation 문장이다. 그 문장이 장면 서술을
말로 되풀이하기만 하면 밤 선택 1회의 대가에 비해 얻는 정보가 없다. 행동에 explanation_knowledge(행위자 knowledge id)를
걸어 두면, 설명이 그 지식의 낱말을 장면 밖에서 둘 미만으로만 담을 때 지식 문장을 그대로 뒤에 붙인다 — 지어내지 않는다.
"""

import re

_PARTICLE_RE = re.compile(r"(에서|에게|으로|이다|까지|부터|은|는|이|가|을|를|에|의|도|로|와|과|만)$")
_STRIP_RE = re.compile(r"[^\w]+")
# "숫자" 한 낱말은 손목띠를 보는 장면 자체가 이미 말해 준다 — 낱말 하나로는 지식을 옮겼다고 보지 않는다.
MIN_SHARED_TOKENS = 2


def _content_tokens(text):
    tokens = (_PARTICLE_RE.sub("", _STRIP_RE.sub("", word)) for word in text.split())
    return {token for token in tokens if len(token) >= 2}


def explanation_line(bundle, opportunity):
    """설명 대사 = 시나리오 explanation(없으면 서술) + 장면에 없는 낱말을 충분히 담지 못한 연결 지식 문장."""
    line = opportunity.explanation or opportunity.narration
    if not opportunity.explanation_knowledge:
        return line
    character = next(c for c in bundle.characters if c.name == opportunity.actor)
    scene_tokens = _content_tokens(f"{opportunity.narration} {opportunity.action}")
    for entry in (k for k in character.knowledge if k.id in opportunity.explanation_knowledge):
        novel = _content_tokens(entry.text) - scene_tokens
        if len(novel & _content_tokens(line)) < MIN_SHARED_TOKENS:
            line = f"{line} {entry.text}"
    return line
