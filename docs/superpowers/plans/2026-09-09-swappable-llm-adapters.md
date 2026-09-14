# Gemini/Ollama LLM Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 LLMPort 뒤에서 NPC와 core의 provider를 설정으로 Ollama 또는 Gemini adapter로 선택하고, core를 검증된 Gemini 모델로 전환해 테스터2 preview를 제공한다.

**Architecture:** `LLMPort`와 하네스는 유지한다. 새 `GeminiLLM`이 Google SDK를 내부 형식으로 변환하고, 기존 `llm_factory.py` composition root가 provider별 adapter를 생성한다. 공식 문서와 현재 계정 model 목록으로 호환 모델을 선택한 뒤 core만 Gemini로 전환하며, adapter 동작과 의미 품질을 각각 검증한다.

**Tech Stack:** Python 3, Pydantic, `google-genai==1.29.0`, pytest, 기존 hexagonal `LLMPort`

**Spec:** `docs/superpowers/specs/2026-09-09-swappable-llm-adapters-design.md`

## Global Constraints

- 기존 `LLMPort.complete(messages, json_schema, *, temperature=None) -> dict` 계약을 바꾸지 않는다.
- adapter와 실제 corpus를 검증하기 전에는 `.env`와 실행 중 8500을 바꾸지 않는다. 검증 뒤 core만 Gemini로 바꾸고 NPC Exaone·embedding Gemini·DB 설정은 유지한다.
- 기존 `google-genai==1.29.0`만 사용하고 새 dependency를 추가하지 않는다.
- Gemini SDK 타입은 outbound adapter 밖으로 노출하지 않는다.
- JSON 파싱 실패와 응답 차단·text 부재만 기존 호출자가 감사할 수 있는 명시적 오류로 처리하고, adapter 자체 재시도 정책은 새로 만들지 않는다.
- 실제 Gemini 호출은 사용자 승인 범위다. key 값은 출력·문서·artifact에 저장하지 않는다.
- Git 저장소로 인식되지 않는 작업공간이므로 commit/worktree 단계는 실행하지 않는다.

---

### Task 1: Gemini LLM adapter와 factory 전환

**Files:**
- Create: `backend/apps/engine/adapter/outbound/llm/gemini_llm.py`
- Modify: `backend/apps/engine/dependencies/llm_factory.py`
- Modify: `backend/tests/engine/test_health_and_factories.py`
- Create: `backend/tests/pure/test_gemini_llm.py`

**Interfaces:**
- Consumes: `LLMPort.complete(messages: list[MessageDTO], json_schema: dict, *, temperature: float | None = None) -> dict`
- Produces: `GeminiLLM(api_key: str, model: str).complete(...) -> dict`; `build_llm(...)`의 `provider == "gemini"` 분기

- [ ] **Step 1: adapter 계약의 failing tests를 작성한다**

mock `genai.Client`로 아래 동작을 각각 검증한다.

```python
def test_gemini_complete_sends_messages_schema_and_temperature(monkeypatch):
    llm = GeminiLLM(api_key="test-key", model="gemini-test")
    result = llm.complete(
        [MessageDTO(role="system", content="규칙"), MessageDTO(role="user", content="질문")],
        {"type": "object", "properties": {"answer": {"type": "string"}}},
        temperature=0.0,
    )
    assert result == {"answer": "응답"}
    assert recorded_call["model"] == "gemini-test"
    assert recorded_call["temperature"] == 0.0

def test_gemini_complete_rejects_non_json_text(monkeypatch):
    with pytest.raises(LLMParseError):
        GeminiLLM(api_key="test-key", model="gemini-test").complete(messages, schema)
```

- [ ] **Step 2: adapter test가 올바른 이유로 실패하는지 확인한다**

Run:

```bash
cd backend
.venv/bin/python -m pytest tests/pure/test_gemini_llm.py -q --tb=short
```

Expected: `gemini_llm` module 또는 `GeminiLLM`이 없어 FAIL.

- [ ] **Step 3: SDK 경계를 최소 구현한다**

