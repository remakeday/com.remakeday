# DB 비밀번호 코드 제거·교체 Implementation Plan

**검토 등급:** A (보안)

**Goal:** 공개 저장소(github.com/remakeday/com.remakeday)에 평문으로 커밋된 DB 비밀번호를 코드에서 없애고, git 이력에 남은 옛 값을 교체로 무효화한다.

**Architecture:** 비밀번호의 원천은 git이 무시하는 `.env` 두 곳뿐이다 — 루트 `.env`의 `POSTGRES_PASSWORD`(docker compose 보간), `backend/.env`의 `DATABASE_URL`(백엔드 `Settings`). 코드는 값을 읽기만 한다.

## Global Constraints

- 비밀번호 값은 출력·문서·테스트·커밋 메시지·명령줄 인자에 적지 않는다. 확인은 True/False·개수로만 한다. **이번 교체에서도 이 저장소의 문서·테스트에 새 값을 넣지 않는다** — 옛 값이 공개 이력에 남은 경위가 바로 테스트 리터럴이었다.
- DB는 `127.0.0.1:5435`에만 열려 있고 터널로 노출되지 않는다 — 옛 값 유출의 실제 위험은 로컬 접근자에 한정되지만, 공개 이력에 남았으므로 교체한다.
- 이 머신이 배포 서버다(8500 = `api.remakeday.com`, cloudflared). 별도 배포 서버의 `.env`는 없다.

## 교체 실행 전 체크리스트 (opus 리뷰 정리)

실행 직전에 위에서부터 하나씩 확인한다. 하나라도 아니면 멈춘다.

- [ ] 다른 pytest·8600 루프 서버·다른 에이전트의 백엔드 작업이 없다(1단계 명령). 교체 중 테스트 DB 연결이 끊기고, `.env`를 먼저 바꾸므로 그 사이 시작한 pytest는 실패한다.
- [ ] 한가한 시간대이고 진행 중인 플레이가 없다(`backend.log` 끝이 1~2분 동안 늘지 않음). 8500 재시작 동안 공개 API가 잠깐 끊기고 진행 중인 LLM 요청이 끊긴다.
- [ ] 새 값을 두 `.env`에 저장한 뒤 동일성 확인이 True다(3단계).
- [ ] ALTER 직후 곧바로 **uvicorn(8500)만** 재시작한다(4→5단계). `start_demo.sh`는 쓰지 않는다.
- [ ] 확인(모두 True): DB 연결 / 로컬 `/health` 200 / `api.remakeday.com/health` 200 / `tests/engine/test_guards.py` 통과 / `docker compose config` / 옛 비밀번호 접속 거부.
- [ ] `backend/.env.bak.20260916` 삭제, `backend/.env`·루트 `.env` `chmod 600`, `unset NEW_PW`.

## Part 1 — 코드에서 제거 (완료, 2026-09-18)

