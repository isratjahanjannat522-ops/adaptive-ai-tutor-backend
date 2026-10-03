from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User, Progress, StudentModel
from app.llm.openrouter import generate_content

router = APIRouter(prefix="/exercises", tags=["Misinformation Exercises"])


class ClaimEvaluationRequest(BaseModel):
    claim: str = Field(..., min_length=10, max_length=1000)
    student_judgment: str = Field(..., pattern="^(true|false|unsure)$")
    student_reasoning: str = Field(..., min_length=5, max_length=1500)
    time_spent_seconds: int = Field(default=0, ge=0, le=86400)


class ClaimEvaluationResponse(BaseModel):
    feedback: str
    suggested_checks: List[str]
    confidence_note: str


class DetectionExercise(BaseModel):
    id: int
    claim: str
    context: str
    difficulty: str


DETECTION_EXERCISES = [
    {
        "id": 1,
        "claim": "A new study proves that drinking 3 cups of coffee daily completely prevents all forms of cancer.",
        "context": "Shared widely on social media with no link to the actual study.",
        "difficulty": "easy",
    },
    {
        "id": 2,
        "claim": "Government scientists have confirmed that 5G towers are the main cause of recent unusual weather patterns.",
        "context": "Posted by an anonymous account with dramatic images of storms.",
        "difficulty": "moderate",
    },
    {
        "id": 3,
        "claim": "A peer-reviewed paper published last month found a moderate association between prolonged social media use and increased anxiety symptoms in adolescents, after controlling for sleep and prior mental health.",
        "context": "Reported by a university press office with a link to the journal.",
        "difficulty": "challenging",
    },
    {
        "id": 4,
        "claim": "Breaking: Famous celebrity dies in car accident – confirmed by multiple eye witnesses on Twitter.",
        "context": "No major news outlets have reported it. The 'eye witnesses' are unverified accounts.",
        "difficulty": "moderate",
    },
    {
        "id": 5,
        "claim": "Eating carrots improves night vision dramatically because of high vitamin A content – this is why WWII pilots ate them.",
        "context": "A common belief that mixes a real nutrient fact with a historical myth used for propaganda.",
        "difficulty": "challenging",
    },
]


@router.get("/detection", response_model=List[DetectionExercise])
async def list_detection_exercises(current_user: User = Depends(get_current_user)):
    return [DetectionExercise(**ex) for ex in DETECTION_EXERCISES]


@router.post("/evaluate-claim", response_model=ClaimEvaluationResponse)
async def evaluate_claim(
    payload: ClaimEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Interactive misinformation detection exercise.
    Records Progress (no fake lesson_id) and updates last_activity.
    """
    prompt = f"""
You are an Adaptive AI Tutor helping a Higher Education student practice evaluating claims for misinformation.

Claim: "{payload.claim}"
Student judgment: {payload.student_judgment}
Student reasoning: "{payload.student_reasoning}"

Provide constructive, educational feedback. Structure your reply as:
1. Brief assessment of the student's judgment and reasoning (encourage good habits, gently correct weak ones).
2. Key issues with the claim (or why it may be credible).
3. What the student should check next.

Then list 3-5 concrete suggested checks the student should perform.
Finally give a short confidence note about how sure we can be.

Stay neutral and focus on evidence, source, context, and reasoning.
"""
    feedback = await generate_content(prompt)

    suggested = [
        "Identify the original source of the claim",
        "Check whether reliable outlets have reported the same information",
        "Look for the actual study, data, or primary document if one is mentioned",
        "Examine the date and whether context has been removed",
        "Notice emotional language and possible intent",
    ]
    confidence_note = (
        "Remember: high confidence should be backed by strong evidence. "
        "If evidence is weak or missing, lower your confidence and investigate further."
    )

    # Record activity (counts toward daily goal minutes; no fake lesson)
    progress = Progress(
        user_id=current_user.id,
        lesson_id=None,
        score=None,
        confidence=None,
        time_spent_seconds=payload.time_spent_seconds,
        adaptive_action="detection_exercise",
        completed=True,
    )
    db.add(progress)

    sm_result = await db.execute(
        select(StudentModel).where(StudentModel.user_id == current_user.id)
    )
    sm = sm_result.scalar_one_or_none()
    if sm:
        sm.last_activity = datetime.utcnow()

    await db.commit()

    return ClaimEvaluationResponse(
        feedback=feedback,
        suggested_checks=suggested,
        confidence_note=confidence_note,
    )