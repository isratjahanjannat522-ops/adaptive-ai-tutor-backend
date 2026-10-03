"""Recompute overall StudentModel from all topic masteries (average)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import StudentModel, StudentTopicMastery


async def recompute_overall_student_model(
    db: AsyncSession, user_id: int, sm: StudentModel | None = None
) -> StudentModel | None:
    if sm is None:
        result = await db.execute(
            select(StudentModel).where(StudentModel.user_id == user_id)
        )
        sm = result.scalar_one_or_none()
    if sm is None:
        return None

    tm_result = await db.execute(
        select(StudentTopicMastery).where(StudentTopicMastery.user_id == user_id)
    )
    topics = list(tm_result.scalars().all())
    if not topics:
        return sm

    n = len(topics)
    sm.mastery_score = sum(t.mastery for t in topics) / n
    sm.confidence = sum(t.confidence for t in topics) / n
    sm.learning_speed = sum(t.learning_speed for t in topics) / n
    # recent_performance stays the latest quiz/assessment score (set by caller)
    return sm