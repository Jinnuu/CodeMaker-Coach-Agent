# CodeMaker Coach 임시 프론트엔드 (개발 검증용)

CORS와 `POST /api/problems/generate` API를 웹 브라우저에서 편리하게 수동 검증하기 위해 제공되는 임시 정적 웹 페이지입니다.

## 실행 방법

### Terminal 1: FastAPI API 서버 실행 (포트 8011)

```bash
PYTHONPATH=apps/api AGENT_MODE=stub uv run uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

### Terminal 2: Nginx 임시 프론트엔드 실행 (포트 5173)

```bash
docker compose -f docker-compose.temp.yml up
```

### 웹 브라우저 확인

브라우저에서 아래 링크에 접속하여 UI 테스트를 수행합니다:
[http://localhost:5173](http://localhost:5173)

---

## 독립 수동 체크 명령어

### 1. 헬스 체크 API

```bash
curl http://localhost:8011/health
```

### 2. 문제 생성 API 호출 테스트

```bash
curl -X POST http://localhost:8011/api/problems/generate \
  -H "Content-Type: application/json" \
  -d '{"algorithm":"binary_search","difficulty":"easy","learning_goal":"상한액 C 이분 탐색"}'
```

---

## 프론트엔드 종료

```bash
docker compose -f docker-compose.temp.yml down
```

---

## 데이터베이스 자격 증명 획득 방법 (참고용)

기존 동작 중인 `codemaker-postgres-1`의 환경 변수로부터 비밀번호를 파악하려면 호스트의 터미널에서 다음 명령을 실행하십시오:

```bash
docker inspect codemaker-postgres-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep POSTGRES
```
