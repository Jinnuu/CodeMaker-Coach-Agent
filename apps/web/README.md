# apps/web — 프론트엔드 (Next.js)

- `/generate` — 문제 생성 화면 (알고리즘·난이도·스타일·언어·힌트 방식 선택)
- `/solve/[id]` — 문제 풀이 화면 (Monaco/CodeMirror 에디터 + AI Tutor 챗봇 패널)
- `/community` — 코드 공유 피드 (AC gating 적용)

힌트 단계·정답 노출 여부는 서버가 판단한다(프론트에서 임의 변경 불가). Phase 8에서 초기화한다.
