from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field
import csv
import io

from app.db.session import get_db
from app.models.models import User, Progress, QuizResult, Quiz, Lesson, StudentModel
from app.api.deps import get_current_user

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


class TestAnswer(BaseModel):
    question_id: int
    selected_index: int


class TestSubmit(BaseModel):
    test_type: str = Field(..., pattern="^(pre|post)$")
    answers: List[TestAnswer]
    time_spent_seconds: int = Field(default=0, ge=0)


class TestResultOut(BaseModel):
    test_type: str
    score: float
    correct_count: int
    total_questions: int
    knowledge_score: float
    attitude_score: Optional[float] = None
    message: str


# Pre/Post test questions (knowledge + attitude)
TEST_QUESTIONS = [
    # --- Knowledge (1-14) ---
    {
        "id": 1,
        "type": "mcq",
        "question": "A fitness influencer posts that one exercise burns more fat than anything else. She only shows her own results and follower comments, and she sells a related program. How should we treat this claim?",
        "options": [
            "It is definitely disinformation — she is lying to sell the program",
            "It is definitely misinformation — she just misunderstood the science",
            "We cannot know her intent, so treat the claim as unverified",
            "It is satire and not meant to be taken seriously",
        ],
        "correct_index": 2,
    },
    {
        "id": 2,
        "type": "mcq",
        "question": "Why do false or misleading claims often spread faster online than the corrections?",
        "options": [
            "Platforms remove corrections before they can spread",
            "False claims are usually simpler and more emotional, so people share them quickly",
            "Search engines rank false claims higher on purpose",
            "Most people fact-check before sharing, which slows false claims down",
        ],
        "correct_index": 1,
    },
    {
        "id": 3,
        "type": "mcq",
        "question": "A supplement claims it fully reverses hair loss and shows thousands of positive reviews on its own website. What is the biggest problem with this evidence?",
        "options": [
            "Customer reviews are always fake",
            "Reviews on the company’s own site mostly come from happy customers and are not independent tests",
            "Thousands of reviews are already strong enough proof",
            "The price of the product makes the claim more believable",
        ],
        "correct_index": 1,
    },
    {
        "id": 4,
        "type": "mcq",
        "question": "A student hears that final exams are postponed and shares it with friends without checking the university website. They say “everyone was talking about it so it must be true.” What best explains this?",
        "options": [
            "An official announcement had already confirmed it",
            "People often believe something just because many others are saying it",
            "The information was meant as a joke",
            "The student deliberately tried to trick their friends",
        ],
        "correct_index": 1,
    },
    {
        "id": 5,
        "type": "mcq",
        "question": "A short 12-second clip from a 40-minute political speech goes viral with the headline “Politician makes shocking statement.” Viewers cannot hear what was said before or after. What is the main problem?",
        "options": [
            "The headline is only clickbait",
            "Important context is missing, so the clip can be misleading",
            "The video itself has been digitally changed",
            "The video is a parody",
        ],
        "correct_index": 1,
    },
    {
        "id": 6,
        "type": "mcq",
        "question": "A blog post says “Drinking lemon water every morning boosts metabolism by 50%” but gives no study or source. What is the main issue?",
        "options": [
            "Context is missing from an otherwise good claim",
            "A specific number is given with no evidence at all",
            "The claim is meant as a joke",
            "The whole article was written by AI",
        ],
        "correct_index": 1,
    },
    {
        "id": 7,
        "type": "mcq",
        "question": "A verified public health agency publishes vaccination rates with a public dataset and clear methods. How should this be treated?",
        "options": [
            "As misinformation — health numbers are often manipulated",
            "As disinformation — government agencies usually have hidden motives",
            "As reliable information — the source and methods can be checked",
            "As something that can never be trusted without independent replication",
        ],
        "correct_index": 2,
    },
    {
        "id": 8,
        "type": "mcq",
        "question": "A clearly labelled satire site posts an exaggerated story. Someone screenshots it without the satire label and many people believe it is real news. How should we describe this?",
        "options": [
            "Original = misinformation, later spread = disinformation",
            "Original = satire, later spread = misinformation",
            "Original = disinformation, later spread = satire",
            "Original = clickbait, later spread = fabricated news",
        ],
        "correct_index": 1,
    },
    {
        "id": 9,
        "type": "mcq",
        "question": "Claim: “Students who sleep more get better grades.”\nEvidence: A controlled experiment randomly gave students either 8 or 5 hours of sleep for two weeks. The 8-hour group scored higher.\nHow well does the evidence support the claim?",
        "options": [
            "Strongly supports it",
            "Only weakly supports it (or is confounded)",
            "Is irrelevant",
            "Not enough information",
        ],
        "correct_index": 0,
    },
    {
        "id": 10,
        "type": "mcq",
        "question": "Same claim: “Students who sleep more get better grades.”\nEvidence: A survey found students with higher GPAs also sleep more, but those students also work fewer part-time hours.\nHow well does the evidence support the claim?",
        "options": [
            "Strongly supports it",
            "Only weakly supports it (or is confounded)",
            "Is irrelevant",
            "Not enough information",
        ],
        "correct_index": 1,
    },
    {
        "id": 11,
        "type": "mcq",
        "question": "Same claim: “Students who sleep more get better grades.”\nEvidence: A study found no link between sleep and grades among high-achieving students, but it only looked at that group.\nHow well does the evidence support the claim?",
        "options": [
            "Strongly supports it",
            "Only weakly supports it (or is confounded)",
            "Is irrelevant",
            "Not enough information",
        ],
        "correct_index": 1,
    },
    {
        "id": 12,
        "type": "mcq",
        "question": "Claim: “Students who exercise regularly concentrate better in class.”\nEvidence: A controlled experiment randomly assigned students to exercise or no-exercise groups. The exercise group scored higher on concentration tests.\nHow well does the evidence support the claim?",
        "options": [
            "Strongly supports it",
            "Only weakly supports it (or is confounded)",
            "Is irrelevant",
            "Not enough information",
        ],
        "correct_index": 0,
    },
    {
        "id": 13,
        "type": "mcq",
        "question": "Same claim: “Students who exercise regularly concentrate better in class.”\nEvidence: A survey found that students who exercise more also sleep better, which could explain the better concentration.\nHow well does the evidence support the claim?",
        "options": [
            "Strongly supports it",
            "Only weakly supports it (or is confounded)",
            "Is irrelevant",
            "Not enough information",
        ],
        "correct_index": 1,
    },
    {
        "id": 14,
        "type": "mcq",
        "question": "Same claim: “Students who exercise regularly concentrate better in class.”\nEvidence: A study found no link between exercise and concentration in students who already had high grades, but it excluded students with learning difficulties.\nHow well does the evidence support the claim?",
        "options": [
            "Strongly supports it",
            "Only weakly supports it (or is confounded)",
            "Is irrelevant",
            "Not enough information",
        ],
        "correct_index": 1,
    },
    # --- Attitude / self-efficacy (15-20) ---
    {
        "id": 15,
        "type": "likert",
        "question": "I feel confident identifying misinformation on social media.",
        "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
    },
    {
        "id": 16,
        "type": "likert",
        "question": "I know how to check whether a claim or news story is true before I trust it.",
        "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
    },
    {
        "id": 17,
        "type": "likert",
        "question": "I can explain why something might be misleading, not just guess.",
        "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
    },
    {
        "id": 18,
        "type": "likert",
        "question": "I think it is important to verify information before believing it.",
        "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
    },
    {
        "id": 19,
        "type": "likert",
        "question": "I want to get better at spotting misinformation.",
        "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
    },
    {
        "id": 20,
        "type": "likert",
        "question": "I believe misinformation is a serious problem that affects people like me.",
        "options": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
    },
]