- [x] `docker-compose.yml`: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?…}` — 값이 없으면 compose가 안내 문구와 함께 실패. 사용자·DB 이름(`pigfarm`)은 비밀이 아니라 그대로 둔다.
- [x] `backend/tests/conftest.py`: `TEST_DATABASE_URL` 우선, 없으면 `Settings().database_url`(환경변수 > `backend/.env`)에서 DB 이름만 `pigfarm_test`로 바꾼다. 관리 접속 DB는 기존과 같이 `pigfarm`. 둘 다 없으면 `RuntimeError`로 안내.
- [x] `backend/tests/conftest.py` 가드: 최종 테스트 URL(`TEST_DATABASE_URL` 포함)의 DB 이름이 `_test`로 끝나지 않으면 `RuntimeError`(값 없는 안내 문구). 테스트는 매번 모든 테이블을 `TRUNCATE`하므로 운영 DB를 가리키는 경로를 막는다.
- [x] `backend/scripts/run_core_selection.py`: `LOOP_DB_URL` 상수 → `_loop_db_url()`(`get_settings().database_url`에서 DB 이름만 `pigfarm_test`).
- [x] `docs/demo_guide.md`: "DB 비밀번호는 `.env`에만" 안내 한 줄.
- [ ] **루트 `.env`에 `POSTGRES_PASSWORD` 추가(컨트롤러)** — 이 줄이 생기기 전까지 `docker compose up/stop`(=`start_demo.sh`·`stop_demo.sh`)이 보간 오류로 멈춘다. 실행 중인 컨테이너에는 영향 없음. Part 2의 3단계에서 함께 넣는다.

기존 컨테이너: compose가 해석한 값이 컨테이너에 들어간 값과 같으면 설정 해시가 같아 `docker compose up -d`가 컨테이너를 다시 만들지 않는다(2026-09-18 확인: True). 값이 바뀌면 컨테이너가 재생성되지만 볼륨(`demopigfarm_pigfarm-db-data`)은 유지된다. **이미 초기화된 볼륨은 `POSTGRES_PASSWORD`를 다시 읽지 않는다** — 실제 비밀번호는 `ALTER USER`로만 바뀐다.

## Part 2 — 교체 절차 (실행 전, 컨트롤러가 한 번에)

대상(compose 기준): 서비스·컨테이너 `pigfarm-db`, DB 사용자 `pigfarm`, 기본 DB `pigfarm`(테스트 DB `pigfarm_test`도 같은 사용자). 순서는 **env 저장(3) → ALTER(4) → uvicorn 재시작(5)**이다. 모든 명령은 저장소 루트에서 한 셸 세션으로 실행한다(셸 변수 유지).

### 1. 선행 확인

```bash
pgrep -af pytest                       # 비어 있어야 한다
ss -ltn 'sport = :8600' | tail -n +2   # 루프 서버 없음 → 빈 출력
wc -l backend.log; # 1~2분 뒤 다시 실행해 줄 수가 그대로인지 본다(진행 중 플레이 없음)
tail -n 20 backend.log                 # 최근 요청이 /api/v1/... 플레이 요청으로 이어지고 있지 않은지
```

에이전트 래퍼(`bash -c "..."`)로 실행하면 `pgrep -f`가 래퍼 자신의 명령줄에 걸릴 수 있다. 결과에 나온 PID의 `ps -o args= -p <PID>`가 실제 pytest인지 확인한다.

### 2. 새 값 생성 — 셸 변수에만

값을 화면에 내지 않는다. URL에 그대로 넣을 수 있게 영숫자(hex)만 쓴다.

```bash
NEW_PW=$(openssl rand -hex 24)
```

### 3. env 저장 (ALTER보다 먼저)

두 파일을 같은 값으로 갱신한다. 값은 **환경변수로** 파이썬에 넘긴다(명령줄 인자 금지 — 프로세스 목록 노출). 결과는 출력하지 않고 True/False만 본다.

```bash
NEW_PW="$NEW_PW" backend/.venv/bin/python - <<'EOF'
import os
from pathlib import Path
from sqlalchemy.engine import make_url