`GeminiLLM.complete()`은 port message를 SDK contents로 변환하고 `types.GenerateContentConfig`에 `temperature`, `response_mime_type="application/json"`, `response_json_schema=json_schema`를 전달한다. `response.text`를 `json.loads()`하고 `JSONDecodeError` 또는 text type 오류를 `LLMParseError`로 변환한다.

```python
config = types.GenerateContentConfig(
    temperature=0.7 if temperature is None else temperature,
    response_mime_type="application/json",
    response_json_schema=json_schema or None,
)
response = self._client.models.generate_content(
    model=self._model,
    contents=[{"role": m.role, "parts": [{"text": m.content}]} for m in messages],
    config=config,
)
```

- [ ] **Step 4: factory red test를 작성한다**

`test_llm_factory_switches`의 기존 Gemini `NotImplementedError` 기대를 `GeminiLLM` instance 기대와 전달된 model/API key 검증으로 바꾼다. fake·ollama·unknown provider 기대는 유지한다. NPC와 core getter가 서로 다른 provider/model 설정을 쓰는 기존 설정 seam도 mock으로 확인한다.

- [ ] **Step 5: factory에서 Gemini adapter를 주입한다**

`build_llm`은 Gemini 분기에서 `get_settings().gemini_api_key` 또는 명시적으로 전달받은 동일 설정값으로 `GeminiLLM`을 만든다. provider 분기 외 use case·harness·HTTP schema는 수정하지 않는다.

- [ ] **Step 6: focused green을 확인한다**

Run:

```bash
cd backend
.venv/bin/python -m pytest tests/pure/test_gemini_llm.py tests/engine/test_health_and_factories.py -q --tb=short
```

Expected: 새 adapter 계약과 기존 fake/ollama/fail-fast factory 회귀가 모두 PASS.

### Task 2: 설정 전환 문서와 전체 회귀

**Files:**
- Create: `backend/docs/llm-providers.md`
- Modify: `docs/HANDOFF.md`
- Modify: `docs/review-verification/2026-09-09-connected-implementation/test-execution-ledger.md`

