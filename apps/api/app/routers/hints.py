"""Hints 라우터 — 챗봇형 힌트 요청 / 단계 승급 (FR-15~FR-19, NFR-4).

핵심 보안 규칙:
1. 허용 단계 초과 힌트는 서버에서 물리적으로 차단 (검색 자체를 막음).
2. 단계 승급은 명시적 confirm=true 요청을 거쳐야만 한다.
3. 클라이언트가 allowed_level을 임의로 올릴 수 없다.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.db import get_db
from app.gateway import AgentGateway, get_agent_gateway
from app.models.problem import Hint, Problem
from app.models.submission import HintProgress
from app.schemas.domain import HintProgressResponse, HintResponse, HintUnlockRequest

from agent import (
    request_hint_package,
    hint_package_to_dict,
    HintRequestPackageInput,
)

router = APIRouter(prefix="/api/hints", tags=["hints"])


def _dep_gateway() -> AgentGateway:
    return get_agent_gateway()


def _get_or_create_progress(user_id: int, problem_id: str, db: Session) -> HintProgress:
    """힌트 진행 상태를 가져오거나 level=1로 초기화한다."""
    progress = (
        db.query(HintProgress)
        .filter(HintProgress.user_id == user_id, HintProgress.problem_id == problem_id)
        .first()
    )
    if not progress:
        progress = HintProgress(user_id=user_id, problem_id=problem_id, allowed_level=1)
        db.add(progress)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            progress = (
                db.query(HintProgress)
                .filter(HintProgress.user_id == user_id, HintProgress.problem_id == problem_id)
                .first()
            )
    return progress


def _deduplicate_hints(hints: List[Hint]) -> List[Hint]:
    """레벨별로 중복된 힌트가 DB에 적재되어 있더라도 최초 1개씩만 남기고 필터링한다."""
    seen = set()
    deduped = []
    for h in hints:
        if h.level not in seen:
            seen.add(h.level)
            deduped.append(h)
    return sorted(deduped, key=lambda x: x.level)


async def _get_or_generate_hints(
    problem_id: str,
    problem: Problem,
    db: Session,
    gateway: AgentGateway,
) -> List[Hint]:
    """DB에서 힌트를 조회하고, 없으면 예외 및 중복 방지 처리를 거쳐 실시간 생성 후 반환한다."""
    hints = db.query(Hint).filter(Hint.problem_id == problem_id).all()
    
    if not hints:
        from agent.schemas import GeneratedProblem, HintBlueprint, Hint as AgentHint
        
        generated = GeneratedProblem(
            problem_id=problem.id,
            title=problem.title,
            difficulty=problem.difficulty,
            algorithm=problem.algorithm,
            learning_goal=problem.learning_goal,
            statement=problem.statement,
            input_format=problem.input_format,
            output_format=problem.output_format,
            constraints=problem.constraints,
            sample_input=problem.sample_input,
            sample_output=problem.sample_output,
            expected_time_complexity=problem.expected_time_complexity,
            hint_blueprint=HintBlueprint(
                intended_algorithm=problem.algorithm,
                core_insight=problem.learning_goal or "알고리즘 구현을 위한 접근 방식",
                common_misconceptions=["시간 복잡도 초과", "경계 조건 처리 누락", "인덱스 범위 접근 초과"],
                edge_case_focus=["빈 배열/빈 입력 값", "단일 원소", "최대/최소 경계값"],
                forbidden_disclosures=["완전한 정답 소스 코드", "직접 카피 가능한 구현체"],
                level_1_guidance="문제의 핵심 요구사항과 접근 방식을 생각해보세요.",
                level_2_guidance="알고리즘 구현 시 필요한 핵심 자료구조와 탐색 흐름을 설계해보세요.",
                level_3_guidance="인덱스 범위와 예외 조건 처리에 주의하여 스켈레톤 빈칸을 채워보세요.",
            ),
        )
        
        try:
            hint_bundle = await gateway.generate_hints(generated, allowed_level=3)
            raw_hints = hint_bundle.hints
        except Exception as llm_err:
            import logging
            logging.getLogger(__name__).warning(f"Failed to generate hints in router, falling back to static hints: {llm_err}")
            raw_hints = [
                AgentHint(problem_id=problem_id, level=1, title="접근 힌트", content="문제 요구사항을 쪼개어 단순한 케이스부터 생각해보세요."),
                AgentHint(problem_id=problem_id, level=2, title="알고리즘 힌트", content="핵심 의도인 알고리즘 분류에 맞추어 설계를 구체화하세요."),
                AgentHint(problem_id=problem_id, level=3, title="구현 스켈레톤", content="아래의 구조를 토대로 작성해보세요.", code_skeleton="pass # TODO: 여기에 코드를 작성하세요.")
            ]

        # 중복 저장 방지: 저장 직전 기존 찌꺼기 힌트 일괄 삭제
        db.query(Hint).filter(Hint.problem_id == problem_id).delete()
        db.flush()

        for h in raw_hints:
            db.add(Hint(
                problem_id=problem_id,
                level=h.level,
                title=h.title,
                content=h.content,
                reveals_core_code=False,
                code_skeleton=h.code_skeleton,
                concept_refs=h.concept_refs or [],
                source=h.source or "generated",
            ))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            
        hints = db.query(Hint).filter(Hint.problem_id == problem_id).all()
        
    return _deduplicate_hints(hints)


@router.post("/request", status_code=status.HTTP_200_OK)
async def request_hint(
    body: HintRequestPackageInput,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    gateway: AgentGateway = Depends(_dep_gateway),
) -> dict:
    """챗봇형 힌트 요청 — Agent 패키지의 비동기 request_hint_package() 호출."""
    problem = db.get(Problem, body.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문제를 찾을 수 없습니다.")

    progress = _get_or_create_progress(user_id, body.problem_id, db)
    body.allowed_level = progress.allowed_level

    all_hints = await _get_or_generate_hints(body.problem_id, problem, db, gateway)
    allowed_hints = [h for h in all_hints if h.level <= progress.allowed_level]

    from agent.schemas import Hint as AgentHint
    agent_hints = [
        AgentHint(
            problem_id=h.problem_id,
            level=h.level,
            title=h.title,
            content=h.content,
            reveals_core_code=h.reveals_core_code,
            code_skeleton=h.code_skeleton,
            concept_refs=h.concept_refs or [],
            source=h.source or "db"
        )
        for h in allowed_hints
    ]

    package = await request_hint_package(body, generated_hints=agent_hints)
    return hint_package_to_dict(package)


@router.get("/{problem_id}/progress", response_model=HintProgressResponse)
def get_hint_progress(
    problem_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> HintProgressResponse:
    """현재 사용자의 힌트 허용 단계 조회."""
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문제를 찾을 수 없습니다.")
    progress = _get_or_create_progress(user_id, problem_id, db)
    return HintProgressResponse(problem_id=problem_id, allowed_level=progress.allowed_level)


@router.get("/{problem_id}", response_model=List[HintResponse])
async def get_hints(
    problem_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    gateway: AgentGateway = Depends(_dep_gateway),
) -> List[HintResponse]:
    """허용 단계 이하의 힌트 목록 반환."""
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문제를 찾을 수 없습니다.")

    progress = _get_or_create_progress(user_id, problem_id, db)
    allowed = progress.allowed_level

    all_hints = await _get_or_generate_hints(problem_id, problem, db, gateway)
    allowed_hints = [h for h in all_hints if h.level <= allowed]
    return [HintResponse.model_validate(h) for h in allowed_hints]


@router.post("/{problem_id}/unlock", response_model=HintProgressResponse)
def unlock_next_level(
    problem_id: str,
    body: HintUnlockRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> HintProgressResponse:
    """다음 단계 힌트 승급 — confirm=true 명시 필수 (FR-17, FR-18).

    프론트는 '다음 단계 힌트를 여시겠습니까?' 확인 모달 후 이 API를 호출한다.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="명시적 확인(confirm=true)이 필요합니다.",
        )

    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문제를 찾을 수 없습니다.")

    progress = _get_or_create_progress(user_id, problem_id, db)
    if progress.allowed_level >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 최고 단계(3단계) 힌트까지 허용되었습니다.",
        )

    progress.allowed_level += 1
    db.commit()
    return HintProgressResponse(problem_id=problem_id, allowed_level=progress.allowed_level)
