from datetime import datetime
from typing import List, Optional
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, hash_password
from app.db.session import get_db
from app.models.models import (
    User,
    StudentModel,
    Progress,
    QuizResult,
    Quiz,
    Lesson,
)
from app.schemas.schemas import AdminCreateUser, UserOut

router = APIRouter(prefix="/admin", tags=["Admin / Teacher"])


# ---------- Schemas ----------

class StudentSummary(BaseModel):
    user_id: int
    full_name: str
    email: str
    mastery_score: float
    confidence: float
    learning_speed: float
    recent_performance: float
    last_activity: Optional[datetime]
    total_assessments: int
    pre_test_score: Optional[float] = None
    post_test_score: Optional[float] = None
    total_time_seconds: int = 0


class QuizHistoryItem(BaseModel):
    quiz_id: int
    lesson_title: str
    score: float
    time_spent_seconds: int
    created_at: datetime


class ActivityItem(BaseModel):
    title: str
    score: Optional[float]
    adaptive_action: Optional[str]
    time_spent_seconds: int
    created_at: datetime


class StudentDetail(BaseModel):
    user_id: int
    full_name: str
    email: str
    mastery_score: float
    confidence: float
    learning_speed: float
    recent_performance: float
    last_activity: Optional[datetime]
    pre_test_score: Optional[float]
    post_test_score: Optional[float]
    total_time_seconds: int
    quiz_history: List[QuizHistoryItem]
    activity_history: List[ActivityItem]


# ---------- Auth helpers ----------

async def require_teacher_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers and admins only",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only",
        )
    return current_user


# ---------- List students (richer summary) ----------

@router.get("/students", response_model=List[StudentSummary])
async def list_students(
    current_user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User, StudentModel)
        .outerjoin(StudentModel, User.id == StudentModel.user_id)
        .where(User.role == "student")
        .order_by(User.full_name)
    )

    students = []
    for user, sm in result.all():
        # assessment count
        count_result = await db.execute(
            select(func.count(Progress.id)).where(Progress.user_id == user.id)
        )
        total = count_result.scalar() or 0

        # pre / post scores (latest of each)
        pre_score = None
        post_score = None
        tests = await db.execute(
            select(Progress)
            .where(
                Progress.user_id == user.id,
                Progress.adaptive_action.in_(["pre_test", "post_test"]),
            )
            .order_by(desc(Progress.created_at))
        )
        for p in tests.scalars().all():
            if p.adaptive_action == "pre_test" and pre_score is None:
                pre_score = p.score
            if p.adaptive_action == "post_test" and post_score is None:
                post_score = p.score

        # total time (progress + quizzes)
        time_prog = await db.execute(
            select(func.coalesce(func.sum(Progress.time_spent_seconds), 0)).where(
                Progress.user_id == user.id
            )
        )
        time_quiz = await db.execute(
            select(func.coalesce(func.sum(QuizResult.time_spent_seconds), 0)).where(
                QuizResult.user_id == user.id
            )
        )
        total_time = int(time_prog.scalar() or 0) + int(time_quiz.scalar() or 0)

        students.append(
            StudentSummary(
                user_id=user.id,
                full_name=user.full_name,
                email=user.email,
                mastery_score=sm.mastery_score if sm else 0.0,
                confidence=sm.confidence if sm else 0.0,
                learning_speed=sm.learning_speed if sm else 1.0,
                recent_performance=sm.recent_performance if sm else 0.0,
                last_activity=sm.last_activity if sm else None,
                total_assessments=total,
                pre_test_score=pre_score,
                post_test_score=post_score,
                total_time_seconds=total_time,
            )
        )
    return students


# ---------- Single student detail (quiz history + activity) ----------