def read(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def put(path, key, value):
    p = Path(path)
    lines, done = p.read_text(encoding="utf-8").splitlines(), False
    for i, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == key:
            lines[i], done = f"{key}={value}", True
    if not done:
        lines.append(f"{key}={value}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")   # 기존 파일 권한 유지

pw = os.environ["NEW_PW"]
url = make_url(read("backend/.env")["DATABASE_URL"]).set(password=pw)
put("backend/.env", "DATABASE_URL", url.render_as_string(hide_password=False))
put(".env", "POSTGRES_PASSWORD", pw)

b, r = read("backend/.env"), read(".env")
print("db pw same in both .env:", make_url(b["DATABASE_URL"]).password == r.get("POSTGRES_PASSWORD"))
print("db pw is new:", r.get("POSTGRES_PASSWORD") == pw)
EOF
```

둘 다 True가 아니면 멈추고 롤백 절을 본다. 이 시점에는 DB 비밀번호가 아직 옛 값이다 — 실행 중인 uvicorn은 메모리의 옛 설정으로 계속 동작하고, 새로 시작하는 pytest·스크립트는 접속에 실패한다(그래서 1단계가 선행 조건이다).

### 4. DB에서 교체 (ALTER)

실행 중인 컨테이너 안에서 로컬 소켓(trust)으로 접속하므로 옛 비밀번호가 필요 없다. SQL은 `printf`(셸 내장, 프로세스 목록에 안 남음)로 stdin에 넣는다. psql 출력은 버리고 종료 코드만 본다(오류 메시지에 문장이 찍힐 수 있다).

```bash
printf "ALTER USER pigfarm WITH PASSWORD '%s';\n" "$NEW_PW" \
  | docker exec -i pigfarm-db psql -U pigfarm -d pigfarm -q -v ON_ERROR_STOP=1 >/dev/null 2>&1 \
  && echo 'alter: True' || echo 'alter: False'
```

- **실패(False)면** 새 값이 서버 로그에 남았을 수 있다(`log_min_error_statement` 기본 ERROR → `STATEMENT:` 줄). 값을 보지 말고 개수만 센다: `docker logs pigfarm-db 2>&1 | grep -c 'ALTER USER'`. 1 이상이면 그 컨테이너 로그에 값이 있다는 뜻이므로, 교체를 마친 뒤 컨테이너 재생성(`docker compose up -d`, 볼륨 유지) 때 로그와 함께 사라지게 하고 그 전까지 로그를 공유하지 않는다. 원인을 고친 뒤 같은 명령을 다시 실행한다.
- 성공한 ALTER는 기본 설정(`log_statement=none`)에서 로그에 남지 않는다.
- ALTER 뒤 5단계까지의 짧은 구간에는 실행 중인 백엔드의 **기존 풀 연결은 유지**되고 새 연결만 실패한다. 곧바로 5단계로 간다.

### 5. uvicorn(8500)만 재시작

`start_demo.sh`는 쓰지 않는다 — 루트 `.env` 값이 바뀌어 compose 설정 해시가 달라지므로 `docker compose up -d`가 DB 컨테이너를 재생성하고, ollama 워밍업이 실패하면 `exit 1`로 중간에 멈춘다. 컨테이너 재생성은 다음 정상 기동으로 미룬다(그때 볼륨이 유지되므로 새 비밀번호 그대로 정상 접속된다).

8500이 곧 `api.remakeday.com`이다. 재시작 동안 공개 API가 잠깐 끊기고 진행 중인 LLM 요청이 끊기거나 종료가 그 요청이 끝날 때까지 늦어진다.

기존 실행 명령(2026-09-18 `ps`·`start_demo.sh` 확인, 작업 디렉터리 `backend/`)과 같은 명령으로 다시 띄운다. `pkill -f`는 에이전트 래퍼 셸의 명령줄에도 걸릴 수 있으므로 포트에서 PID를 찾는다.

```bash
cd backend
PID=$(ss -ltnpH 'sport = :8500' | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2)
ps -o args= -p "$PID"          # .venv/bin/uvicorn main:app --port 8500 --host 127.0.0.1 인지 확인
kill "$PID"
while kill -0 "$PID" 2>/dev/null; do sleep 1; done   # 30초 넘게 안 끝나면 진행 중 요청 — 기다리거나 kill -9
nohup .venv/bin/uvicorn main:app --port 8500 --host 127.0.0.1 > ../backend.log 2>&1 &
until curl -sf localhost:8500/health >/dev/null; do sleep 1; done
cd ..
```

`> ../backend.log`는 `start_demo.sh`와 같이 로그를 덮어쓴다. 필요하면 재시작 전에 복사해 둔다. alembic은 스키마 변경이 없으므로 돌리지 않는다.

### 6. 확인 (True/False만)

```bash
cd backend
PYTHONPATH=. .venv/bin/python -c "
from sqlalchemy import create_engine, text
from core.matrix.grid_keymaker_secret_manager import get_settings
e = create_engine(get_settings().database_url)
with e.connect() as c: print('db connect:', c.execute(text('select 1')).scalar() == 1)"
curl -s -o /dev/null -w '%{http_code}\n' localhost:8500/health                   # 200
curl -s -o /dev/null -w '%{http_code}\n' https://api.remakeday.com/health        # 200
PYTHONPATH=. .venv/bin/python -m pytest -q tests/engine/test_guards.py          # passed
cd .. && docker compose config --quiet && echo 'compose: True'
```

옛 비밀번호 접속 거부 — 옛 값은 교체 전 커밋 `1ea9d81`의 `docker-compose.yml`에서 읽고 출력하지 않는다:

```bash
backend/.venv/bin/python - <<'EOF'
import re, subprocess, psycopg
old = re.search(r"POSTGRES_PASSWORD:\s*(\S+)",
                subprocess.run(["git", "show", "1ea9d81:docker-compose.yml"], capture_output=True, text=True).stdout).group(1)
try:
    psycopg.connect(host="127.0.0.1", port=5435, user="pigfarm", dbname="pigfarm", password=old, connect_timeout=5).close()
    print("old pw rejected: False")
except psycopg.OperationalError:
    print("old pw rejected: True")
EOF
```

### 7. 정리

```bash
rm backend/.env.bak.20260916      # 현재 OAuth 시크릿·세션 시크릿·Gemini 키와 같은 값이 들어 있다
chmod 600 backend/.env .env
unset NEW_PW
```

## 롤백

- **옛 값으로 되돌리는 것은 선택지가 아니다** — 옛 값은 공개 이력에 있다.
- **3단계 뒤·4단계 전 실패**: DB는 아직 옛 값이다. 원인을 고치고 4단계를 진행한다(env는 이미 새 값).
- **4단계 뒤 실패(백엔드가 DB에 못 붙음 등)**: 컨테이너 안 trust 접속으로 `backend/.env`에 저장된 값을 다시 ALTER해 env와 DB를 맞춘다. 셸 변수가 살아 있으면 4단계를 그대로 재실행한다. 셸을 잃었으면 `backend/.env`에서 값을 읽어(출력 없이) 같은 방식으로 넣는다:
  ```bash
  backend/.venv/bin/python - <<'EOF' | docker exec -i pigfarm-db psql -U pigfarm -d pigfarm -q -v ON_ERROR_STOP=1 >/dev/null 2>&1 && echo 'realign: True' || echo 'realign: False'
  from sqlalchemy.engine import make_url
  from pathlib import Path
  line = next(l for l in Path("backend/.env").read_text(encoding="utf-8").splitlines() if l.startswith("DATABASE_URL="))
  print(f"ALTER USER pigfarm WITH PASSWORD '{make_url(line.split('=', 1)[1].strip().strip(chr(34)).strip(chr(39))).password}';")
  EOF
  ```
  `.env` 자체가 깨졌으면 2단계부터 새 값으로 다시 실행한다(3→4→5).
- **5단계 실패(uvicorn이 안 뜸)**: `backend.log`에서 원인을 보되 값이 찍힌 줄은 공유하지 않는다. DB 연결 문제면 위 재정렬 후 5단계만 다시 한다.

## 남는 위험

- **git 이력** — 옛 값은 공개 저장소의 과거 커밋 2개, 3곳에 영구히 남는다: `9ad8ecc`(`backend/scripts/run_core_selection.py`), `f2b4926`(`backend/tests/conftest.py`·`docker-compose.yml`). 이력 재작성은 하지 않는다 — 교체로 옛 값을 무효화하는 것이 해결책이다.
- **다른 사본** — 포크·클론·로컬 사본(`demo.pigfarm` 시절 경로 포함)과 `__pycache__`의 `.pyc`에 옛 값이 남을 수 있다. 교체 후에는 무해.
- 루트 `.env`와 `backend/.env`에 같은 DB 비밀번호가 두 번 있다 — 한쪽만 바꾸면 compose가 컨테이너를 재생성하거나 백엔드 접속이 실패한다(3단계에서 둘 다, 동일성 True 확인).
- 교체를 마친 뒤 첫 `docker compose up -d`(`start_demo.sh` 포함)는 DB 컨테이너를 재생성한다. 볼륨이 유지되므로 정상이며, 4단계 실패 로그가 있었다면 이때 함께 사라진다.
