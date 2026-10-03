from datetime import datetime
from typing import Optional, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import (
    User,
    StudentModel,
    StudentTopicMastery,
    Lesson,
    Topic,
    Module,
    Course,
    Quiz,
    QuizResult,
    Progress,
)
from app.schemas.schemas import (
    StudentModelOut,
    TopicMasteryOut,
    AssessmentIn,
    AssessmentOut,
    RecommendationOut,
)
from app.api.deps import get_current_user
from app.agent.student_model import StudentModelUpdater, TopicEvidence
from app.agent.agent import TutorAgent
from app.agent.overall import recompute_overall_student_model

router = APIRouter(prefix="/student-model", tags=["Student Model"])

updater = StudentModelUpdater()
agent = TutorAgent()


# ---------------------------------------------------------------------------
# Helpers: next lesson without LLM
# ---------------------------------------------------------------------------

async def _ordered_lessons(db: AsyncSession) -> List[Tuple[Lesson, int]]:
    course_result = await db.execute(select(Course).where(Course.is_active == True))
    course = course_result.scalar_one_or_none()
    if not course:
        return []

    modules_result = await db.execute(
        select(Module)
        .where(Module.course_id == course.id)
        .order_by(Module.order_number)
    )
    ordered: List[Tuple[Lesson, int]] = []
    for mod in modules_result.scalars().all():
        topics_result = await db.execute(
            select(Topic)
            .where(Topic.module_id == mod.id)
            .order_by(Topic.order_number)
        )
        for topic in topics_result.scalars().all():
            lessons_result = await db.execute(
                select(Lesson)
                .where(Lesson.topic_id == topic.id)
                .order_by(Lesson.order_number)
            )
            for les in lessons_result.scalars().all():
                ordered.append((les, topic.id))
    return ordered


async def _completed_lesson_ids(db: AsyncSession, user_id: int) -> set:
    result = await db.execute(
        select(Quiz.lesson_id)
        .join(QuizResult, QuizResult.quiz_id == Quiz.id)
        .where(QuizResult.user_id == user_id)
        .distinct()
    )
    return set(result.scalars().all())


async def pick_next_lesson_id(
    db: AsyncSession, user_id: int
) -> Tuple[Optional[int], str]:
    """
    1. First lesson with no quiz completion (course order).
    2. Else first lesson with topic mastery < 70.
    3. Else last lesson (revisit / advance).
    """
    ordered = await _ordered_lessons(db)
    if not ordered:
        return None, "No lessons in course"

    completed = await _completed_lesson_ids(db, user_id)

    for lesson, _topic_id in ordered:
        if lesson.id not in completed:
            return lesson.id, "Next incomplete lesson in course order"

    tm_result = await db.execute(
        select(StudentTopicMastery).where(StudentTopicMastery.user_id == user_id)
    )
    mastery_by_topic = {tm.topic_id: tm.mastery for tm in tm_result.scalars().all()}

    weakest_id = None
    weakest_mastery = 101.0
    for lesson, topic_id in ordered:
        m = mastery_by_topic.get(topic_id, 0.0)
        if m < 70 and m < weakest_mastery:
            weakest_mastery = m
            weakest_id = lesson.id
    if weakest_id is not None:
        return weakest_id, f"Topic mastery still below 70 ({weakest_mastery:.0f})"

    last_lesson, _ = ordered[-1]
    return last_lesson.id, "All lessons completed; revisiting final lesson"


# ---------------------------------------------------------------------------
# NEW: fast recommendation for Dashboard (no LLM)
# ---------------------------------------------------------------------------