@router.get("/students/{user_id}", response_model=StudentDetail)
async def get_student_detail(
    user_id: int,
    current_user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User, StudentModel)
        .outerjoin(StudentModel, User.id == StudentModel.user_id)
        .where(User.id == user_id, User.role == "student")
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")

    user, sm = row

    # pre / post
    pre_score = None
    post_score = None
    tests = await db.execute(
        select(Progress)
        .where(
            Progress.user_id == user.id,
            Progress.adaptive_action.in_(["pre_test", "post_test"]),
        )
        .order_by(desc(Progress.created_at))
    )
    for p in tests.scalars().all():
        if p.adaptive_action == "pre_test" and pre_score is None:
            pre_score = p.score
        if p.adaptive_action == "post_test" and post_score is None:
            post_score = p.score

    # total time
    time_prog = await db.execute(
        select(func.coalesce(func.sum(Progress.time_spent_seconds), 0)).where(
            Progress.user_id == user.id
        )
    )
    time_quiz = await db.execute(
        select(func.coalesce(func.sum(QuizResult.time_spent_seconds), 0)).where(
            QuizResult.user_id == user.id
        )
    )
    total_time = int(time_prog.scalar() or 0) + int(time_quiz.scalar() or 0)

    # quiz history
    quiz_rows = await db.execute(
        select(QuizResult, Quiz, Lesson)
        .join(Quiz, QuizResult.quiz_id == Quiz.id)
        .join(Lesson, Quiz.lesson_id == Lesson.id)
        .where(QuizResult.user_id == user.id)
        .order_by(desc(QuizResult.created_at))
        .limit(50)
    )
    quiz_history = [
        QuizHistoryItem(
            quiz_id=qr.quiz_id,
            lesson_title=lesson.title,
            score=qr.score,
            time_spent_seconds=qr.time_spent_seconds,
            created_at=qr.created_at,
        )
        for qr, quiz, lesson in quiz_rows.all()
    ]

    # activity history
    act_rows = await db.execute(
        select(Progress, Lesson)
        .outerjoin(Lesson, Progress.lesson_id == Lesson.id)
        .where(Progress.user_id == user.id)
        .order_by(desc(Progress.created_at))
        .limit(50)
    )
    activity_history = []
    for prog, lesson in act_rows.all():
        title = lesson.title if lesson else (prog.adaptive_action or "Activity")
        activity_history.append(
            ActivityItem(
                title=title,
                score=prog.score,
                adaptive_action=prog.adaptive_action,
                time_spent_seconds=prog.time_spent_seconds,
                created_at=prog.created_at,
            )
        )

    return StudentDetail(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        mastery_score=sm.mastery_score if sm else 0.0,
        confidence=sm.confidence if sm else 0.0,
        learning_speed=sm.learning_speed if sm else 1.0,
        recent_performance=sm.recent_performance if sm else 0.0,
        last_activity=sm.last_activity if sm else None,
        pre_test_score=pre_score,
        post_test_score=post_score,
        total_time_seconds=total_time,
        quiz_history=quiz_history,
        activity_history=activity_history,
    )


# ---------- Export ALL students as CSV ----------

@router.get("/export/csv")
async def export_all_students_csv(
    current_user: User = Depends(require_teacher_or_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User, StudentModel)
        .outerjoin(StudentModel, User.id == StudentModel.user_id)
        .where(User.role == "student")
        .order_by(User.full_name)
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "User ID",
            "Full Name",
            "Email",
            "Mastery",
            "Confidence",
            "Learning Speed",
            "Recent Score",
            "Pre-test Score",
            "Post-test Score",
            "Total Time (seconds)",
            "Total Assessments",
            "Last Active",
        ]
    )

    for user, sm in result.all():
        pre_score = None
        post_score = None
        tests = await db.execute(
            select(Progress)
            .where(
                Progress.user_id == user.id,
                Progress.adaptive_action.in_(["pre_test", "post_test"]),
            )
            .order_by(desc(Progress.created_at))
        )
        for p in tests.scalars().all():
            if p.adaptive_action == "pre_test" and pre_score is None:
                pre_score = p.score
            if p.adaptive_action == "post_test" and post_score is None:
                post_score = p.score

        count_result = await db.execute(
            select(func.count(Progress.id)).where(Progress.user_id == user.id)
        )
        total = count_result.scalar() or 0

        time_prog = await db.execute(
            select(func.coalesce(func.sum(Progress.time_spent_seconds), 0)).where(
                Progress.user_id == user.id
            )
        )
        time_quiz = await db.execute(
            select(func.coalesce(func.sum(QuizResult.time_spent_seconds), 0)).where(
                QuizResult.user_id == user.id
            )
        )
        total_time = int(time_prog.scalar() or 0) + int(time_quiz.scalar() or 0)

        writer.writerow(
            [
                user.id,
                user.full_name,
                user.email,
                round(sm.mastery_score, 1) if sm else 0,
                round(sm.confidence, 1) if sm else 0,
                round(sm.learning_speed, 2) if sm else 1.0,
                round(sm.recent_performance, 1) if sm else 0,
                pre_score if pre_score is not None else "",
                post_score if post_score is not None else "",
                total_time,
                total,
                sm.last_activity.isoformat() if sm and sm.last_activity else "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=all_students_data.csv"
        },
    )


# ---------- Create teacher / admin (admin only) ----------

@router.post(
    "/create-teacher",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_teacher(
    payload: AdminCreateUser,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == payload.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if payload.role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'teacher' or 'admin'",
        )

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user