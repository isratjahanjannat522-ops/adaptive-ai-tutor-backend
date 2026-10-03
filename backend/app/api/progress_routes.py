from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.models import User, Progress, Lesson, QuizResult, Quiz
from app.api.deps import get_current_user

router = APIRouter(prefix="/progress", tags=["Progress"])


class ProgressItem(BaseModel):
    id: int
    lesson_id: Optional[int]
    lesson_title: str
    score: Optional[float]
    confidence: Optional[float]
    adaptive_action: Optional[str]
    time_spent_seconds: int
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QuizResultItem(BaseModel):
    id: int
    quiz_id: int
    lesson_id: int
    lesson_title: str
    score: float
    time_spent_seconds: int
    created_at: datetime


@router.get("/history", response_model=List[ProgressItem])
async def get_progress_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    result = await db.execute(
        select(Progress, Lesson)
        .outerjoin(Lesson, Progress.lesson_id == Lesson.id)
        .where(Progress.user_id == current_user.id)
        .order_by(desc(Progress.created_at))
        .limit(limit)
    )
    items = []
    for prog, lesson in result.all():
        title = lesson.title if lesson else (prog.adaptive_action or "Activity")
        items.append(
            ProgressItem(
                id=prog.id,
                lesson_id=prog.lesson_id,
                lesson_title=title,
                score=prog.score,
                confidence=prog.confidence,
                adaptive_action=prog.adaptive_action,
                time_spent_seconds=prog.time_spent_seconds,
                completed=prog.completed,
                created_at=prog.created_at,
            )
        )
    return items


@router.get("/quiz-results", response_model=List[QuizResultItem])
async def get_quiz_results(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    result = await db.execute(
        select(QuizResult, Quiz, Lesson)
        .join(Quiz, QuizResult.quiz_id == Quiz.id)
        .join(Lesson, Quiz.lesson_id == Lesson.id)
        .where(QuizResult.user_id == current_user.id)
        .order_by(desc(QuizResult.created_at))
        .limit(limit)
    )
    items = []
    for qr, quiz, lesson in result.all():
        items.append(
            QuizResultItem(
                id=qr.id,
                quiz_id=qr.quiz_id,
                lesson_id=lesson.id,
                lesson_title=lesson.title,
                score=qr.score,
                time_spent_seconds=qr.time_spent_seconds,
                created_at=qr.created_at,
            )
        )
    return items