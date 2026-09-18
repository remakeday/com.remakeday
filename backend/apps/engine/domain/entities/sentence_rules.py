"""답변 문장 분할 — 대사창 한 줄씩 넘기기용 순수 함수 (낮 화면 VN 설계 §3)."""

_TERMINATORS = ".?!…"
_QUOTE_PAIRS = {'"': '"', "“": "”"}  # 여는 따옴표 → 닫는 따옴표


def split_sentences(text: str) -> list[str]:
    """마침표·물음표·느낌표·줄임표(연속 포함) 뒤가 공백이나 끝이면 나눈다. 따옴표 안은 나누지 않는다.
    짝이 없는 따옴표는 여는 것으로 치지 않는다 — 모델 답변의 홀따옴표가 나머지를 한 줄로 뭉치지 않게."""
    sentences, start, closing, i = [], 0, None, 0
    while i < len(text):
        ch = text[i]
        if closing is None and ch in _QUOTE_PAIRS and _QUOTE_PAIRS[ch] in text[i + 1:]:
            closing = _QUOTE_PAIRS[ch]
        elif ch == closing:
            closing = None
        elif closing is None and ch in _TERMINATORS:
            while i + 1 < len(text) and text[i + 1] in _TERMINATORS:
                i += 1
            if i + 1 == len(text) or text[i + 1].isspace():
                sentences.append(text[start:i + 1])
                start = i + 1
        i += 1
    sentences.append(text[start:])
    return [s.strip() for s in sentences if s.strip()]
