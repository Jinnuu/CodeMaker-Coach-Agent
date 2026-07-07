# packages/rag — RAG 파이프라인

`docs/knowledge/`의 개념 문서를 색인하고 검색한다.

- Loader → TextSplitter → Embedding → VectorStore(Qdrant) → Retriever
- 검색 대상 2종: (1) 알고리즘 개념 문서 색인, (2) 문제별 힌트 색인(허용 단계 필터)

상세: `docs/ARCHITECTURE.md` 2.4
