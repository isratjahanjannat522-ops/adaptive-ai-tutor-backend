# app/api/auth_routes.py

from datetime import datetime, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.utils.email import send_verification_email
from app.utils.email_validation import is_email_deliverable
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
# Helper: auto-delete unverified accounts older than 10 minutes
# ------------------------------------------------------------------
async def cleanup_expired_unverified_users(db: AsyncSession) -> None:
    cutoff = datetime.utcnow() - timedelta(minutes=10)

    result = await db.execute(
        select(User.id).where(
            User.is_verified == False,
            User.created_at < cutoff,
        )
    )
    expired_ids = [row[0] for row in result.all()]

    if not expired_ids:
        return

    # Delete related records first
    await db.execute(delete(StudentModel).where(StudentModel.user_id.in_(expired_ids)))
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id.in_(expired_ids)))
    await db.execute(delete(User).where(User.id.in_(expired_ids)))
    await db.commit()
    print(f"🧹 Auto-deleted {len(expired_ids)} unverified account(s) older than 10 min")


# ------------------------------------------------------------------
# REGISTER
# ------------------------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    await cleanup_expired_unverified_users(db)

    is_valid, error_msg = is_email_deliverable(payload.email)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,  # always "email does not exist"
        )

    result = await db.execute(
        select(User).where(User.email == payload.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=10)

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role="student",
        is_verified=False,
        verification_token=token,
        verification_token_expires=expires,
    )
    db.add(user)
    await db.flush()

    student_model = StudentModel(user_id=user.id)
    db.add(student_model)

    await db.commit()
    await db.refresh(user)

    email_sent = await send_verification_email(user.email, token)

    verification_link = f"{settings.BACKEND_URL}/api/v1/auth/verify-email?token={token}"
    print("\n" + "=" * 70)
    print("EMAIL VERIFICATION LINK (expires in 10 minutes):")
    print(verification_link)
    print("=" * 70 + "\n")

    message = (
        "Registration successful. Please check your email and verify within 10 minutes."
        if email_sent
        else "Registration successful, but we could not send the email. "
             
    )

    return {
        "message": message,
        "email": user.email,
    }


# ------------------------------------------------------------------
# VERIFY EMAIL
# ------------------------------------------------------------------
@router.get("/verify-email")
async def verify_email(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    await cleanup_expired_unverified_users(db)

    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please register again or request a new link.",
        )

    if user.is_verified:
        return {"message": "Email already verified. You can log in now."}

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    await db.commit()

    return {"message": "Email verified successfully! You can now log in."}


# ------------------------------------------------------------------
# RESEND VERIFICATION
# ------------------------------------------------------------------
class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/resend-verification")
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend verification email and reset the 10-minute timer.
    Only works for unverified accounts that still exist.
    """
    await cleanup_expired_unverified_users(db)

    result = await db.execute(
        select(User).where(User.email == payload.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal whether the email exists or not
        return {
            "message": "If this email is registered and not yet verified, a new verification link has been sent."
        }

    if user.is_verified:
        return {
            "message": "This email is already verified. You can log in."
        }

    # Generate new token + reset 10-minute window
    new_token = secrets.token_urlsafe(32)
    user.verification_token = new_token
    user.verification_token_expires = datetime.utcnow() + timedelta(minutes=10)
    await db.commit()

    email_sent = await send_verification_email(user.email, new_token)

    verification_link = f"{settings.BACKEND_URL}/api/v1/auth/verify-email?token={new_token}"
    print("\n" + "=" * 70)
    print("RESENT VERIFICATION LINK (expires in 10 minutes):")
    print(verification_link)
    print("=" * 70 + "\n")

    if email_sent:
        return {
            "message": "A new verification link has been sent. Please check your inbox (expires in 10 minutes)."
        }
    else:
        return {
            "message": "Could not send email. Please check the server terminal for the new link."
        }


# ------------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------------
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    await cleanup_expired_unverified_users(db)

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

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. "
                   "You can request a new verification link at /auth/resend-verification",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

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