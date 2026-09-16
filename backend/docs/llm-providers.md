# LLM provider 전환

NPC와 core는 같은 `LLMPort.complete()` 계약을 사용하며 각각의 provider/model 설정으로 독립적으로 선택한다. 기존 composition root인 `apps/engine/dependencies/llm_factory.py`가 `FakeLLM`, `OllamaLLM`, `GeminiLLM`을 연결한다. 다른 모델을 선택해도 게임 use case나 하네스를 바꿀 필요가 없다.

## Core를 Gemini로 선택

기존 로컬 `backend/.env`에서 아래 설정을 사용한다. API 키는 기존 `GEMINI_API_KEY` 값을 유지하고 문서·로그·공유 파일에 복사하지 않는다.

```dotenv
NPC_LLM_PROVIDER=ollama
NPC_LLM_MODEL=kanana1.5:8b-q4km
CORE_LLM_PROVIDER=gemini
CORE_LLM_MODEL=gemini-3-flash-preview
GEMINI_REQUESTS_PER_MINUTE=10
EMBEDDING_PROVIDER=gemini
```

Tester2의 선택·연결 검증이 완료된 기본 core 모델은 `gemini-3-flash-preview`다. 다른 Gemini 모델을 시험하려면 `CORE_LLM_MODEL`을 해당 계정에서 생성 API로 검증한 모델 ID로 바꾼다.

Gemini completion에도 기존 `GEMINI_API_KEY`가 필요하다. 키가 비어 있으면 adapter 생성 시 명시적인 설정 오류가 발생한다. Core 설정은 planner, advisor, manager, evaluator 등 기존 core 역할 전체에 적용된다. NPC와 embedding 설정은 독립적이다.

설정과 adapter 인스턴스는 프로세스에서 캐시되므로 변경 후 새 backend 프로세스로 재시작해야 한다. `/health`의 `models.core`가 `gemini:<선택한 모델 ID>`인지 확인한다. 이 표시는 선택된 설정을 나타내며 외부 생성 API의 접근 권한·할당량·의미 정확성을 검증하지는 않는다. 실제 연결과 질문 품질은 별도로 확인한다.

## 다른 로컬 모델로 선택

Ollama에 이미 준비한 모델 ID를 그대로 지정한다. 어댑터는 모델을 설치하거나 이름을 고치지 않는다.

```dotenv
CORE_LLM_PROVIDER=ollama
CORE_LLM_MODEL=<설치한-Ollama-모델-ID>
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

NPC도 같은 방식으로 `NPC_LLM_PROVIDER`와 `NPC_LLM_MODEL`을 바꿀 수 있다. Gemini가 실패했을 때 Ollama로 자동 전환하지 않는다.

## 어댑터 계약과 검증 범위

- 설치된 `google-genai==1.29.0`의 `models.generate_content()`를 사용한다. SDK 타입은 outbound adapter 내부에 둔다.
- System 메시지는 `system_instruction`, user/assistant 메시지는 Gemini의 user/model 역할로 전달한다. System 메시지만 있는 요청에는 같은 지시를 실행하는 짧은 user 메시지를 추가한다.
- `response_mime_type="application/json"`과 원래 `response_json_schema`를 전달한다. SDK와 모델이 모든 제약을 강제한다고 가정하지 않으며 기존 하네스가 최종 스키마와 사실 범위를 검사한다.
- 명시적 temperature 값은 그대로 전달한다. 지정하지 않으면 기존 Ollama adapter와 같은 0.7을 사용한다. 현재 advisor의 0도 유지한다.
- 정상 JSON object만 dict로 반환한다. 빈 응답·잘못된 JSON·object가 아닌 JSON은 `LLMParseError`로, 차단/비정상 종료는 이유를 포함한 실패로 전달한다. SDK 오류는 원래대로 전파한다.
- 어댑터는 한 번만 요청한다. 재생성과 호출 감사는 기존 하네스가 담당하며, 실제 선택한 model ID가 감사 기록에 남는다.

Mock SDK 테스트는 배선·역할·스키마·temperature·오류 계약을 검증한다. Adapter 테스트 통과가 기존 RM1 의미 오류 해결을 뜻하지는 않는다. 실제 모델을 바꾸면 같은 질문 corpus와 원본 근거로 다시 평가해야 한다.


## 요청 할당량

`GEMINI_REQUESTS_PER_MINUTE`는 양수이며 기본값은10이다. 같은 backend 프로세스의 모든 Gemini completion adapter가 하나의 thread-safe admission gate를 공유하므로 기본 설정에서는 요청을 최소6초 간격으로 허용한다. 새 adapter 생성, 병렬 night 평가, 하네스 재시도도 같은 간격을 사용한다. 실패한 요청도 슬롯을 소비하며 이 대기는 기존 하네스의 호출 경과 시간에 포함된다. SDK 내부 재시도를 추가하지 않는다.

이 제한은 현재 단일 worker 프로세스의 completion 요청에 적용한다. 다른 프로세스·외부 도구·embedding 요청까지 계정 전체로 묶는 분산 제한은 아니다. 사용자가 알려준 일1500회 한도는 제공자가 적용하며 앱에 별도 일일 DB 카운터를 추가하지 않았다. provider quota 오류는 기존 오류와 감사 기록으로 남는다. 병렬 요청은 대기 때문에 응답 시간이 늘어날 수 있다.

모델 목록에 있다는 사실만으로 생성 권한을 보장하지 않는다. 이번 실제 연결 검사에서2.5Pro는 목록에 있었지만 생성404였고3.1Pro Preview 생성은 성공했다. 최종 Tester2 runtime은 사용자 선택에 따라 `gemini-3-flash-preview`로 설정되었고 root가 연결을 검증했다.