@router.get("/test-questions")
async def get_test_questions(current_user: User = Depends(get_current_user)):
    safe = [
        {
            "id": q["id"],
            "type": q["type"],
            "question": q["question"],
            "options": q["options"],
        }
        for q in TEST_QUESTIONS
    ]
    return {
        "questions": safe,
        "total": len(safe),
        "knowledge_count": sum(1 for q in TEST_QUESTIONS if q["type"] == "mcq"),
        "likert_count": sum(1 for q in TEST_QUESTIONS if q["type"] == "likert"),
    }


@router.post("/submit-test", response_model=TestResultOut)
async def submit_test(
    payload: TestSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    answer_map = {a.question_id: a.selected_index for a in payload.answers}

    knowledge_qs = [q for q in TEST_QUESTIONS if q["type"] == "mcq"]
    likert_qs = [q for q in TEST_QUESTIONS if q["type"] == "likert"]

    correct = 0
    for q in knowledge_qs:
        if answer_map.get(q["id"]) == q["correct_index"]:
            correct += 1

    total = len(knowledge_qs)
    score = round((correct / total) * 100, 1) if total else 0.0

    likert_vals = []
    for q in likert_qs:
        idx = answer_map.get(q["id"])
        if idx is not None and 0 <= idx <= 4:
            likert_vals.append(idx + 1)

    attitude = round(sum(likert_vals) / len(likert_vals), 2) if likert_vals else None

    progress = Progress(
        user_id=current_user.id,
        lesson_id=None,
        score=score,
        time_spent_seconds=payload.time_spent_seconds,
        adaptive_action=f"{payload.test_type}_test",
        completed=True,
    )
    db.add(progress)

    if payload.test_type == "post":
        sm_result = await db.execute(
            select(StudentModel).where(StudentModel.user_id == current_user.id)
        )
        sm = sm_result.scalar_one_or_none()
        if sm:
            sm.recent_performance = score
            sm.last_activity = datetime.utcnow()

    await db.commit()

    msg = f"{payload.test_type.capitalize()}-test done. Score: {score}% ({correct}/{total})"
    if attitude is not None:
        msg += f". Average agreement: {attitude}/5"

    return TestResultOut(
        test_type=payload.test_type,
        score=score,
        correct_count=correct,
        total_questions=total,
        knowledge_score=score,
        attitude_score=attitude,
        message=msg,
    )


@router.get("/my-tests")
async def get_my_tests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Progress)
        .where(
            Progress.user_id == current_user.id,
            Progress.adaptive_action.in_(["pre_test", "post_test"]),
        )
        .order_by(desc(Progress.created_at))
    )
    items = result.scalars().all()
    return [
        {
            "test_type": p.adaptive_action,
            "score": p.score,
            "time_spent_seconds": p.time_spent_seconds,
            "created_at": p.created_at,
        }
        for p in items
    ]


