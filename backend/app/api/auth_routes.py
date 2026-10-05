# app/api/auth_routes.py

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import settings
from app.db.session import get_db
from app.models.models import RefreshToken, StudentModel, User
from app.schemas.schemas import Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ------------------------------------------------------------------
# REGISTER (no email verification)
# ------------------------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == payload.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user already verified
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role="student",
        is_verified=True,          # ← already verified
        verification_token=None,
        verification_token_expires=None,
    )
    db.add(user)
    await db.flush()

    # Create student model
    student_model = StudentModel(user_id=user.id)
    db.add(student_model)

    await db.commit()
    await db.refresh(user)

    return {
        "message": "Registration successful. You can log in now.",
        "email": user.email,
    }

# ------------------------------------------------------------------
# LOGIN (no verification check)
# ------------------------------------------------------------------
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == form_data.username.lower())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # ← removed the is_verified check completely

    access = create_access_token(data={"sub": str(user.id)})
    refresh = create_refresh_token(data={"sub": str(user.id)})

    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_DAYS),
    )
    db.add(refresh_token)
    await db.commit()

    return Token(access_token=access, refresh_token=refresh)

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user