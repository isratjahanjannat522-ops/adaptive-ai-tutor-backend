from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.session import get_db
from app.models.models import User, Progress, StudentTopicMastery, Topic
from app.api.deps import get_current_user

router = APIRouter(prefix="/goals", tags=["Study Goals & Spaced Repetition"])


class DailyGoalOut(BaseModel):
    date: str
    target_quizzes: int
    completed_quizzes: int
    target_minutes: int
    completed_minutes: int
    goal_met: bool
    message: str


class ReviewItem(BaseModel):
    topic_id: int
    topic_title: str
    mastery: float
    last_assessed: Optional[datetime]
    days_since_review: Optional[int]
    priority: str  # high | medium | low

@router.get("/daily", response_model=DailyGoalOut)
async def get_daily_goal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Daily study goal. Uses UTC so it matches how records are stored.
    Target: 1 quiz + 15 minutes.
    """
    from app.models.models import QuizResult

    # Use UTC for everything so it matches created_at
    now = datetime.utcnow()
    start = datetime(now.year, now.month, now.day)  # midnight UTC today

    # Count quizzes from QuizResult
    quiz_result = await db.execute(
        select(QuizResult).where(
            QuizResult.user_id == current_user.id,
            QuizResult.created_at >= start,
        )
    )
    today_quizzes = quiz_result.scalars().all()
    completed_quizzes = len(today_quizzes)

    # Minutes from Progress + quizzes
    prog_result = await db.execute(
        select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.created_at >= start,
        )
    )
    today_progress = prog_result.scalars().all()

    completed_minutes = (
        sum(p.time_spent_seconds for p in today_progress)
        + sum(q.time_spent_seconds for q in today_quizzes)
    ) // 60

    target_quizzes = 1
    target_minutes = 15
    goal_met = completed_quizzes >= target_quizzes and completed_minutes >= target_minutes

    if goal_met:
        msg = "Great work! You met today's study goal."
    elif completed_quizzes == 0:
        msg = "Take at least one quiz today to stay on track."
    else:
        msg = f"You have completed {completed_quizzes} quiz(es) and {completed_minutes} minutes. Keep going!"

    return DailyGoalOut(
        date=start.date().isoformat(),
        target_quizzes=target_quizzes,
        completed_quizzes=completed_quizzes,
        target_minutes=target_minutes,
        completed_minutes=completed_minutes,
        goal_met=goal_met,
        message=msg,
    )

@router.get("/review", response_model=List[ReviewItem])
async def get_spaced_review_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Simple spaced-repetition style review list.
    Topics with lower mastery or longer time since last assessment appear first.
    """
    result = await db.execute(
        select(StudentTopicMastery, Topic)
        .join(Topic, StudentTopicMastery.topic_id == Topic.id)
        .where(StudentTopicMastery.user_id == current_user.id)
    )

    items = []
    now = datetime.utcnow()
    for tm, topic in result.all():
        days = None
        if tm.last_assessed:
            days = (now - tm.last_assessed).days

        # Priority logic
        if tm.mastery < 50 or (days is not None and days >= 7):
            priority = "high"
        elif tm.mastery < 75 or (days is not None and days >= 3):
            priority = "medium"
        else:
            priority = "low"

        items.append(
            ReviewItem(
                topic_id=topic.id,
                topic_title=topic.title,
                mastery=tm.mastery,
                last_assessed=tm.last_assessed,
                days_since_review=days,
                priority=priority,
            )
        )

    # Sort: high priority first, then lower mastery
    priority_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda x: (priority_order[x.priority], x.mastery))
    return items