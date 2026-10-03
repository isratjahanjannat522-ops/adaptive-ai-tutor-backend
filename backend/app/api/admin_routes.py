from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, hash_password
from app.db.session import get_db
from app.models.models import User, StudentModel, Progress
from app.schemas.schemas import AdminCreateUser, UserOut


router = APIRouter(prefix="/admin", tags=["Admin / Teacher"])


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
    """Strict: only role == 'admin'."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only",
        )
    return current_user


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
        count_result = await db.execute(
            select(func.count(Progress.id)).where(Progress.user_id == user.id)
        )
        total = count_result.scalar() or 0
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
            )
        )
    return students


@router.post(
    "/create-teacher",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_teacher(
    payload: AdminCreateUser,
    current_user: User = Depends(require_admin),  # ONLY existing admins
    db: AsyncSession = Depends(get_db),
):
    """
    Protected endpoint: only an existing admin can create teachers (or other admins).
    Use this from the UI after the first admin has been seeded/created.
    """
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
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user