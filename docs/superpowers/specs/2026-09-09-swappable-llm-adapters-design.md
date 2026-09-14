# Gemini/Ollama LLM Adapter 전환 설계

날짜: 2026-09-09  
상태: **사용자 승인 / core 실제 Gemini 전환·검증 진행 중**

## 목표

기존 `LLMPort.complete()` 계약과 하네스·도메인 로직을 바꾸지 않고 NPC와 core 역할의 LLM provider를 설정으로 `ollama` 또는 `gemini` 중 선택할 수 있게 한다.

## 경계

- 기존 `OllamaLLM`은 유지하고 같은 outbound adapter 위치에 `GeminiLLM`을 추가한다.
- `llm_factory.py`만 provider 이름을 구체 adapter로 바꾸는 composition root다.
- 기존 `NPC_LLM_PROVIDER`, `NPC_LLM_MODEL`, `CORE_LLM_PROVIDER`, `CORE_LLM_MODEL`, `GEMINI_API_KEY`, `OLLAMA_BASE_URL` 설정을 재사용한다.
- 구현 검증 뒤 core만 실제 Gemini로 전환한다. NPC는 `ollama:exaone3.5:7.8b`, embedding은 기존 Gemini를 유지한다.
- 설치된 `google-genai==1.29.0`만 사용하며 새 dependency를 추가하지 않는다.
- Gemini SDK의 요청·structured JSON 응답 변환은 adapter 안에 가두고, SDK 타입을 port나 use case로 넘기지 않는다.
- provider 오류는 그대로 호출자에게 전달하고 JSON 파싱 실패만 기존 `LLMParseError` 계약으로 번역한다. 재시도·스키마 검사는 기존 하네스 책임이다.
- `gemini-2.5-pro`는 현재 key에서 generation404였다. 사용자는 실제 structured JSON probe가 2.543초에 성공한 `gemini-3-flash-preview`를 core 기본 모델로 선택했다.
- 사용자는 실제 Gemini 호출, 동일 corpus 검증, core 설정 전환, 테스터2용 8500 재기동을 승인했다. 비밀값은 출력·artifact에 저장하지 않는다.
- adapter 전환 성공은 기존 Ollama RM1 의미 오판이 해결됐다는 증거가 아니다. 동일 corpus의 실제 Gemini 결과를 독립적으로 판정한다.

## 수용 기준

1. mock Gemini client로 message role/content, model, temperature, JSON schema가 SDK 호출에 정확히 전달된다.
2. 정상 JSON text는 `dict`로 반환되고 잘못된 JSON은 `LLMParseError`가 된다.
3. factory는 fake·ollama·gemini를 선택하며 알 수 없는 provider는 기존처럼 fail-fast한다.
4. NPC와 core는 각자의 provider/model 설정을 독립적으로 사용할 수 있다.
5. pure·factory 회귀, architecture contract, forbidden-word scan, 전체 backend suite를 통과한다.
6. 실제 Gemini adapter probe와 동일 12+10+3+3 corpus의 provider·의미 결과를 기록한다.
7. core provider/model만 검증된 Gemini로 바꾼 새 8500에서 health·새 OpenAPI3경로와 frontend `/play` HTTP200을 확인한다.
