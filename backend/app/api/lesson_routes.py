import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import User, Lesson, Course, Module, Topic
from app.schemas.schemas import GeneratedLessonOut, CourseOut, ModuleOut, LessonOut
from app.api.deps import get_current_user
from app.agent.agent import TutorAgent
from app.llm.openrouter import generate_lesson

router = APIRouter(tags=["Lessons & Course"])
agent = TutorAgent()

# In-memory lesson cache: key -> (content, unix_ts)
# Key = user_id:lesson_id:action:difficulty:mastery_bucket
_LESSON_CACHE: dict[str, tuple[str, float]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour


def _cache_key(
    user_id: int,
    lesson_id: int,
    action: str,
    difficulty: str,
    mastery: float,
) -> str:
    bucket = int(mastery // 10)  # 0..10
    return f"{user_id}:{lesson_id}:{action}:{difficulty}:{bucket}"


@router.get("/course", response_model=CourseOut)
async def get_course(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.is_active == True))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="No active course found")

    modules_result = await db.execute(
        select(Module).where(Module.course_id == course.id).order_by(Module.order_number)
    )
    modules = modules_result.scalars().all()
    module_outs = []
    for mod in modules:
        topics_result = await db.execute(
            select(Topic).where(Topic.module_id == mod.id).order_by(Topic.order_number)
        )
        topics = topics_result.scalars().all()
        lessons = []
        for topic in topics:
            lessons_result = await db.execute(
                select(Lesson).where(Lesson.topic_id == topic.id).order_by(Lesson.order_number)
            )
            for les in lessons_result.scalars().all():
                lessons.append(
                    LessonOut(
                        id=les.id,
                        title=les.title,
                        learning_objective=les.learning_objective,
                        order_number=les.order_number,
                        difficulty=les.difficulty,
                    )
                )
        module_outs.append(
            ModuleOut(
                id=mod.id,
                title=mod.title,
                order_number=mod.order_number,
                lessons=lessons,
            )
        )

    return CourseOut(
        id=course.id,
        title=course.title,
        description=course.description,
        modules=module_outs,
    )


@router.get("/lesson/{lesson_id}/generate", response_model=GeneratedLessonOut)
async def generate_personalized_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    action, difficulty, state = await agent.recommend(db, current_user.id, lesson_id)

    key = _cache_key(
        current_user.id, lesson_id, action, difficulty, state.mastery
    )
    now = time.time()
    cached = _LESSON_CACHE.get(key)
    if cached is not None:
        content, ts = cached
        if now - ts < _CACHE_TTL_SECONDS:
            return GeneratedLessonOut(
                lesson_id=lesson.id,
                lesson_title=lesson.title,
                adaptive_action=action,
                difficulty=difficulty,
                mastery=round(state.mastery, 1),
                confidence=round(state.confidence, 1),
                learning_speed=round(state.learning_speed, 2),
                recent_score=round(state.recent_score or 0.0, 1),
                content=content,
            )

    content = await generate_lesson(
        lesson_title=lesson.title,
        learning_objective=lesson.learning_objective,
        teaching_content=lesson.teaching_content,
        example_activity=lesson.example_activity,
        course_outcome=lesson.course_outcome,
        mastery=state.mastery,
        confidence=state.confidence,
        learning_speed=state.learning_speed,
        recent_score=state.recent_score or 0.0,
        adaptive_action=action,
        difficulty=difficulty,
    )
    _LESSON_CACHE[key] = (content, now)

    return GeneratedLessonOut(
        lesson_id=lesson.id,
        lesson_title=lesson.title,
        adaptive_action=action,
        difficulty=difficulty,
        mastery=round(state.mastery, 1),
        confidence=round(state.confidence, 1),
        learning_speed=round(state.learning_speed, 2),
        recent_score=round(state.recent_score or 0.0, 1),
        content=content,
    )