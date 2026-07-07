# packages/graphrag — Graph RAG (Neo4j) [확장]

사용자 약점·문제·개념·오답유형 관계를 저장해 맞춤형 문제 생성에 활용한다. (MVP 이후 확장)

- Node: User, Problem, Concept, Pattern, Difficulty, ErrorType, TestCase, Submission, SourceDocument
- Edge: REQUIRES_CONCEPT, USES_PATTERN, USER_FAILED_ON, HAS_COMMON_ERROR 등

상세: 기획 11장, `docs/ARCHITECTURE.md` 2.5