@router.get("/export/csv")
async def export_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prog_result = await db.execute(
        select(Progress, Lesson)
        .outerjoin(Lesson, Progress.lesson_id == Lesson.id)
        .where(Progress.user_id == current_user.id)
        .order_by(Progress.created_at)
    )

    quiz_result = await db.execute(
        select(QuizResult, Quiz, Lesson)
        .join(Quiz, QuizResult.quiz_id == Quiz.id)
        .join(Lesson, Quiz.lesson_id == Lesson.id)
        .where(QuizResult.user_id == current_user.id)
        .order_by(QuizResult.created_at)
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["=== QUIZ RESULTS ==="])
    writer.writerow(["Lesson", "Score (%)", "Time (seconds)", "Date"])
    for qr, quiz, lesson in quiz_result.all():
        writer.writerow([
            lesson.title,
            qr.score,
            qr.time_spent_seconds,
            qr.created_at.isoformat() if qr.created_at else "",
        ])

    writer.writerow([])
    writer.writerow(["=== LEARNING ACTIVITY ==="])
    writer.writerow(["Lesson", "Score (%)", "Adaptive Action", "Time (seconds)", "Date"])
    for prog, lesson in prog_result.all():
        title = lesson.title if lesson else (prog.adaptive_action or "Activity")
        writer.writerow([
            title,
            prog.score if prog.score is not None else "",
            prog.adaptive_action or "",
            prog.time_spent_seconds,
            prog.created_at.isoformat() if prog.created_at else "",
        ])

    writer.writerow([])
    writer.writerow(["=== PRE / POST TESTS ==="])
    writer.writerow(["Test Type", "Knowledge Score (%)", "Time (seconds)", "Date"])
    test_result = await db.execute(
        select(Progress)
        .where(
            Progress.user_id == current_user.id,
            Progress.adaptive_action.in_(["pre_test", "post_test"]),
        )
        .order_by(Progress.created_at)
    )
    for p in test_result.scalars().all():
        writer.writerow([
            p.adaptive_action,
            p.score if p.score is not None else "",
            p.time_spent_seconds,
            p.created_at.isoformat() if p.created_at else "",
        ])

    output.seek(0)
    filename = f"adaptive_tutor_progress_{current_user.id}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )