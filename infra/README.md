# infra — 로컬 인프라

`docker-compose.yml`로 의존 서비스를 띄운다.

| 컨테이너 | 역할 | MVP |
|---|---|:---:|
| postgres | 관계형 데이터 | ✅ |
| qdrant | 벡터 스토어 (개념+힌트 색인) | ✅ |
| judge0 (+db, +worker) | 코드 채점 샌드박스 | ✅ |
| neo4j | Graph RAG (확장) | ⬜ |

> 채점 큐는 MVP에서 API 프로세스 내부 인메모리 큐를 사용하므로 Redis 컨테이너가 없다.

```bash
# 앱 서비스만 (권장, 로컬 개발)
docker compose -f infra/docker-compose.yml up -d postgres qdrant

# Graph RAG 포함 (확장)
docker compose -f infra/docker-compose.yml --profile graphrag up -d

# 전체 (judge0 포함) — 아래 제약 참고
docker compose -f infra/docker-compose.yml up -d
```

## ⚠️ Judge0 로컬 실행 제약 (macOS / Apple Silicon)

Judge0의 채점 API 서버는 macOS에서도 뜨지만, **isolate 샌드박스 코드 실행은 실패**한다.
(`status: Internal Error`, `/box/script.py: No such file or directory`)

- 원인: Judge0 1.13.1은 **cgroup v1 + linux/amd64**를 요구한다. Docker Desktop(cgroup v2) +
  Apple Silicon(arm64 에뮬레이션) 환경에서는 isolate가 정상 동작하지 않는다. 설정 오류가 아니다.
- **개발 시 대응 방안**:
  1. 실제 채점은 **Linux 호스트 / CI**에서 검증한다. (거기서는 이 compose가 그대로 동작)
  2. 또는 원격 Judge0 인스턴스 URL을 `.env`의 `JUDGE0_URL`에 지정한다.
  3. 로컬 단위테스트에서는 `run_user_code` Tool(Judge0 클라이언트)을 **모킹**한다. (Phase 3~4)
- 앱 개발(Agent/RAG/API/Web)은 postgres + qdrant만으로 진행 가능하다.
