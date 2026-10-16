# REMAKE DAY — ERD

- 기준: alembic head `216f290d03b3` (survey_votes), 2026-10-01 개발 DB 제약 조건과 대조
- 정본: `backend/apps/engine/adapter/outbound/orms/*.py` — 이 문서는 그 모델을 그림으로 옮긴 것이다
- 실선 = DB에 외래 키가 있는 관계, 점선 = 코드로만 지키는 관계(외래 키 없음)

## 1. 게임 상태·계정·로그

```mermaid
erDiagram
    users |o..o{ attempts : "user_id"
    users |o..o{ survey_votes : "user_id"
    attempts |o..o{ attempts : "prior_attempt_id"
    attempts ||--o{ loops : "attempt_id"
    attempts ||--o{ notes : "attempt_id"
    attempts ||--o{ rules : "attempt_id"
    attempts ||..o| survey_votes : "attempt_id"
    attempts |o..o{ events : "session_id"
    loops ||--o{ npc_states : "loop_id"
    loops ||--o| nights : "loop_id"

    users {
        uuid id PK
        string google_sub UK "Google 계정 식별자"
        string email
        string name
        string picture
        timestamptz created_at
        timestamptz last_login_at
    }

    attempts {
        uuid id PK
        int attempt_n "몇 번째 판"
        uuid prior_attempt_id "이전 판 (FK 없음)"
        string status "active | closed"
        string closed_by
        jsonb prior_cell_results
        jsonb cookies_seen
        int paw_offered_count
        uuid user_id "판 소유자 (FK 없음, 구판은 NULL)"
        timestamptz created_at
    }

    loops {
        uuid id PK
        uuid attempt_id FK,UK "UK(attempt_id, loop_n)"
        int loop_n UK
        int beat
        int budget_left
        int ask_budget_left
        int manager_budget_left
        string state "day | night_pending | night_draft | scored | intervention | closed"
        int damage_level
        bool morning_shifted
        float score
        string world_outcome
        int anomaly_count
        int rumor_index
        jsonb cause_chain
        jsonb side_effect_claims
        jsonb pending_paw
        timestamptz created_at
    }

    npc_states {
        int id PK
        uuid loop_id FK,UK "UK(loop_id, code)"
        string code UK "scenario_characters.code"
        string name
        int suspicion
        int trust
        bool opposite_mode
        bool flagged_abnormal
        string mood
        int uttered_beat "이 비트에 말 걸었으면 그 비트 번호"
        jsonb memory
        jsonb plan
    }

    nights {
        uuid id PK
        uuid loop_id FK,UK "루프당 밤 1개"
        jsonb tapped_note_ids
        text free_text
        jsonb claims
        jsonb fabricated_dropped
        bool user_edited
        int edit_count
        bool submitted
        jsonb per_truth_claim
        jsonb cell_scores
        float total
        bool passed
        int questions_left
        jsonb questions
        jsonb options
        bool rule_chosen
    }

    notes {
        int id PK
        uuid attempt_id FK,UK "UK(attempt_id, source_key)"
        string kind "fragment | confirmed | rule_observation | advice"
        text text
        int loop_n
        string source_key UK
    }

    rules {
        int id PK
        uuid attempt_id FK,UK "UK(attempt_id, rule_id)"
        string rule_id UK "R1, R2..."
        string source
        string target
        int when_beat "NULL = 모든 비트"
        string effect
        string action
        text shown_reason
        text hidden_side_effect
        int created_loop
        bool conflict
    }

    survey_votes {
        uuid id PK
        uuid attempt_id UK "판당 한 표 (FK 없음)"
        uuid user_id "(FK 없음)"
        bool skipped "건너뛰기도 행으로 남긴다"
        smallint fun "1~5 또는 NULL"
        smallint novelty "1~5 또는 NULL"
        smallint ai_agency "1~5 또는 NULL"
        smallint polish "1~5 또는 NULL"
        smallint recommend "1~5 또는 NULL"
        timestamptz created_at
    }

    events {
        bigint id PK
        uuid session_id "대개 attempts.id (FK 없음)"
        int attempt_n
        int loop_n
        string type
        jsonb payload
        timestamptz created_at
    }
```

## 2. 시나리오 시드 (참조 데이터)

매 기동 때 자연키 기준으로 upsert 한다. 테이블끼리도, 게임 상태 테이블과도 외래 키가 없고 `scenario` 문자열과 코드 값으로만 이어진다.

```mermaid
erDiagram
    scenario_truth_claims ||..o| truth_claim_embeddings : "scenario + code = claim_code"

    scenario_characters {
        int id PK
        string scenario UK "UK(scenario, code)"
        string code UK
        string name
        string role
        text persona
        int initial_suspicion
        int initial_trust
        bool lost
    }

    scenario_beats {
        int id PK
        string scenario UK "UK(scenario, n)"
        int n UK
        string title
        text narration
        text morning_text
    }

    scenario_truth_claims {
        int id PK
        string scenario UK "UK(scenario, code)"
        string code UK
        string cell
        text text
    }

    scenario_cookies {
        int id PK
        string scenario UK "UK(scenario, text_id)"
        string text_id UK
        string cell
        int level
        text text
    }

    scenario_fragments {
        int id PK
        string scenario UK "UK(scenario, code)"
        string code UK "fr-{loop}-{n}"
        int loop_n
        text text
    }

    truth_claim_embeddings {
        int id PK
        string scenario UK "UK(scenario, claim_code)"
        string claim_code UK
        vector embedding "1536차원, 현재 미사용"
    }
```

## 3. 읽을 때 주의할 점

- **외래 키는 5개뿐이다.** `loops`·`notes`·`rules` → `attempts`, `npc_states`·`nights` → `loops`. 나머지 관계는 전부 애플리케이션 코드가 지킨다.
- **`attempts.user_id`** 는 판 소유 판정의 유일한 기준이다(`AttemptRepository.get_owned`). 로그인 도입 전에 만든 판은 NULL 이고 누구의 것도 아니다.
- **`events.session_id`** 는 보통 `attempts.id` 지만, 판이 만들어지기 전에 막힌 요청(일일 정원·사용자 한도 가드)은 일회용 UUID 로 기록되므로 `attempts` 에 짝이 없는 행이 있다. 인덱스: `session_id`, `(session_id, type)`.
- **`survey_votes`** 는 CHECK 제약으로 점수 범위(1~5)와 건너뛰기 일관성(건너뛰면 점수 0개, 아니면 1개 이상)을 강제한다.
- **`npc_states.code`** 는 `scenario_characters.code` 값을 루프 시작 시 복사한 것이다. 시드가 바뀌어도 진행 중인 루프의 행은 따라 바뀌지 않는다.
- **`truth_claim_embeddings`** 는 스키마만 있고 런타임에서 쓰지 않는다. 컬럼 규격은 1536차원이고 실제 임베딩 차원 설정(`Settings.embedding_dimensions`)과 다르다.