@router.get("/recommendation", response_model=RecommendationOut)
async def get_recommendation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Adaptive next-step for Dashboard.
    Picks lesson by progress + planner action/difficulty.
    NO LLM — only DB + deterministic AdaptivePlanner.
    """
    lesson_id, reason = await pick_next_lesson_id(db, current_user.id)
    if lesson_id is None:
        raise HTTPException(status_code=404, detail="No lessons available")

    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Recommended lesson not found")

    action, difficulty, state = await agent.recommend(db, current_user.id, lesson_id)

    return RecommendationOut(
        lesson_id=lesson.id,
        lesson_title=lesson.title,
        adaptive_action=action,
        difficulty=difficulty,
        mastery=round(state.mastery, 1),
        confidence=round(state.confidence, 1),
        learning_speed=round(state.learning_speed, 2),
        recent_score=round(state.recent_score or 0.0, 1),
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Existing endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=StudentModelOut)
async def get_student_model(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentModel).where(StudentModel.user_id == current_user.id)
    )
    sm = result.scalar_one_or_none()
    if not sm:
        raise HTTPException(status_code=404, detail="Student model not found")

    tm_result = await db.execute(
        select(StudentTopicMastery, Topic)
        .join(Topic, StudentTopicMastery.topic_id == Topic.id)
        .where(StudentTopicMastery.user_id == current_user.id)
    )
    topics = []
    for tm, topic in tm_result.all():
        topics.append(
            TopicMasteryOut(
                topic_id=topic.id,
                topic_title=topic.title,
                mastery=tm.mastery,
                confidence=tm.confidence,
                learning_speed=tm.learning_speed,
                recent_score=tm.recent_score,
                assessment_count=tm.assessment_count,
            )
        )

    return StudentModelOut(
        mastery_score=sm.mastery_score,
        confidence=sm.confidence,
        confidence_gap=sm.confidence - sm.mastery_score,
        learning_speed=sm.learning_speed,
        recent_performance=sm.recent_performance,
        current_lesson_id=sm.current_lesson_id,
        last_activity=sm.last_activity,
        topics=topics,
    )


@router.post("/assessment", response_model=AssessmentOut)
async def submit_assessment(
    payload: AssessmentIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lesson).where(Lesson.id == payload.lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    topic_id = lesson.topic_id

    tm_result = await db.execute(
        select(StudentTopicMastery).where(
            StudentTopicMastery.user_id == current_user.id,
            StudentTopicMastery.topic_id == topic_id,
        )
    )
    tm = tm_result.scalar_one_or_none()
    is_first = tm is None
    if is_first:
        tm = StudentTopicMastery(
            user_id=current_user.id,
            topic_id=topic_id,
            mastery=0.0,
            confidence=0.0,
            learning_speed=1.0,
        )
        db.add(tm)
        await db.flush()

    previous_mastery = tm.mastery
    evidence = TopicEvidence(
        score=payload.score,
        confidence=payload.confidence,
        time_spent_seconds=payload.time_spent_seconds,
    )

    new_mastery = updater.update_mastery(previous_mastery, evidence.score, is_first)
    new_confidence = updater.update_confidence(
        tm.confidence, evidence.confidence, is_first
    )
    mastery_gain = new_mastery - previous_mastery
    new_speed = updater.update_learning_speed(
        tm.learning_speed, mastery_gain, evidence.time_spent_seconds
    )

    tm.mastery = new_mastery
    tm.confidence = new_confidence
    tm.learning_speed = new_speed
    tm.recent_score = evidence.score
    tm.assessment_count += 1
    tm.total_learning_time += evidence.time_spent_seconds
    tm.last_assessed = datetime.utcnow()

    sm_result = await db.execute(
        select(StudentModel).where(StudentModel.user_id == current_user.id)
    )
    sm = sm_result.scalar_one_or_none()
    if sm:
        sm.recent_performance = evidence.score
        sm.current_lesson_id = payload.lesson_id
        sm.last_activity = datetime.utcnow()
        await recompute_overall_student_model(db, current_user.id, sm)

    # Recommend first, then write Progress with adaptive_action in ONE commit
    action, difficulty, _ = await agent.recommend(
        db, current_user.id, payload.lesson_id
    )

    progress = Progress(
        user_id=current_user.id,
        lesson_id=payload.lesson_id,
        score=payload.score,
        confidence=payload.confidence,
        time_spent_seconds=payload.time_spent_seconds,
        adaptive_action=action,
        completed=True,
    )
    db.add(progress)
    await db.commit()

    return AssessmentOut(
        message="Assessment recorded and student model updated.",
        new_mastery=round(new_mastery, 1),
        new_confidence=round(new_confidence, 1),
        adaptive_action=action,
        difficulty=difficulty,
    )