**Interfaces:**
- Consumes: `NPC_LLM_PROVIDER`, `NPC_LLM_MODEL`, `CORE_LLM_PROVIDER`, `CORE_LLM_MODEL`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL`
- Produces: 비밀값 없는 설정 전환 예시와 구현·검증 경계 기록

- [ ] **Step 1: 비밀값 없는 설정 예시를 작성한다**

`backend/docs/llm-providers.md`에 역할별 독립 전환을 설명한다.

```dotenv
NPC_LLM_PROVIDER=ollama
NPC_LLM_MODEL=exaone3.5:7.8b
CORE_LLM_PROVIDER=gemini
CORE_LLM_MODEL=gemini-3-flash-preview
GEMINI_API_KEY=<set-locally>
```

실제 key·URL을 출력하지 않고, 설정 변경 뒤 cache가 남지 않은 새 프로세스로 기동해야 함을 명시한다. 실제 전환 결과에는 provider/model과 검증 수치만 기록한다.

- [ ] **Step 2: pure·architecture 검증을 실행한다**

Run:

```bash
cd backend
.venv/bin/python -m pytest tests/pure --confcutdir=tests/pure -q --tb=short
.venv/bin/lint-imports
rg -n "LangChain|langchain|LangGraph|langgraph|CrewAI|crewai" apps core
```

Expected: pure PASS, architecture 4 kept/0 broken, forbidden framework finding0.

- [ ] **Step 3: DB 전체 suite를 실행한다**

`pigfarm_test` 단독 소유와 DB guard를 확인한 뒤 실행한다.

```bash
cd backend
.venv/bin/python -m pytest -q --tb=short
```

Expected: exit0. 기존 최종 prompt checkpoint `307 passed, 3 dependency warnings`와 비교하되 수집 수가 바뀌면 새 결과를 그대로 기록한다.

- [ ] **Step 4: 문서에 실제 결과와 한계를 기록한다**

HANDOFF와 실행 장부에 adapter/factory/pure/full 결과를 실행별로 적는다. adapter green을 Gemini 의미 정확도나 RM1 해결로 표현하지 않는다.

### Task 3: 실제 Gemini core 검증과 테스터2 preview 전환

**Files:**
- Modify: `backend/.env` (비밀값은 읽거나 기록하지 않고 provider/model 키만 수정)
- Modify: `docs/HANDOFF.md`
- Modify: `docs/review-verification/2026-09-09-connected-implementation/test-execution-ledger.md`
- Modify: `docs/review-verification/2026-09-09-second-play/tester2.md`

**Interfaces:**
- Consumes: 설치된 `google-genai==1.29.0`, 현재 `GEMINI_API_KEY`, Google model metadata의 supported actions, 기존 12 questions + 10 controls + 3 custom + 3 ambient corpus
- Produces: 실제 structured probe를 통과한 `gemini-3-flash-preview`, 실제 adapter/corpus 결과, core만 Gemini인 테스터2용 8500

- [ ] **Step 1: 지원 모델 후보를 사실로 확인한다**

공식 Gemini API 모델 문서와 같은 API key의 `client.models.list()`를 대조한다. `generateContent`를 지원하고 현재 SDK에서 structured JSON schema 요청을 받을 수 있는 모델만 후보로 남긴다. key·전체 환경값은 출력하지 않고 exact model ID와 지원 근거만 기록한다.

- [ ] **Step 2: 실제 adapter structured-output probe를 실행한다**

선택한 후보에 system/user message와 작은 object schema, `temperature=0`을 보내 `GeminiLLM.complete()`가 dict를 반환하는지 확인한다. HTTP/provider 오류, 차단, JSON parsing 결과와 model ID를 기록하되 prompt에 운영 기록이나 비밀값을 넣지 않는다.

- [ ] **Step 3: 동일 corpus로 의미 gate를 실행한다**

기존 helper corpus의 원문12·통제10·custom3·ambient3, expected relation/source를 바꾸지 않고 core adapter만 Gemini로 실행한다. provider calls, accepted/rejected/error/fallback, source 인용과 PC1–PC8/SPC1–SPC2를 raw로 보존하고 독립 의미 검토를 받는다. Ollama 결과와 단순 성공률만 비교하지 않고 문항별 관계·근거를 확인한다.

- [ ] **Step 4: core 설정만 전환한다**

실제 probe를 통과하고 사용자가 선택한 `gemini-3-flash-preview`로 `CORE_LLM_PROVIDER=gemini`, `CORE_LLM_MODEL=gemini-3-flash-preview`를 설정한다. `NPC_LLM_PROVIDER=ollama`, `NPC_LLM_MODEL=exaone3.5:7.8b`, `EMBEDDING_PROVIDER=gemini`, DB URL과 scenario/harness 설정이 기존 값과 같음을 값 노출 없이 preflight한다.

- [ ] **Step 5: 테스터2용 8500을 재기동하고 읽기 전용 smoke를 한다**

기존 PID의 owner/cwd/cmdline과 preflight 설정을 확인한 뒤 같은 uvicorn 명령으로 재기동한다. 판 생성 없이 `/health`, `/openapi.json`, frontend `/play`를 확인한다. health의 core가 `gemini:<검증된 exact model ID>`, NPC가 `ollama:exaone3.5:7.8b`, embedding이 `gemini`, DB가 `ok`이고 observations/night previous/rule preview 세 경로가 있어야 한다.

- [ ] **Step 6: 결과와 수동 테스트 경계를 마감한다**

HANDOFF와 실행 장부에 exact model ID, 실제 호출·corpus 의미 결과, runtime health를 기록한다. Gemini가 RM1을 통과하지 못하면 그 결함을 그대로 남긴 상태로 테스터2 preview임을 밝힌다. 자동 smoke는 사람 표본으로 세지 않고, 테스터2가 새 게임을 5회차까지 완료한 뒤 attempt_id를 읽기 전용으로 대조한다.
