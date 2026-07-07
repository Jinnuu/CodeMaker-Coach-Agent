# packages/agent — Agent 코어 (LangGraph)

웹/DB에 의존하지 않는 **독립 Python 패키지**. CLI/테스트/노트북에서 단독 실행 가능해야 한다.

- `graph.py` — LangGraph 워크플로우 조립 (`build_graph()`)
- `state.py` — GraphState 정의
- `llm.py` — LLM Provider 팩토리 (claude/openai)
- `nodes/` — 각 Agent = 하나의 Node (problem_generator, testcase_generator, reference_solver, validator, feedback_hints)
- `tools/` — LangChain Tool (run_user_code 등은 Judge0 클라이언트)
- `prompts/` — PromptTemplate

상세: `docs/AGENTS_AND_TOOLS.md`, `docs/ARCHITECTURE.md`
