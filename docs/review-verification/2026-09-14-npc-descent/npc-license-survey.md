# NPC 슬롯 상업 라이선스 조사 — exaone 대안 (2026-09-14)

> 배경: NPC 후보 비교(A.14~A.16)에서 `exaone3.5:7.8b`가 발화 품질 기준선인데,
> 라이선스가 상업 이용을 막는지 확인하고 "상업 가능 + 한국어 강점 + NPC 슬롯 크기" 대안을 조사했다.
> **법률 자문이 아니다 — 원문 조항 인용 + 해석이며, 최종 판단은 계약 검토로 한다.**

## 1. EXAONE 3.5 — 연구 전용, 상업은 별도 계약

공식 저장소 LICENSE(EXAONE AI Model License Agreement 1.1 - NC):

> "open to anyone for **research purposes**... **For commercial use**, please reach out to the official
> contact point of LG AI Research: contact_us@lgresearch.ai"
> "modifications and Derivatives are used **exclusively for research purposes**"

**해석**: 데모데이 제출을 넘어 서비스 오픈(상업 배포)하려면 LG AI Research와 별도 계약 없이는 **사용 불가**.
사용자 우려("엑사온이 상업용으론 안 되는 점")가 원문으로 확인됨.
- 출처: https://github.com/LG-AI-EXAONE/EXAONE-3.5/blob/main/LICENSE

## 2. 대안 후보 표

| 모델 | 크기 | 라이선스 | 상업 | 한국어 특화 | 가용성 (2026-09) |
|---|---|---|---|---|---|
| **KT Mi:dm 2.0 Mini** | 2.3B | **MIT** | O | ◎ "Korea-centric AI" (KT) | HF GGUF (DevQuasar 등) → ollama import |
| KT Mi:dm 2.0 Base | 11.5B | MIT | O | ◎ | NPC 슬롯엔 과대(Core 12b와 pair 불가) |
| **Kakao Kanana 1.5** | 2.1B / **8B** | **Apache 2.0** | O | ◎ (카카오 한국어 중심) | HF GGUF(community) → ollama import |
| SKT A.X 4.0 Light / 3.1 Light | ~7B | **Apache 2.0** | O | ◎ (한국어 코퍼스 1.65T) | HF GGUF(mykor 등) — 이번 회차 미평가, 가용성만 기록 |
| Naver HyperCLOVA X SEED | 0.5/1.5/3B | HyperCLOVA X SEED 전용 라이선스 | **조건부 O — MAU 1,000만 이하 서비스 허용** | ◎ | HF GGUF(community 1.5B 등) — 미평가 |
| Google gemma4:e4b | ~4B급 (3.06GiB) | **Apache 2.0** (Gemma 4부터) | O | ○ (다국어, 한국어 통과 이력 — E7 셀) | **로컬 보유** |
| Qwen3.5 (4b 등) | 0.8~9B | Apache 2.0 | O | △ (다국어 — A.14에서 한국어 품질 열세 실측) | 로컬 보유 |

## 3. 스택 전체 라이선스 점검

| 슬롯 | 모델 | 라이선스 | 상업 배포 관점 |
|---|---|---|---|
| Core (운영) | gemma4:12b | **Apache 2.0** (Gemma 4부터 Apache — Gemma 3 이전은 Gemma Terms) | 문제 없음 |
| NPC (현행) | exaone3.5:7.8b | EXAONE NC (연구 전용) | **블로커 — 교체 또는 LG 계약 필요** |
| judge (개발 도구) | gemma3:12b | Gemma Terms of Use (상업 이용 허용 + 사용 제한 정책) | 배포 스택 밖(평가 도구)이라 영향 낮음. 원하면 gemma4로 대체 가능 |
| embedding (운영) | gemini API | Google API 약관 | 유·무료 티어 약관 차이 유의(무료 티어 데이터 활용 조항) |

## 4. 이번 회차 평가 대상 선정

1. **gemma4:e4b** — 로컬 보유·Apache·무비용. 상업 축 1순위 검증
2. **Kanana 1.5 8B (Q4_K_M)** — 상업(Apache) × 한국어 특화의 품질 축
3. **Mi:dm 2.0 Mini 2.3B (Q4_K_M)** — 상업(MIT) × 한국 특화의 VRAM 축 (2B급 3세화 전례 있음 — 검증 목적)
- A.X Light·HyperCLOVA SEED는 가용성 기록만 (후속 여지)

## 출처

- EXAONE 3.5 LICENSE: https://github.com/LG-AI-EXAONE/EXAONE-3.5/blob/main/LICENSE
- Mi:dm 2.0 (MIT, Korea-centric): https://github.com/K-intelligence-Midm/Midm-2.0 · https://huggingface.co/K-intelligence/Midm-2.0-Base-Instruct
- Kanana 1.5 (Apache 2.0): https://huggingface.co/kakaocorp/kanana-1.5-8b-instruct-2505 · https://huggingface.co/kakaocorp/kanana-1.5-2.1b-instruct-2505
- A.X (Apache 2.0): https://huggingface.co/skt/A.X-4.0-Light · https://huggingface.co/skt/A.X-3.1-Light
- HyperCLOVA X SEED (MAU 1천만 조건): https://clova.ai/en/tech-blog/sowing-the-seeds-in-the-ai-ecosystem-introducing-hyperclova-x-seed-a-commercial-open-source-ai
- Gemma 4 Apache 2.0: https://en.wikipedia.org/wiki/Gemma_(language_model) · https://ollama.com/library/gemma4:12b
