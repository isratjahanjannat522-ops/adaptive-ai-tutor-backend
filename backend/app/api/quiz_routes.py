import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import (
    User,
    Quiz,
    QuizResult,
    Lesson,
    StudentTopicMastery,
    StudentModel,
    Progress,
)
from app.schemas.schemas import (
    QuizOut,
    QuizQuestionPublic,
    QuizSubmitIn,
    QuizSubmitOut,
    QuizExplanation,
)
from app.agent.student_model import StudentModelUpdater
from app.agent.agent import TutorAgent
from app.agent.overall import recompute_overall_student_model


router = APIRouter(prefix="/quiz", tags=["Quiz"])
updater = StudentModelUpdater()
agent = TutorAgent()


@router.get("/lesson/{lesson_id}", response_model=QuizOut)
async def get_quiz_for_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quiz).where(Quiz.lesson_id == lesson_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this lesson")

    questions_data = json.loads(quiz.questions_json)
    # NEVER send correct_index to the client
    questions = [
        QuizQuestionPublic(
            id=q["id"],
            question=q["question"],
            options=q["options"],
        )
        for q in questions_data
    ]

    return QuizOut(
        quiz_id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        questions=questions,
    )


@router.post("/submit", response_model=QuizSubmitOut)
async def submit_quiz(
    payload: QuizSubmitIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quiz).where(Quiz.id == payload.quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = json.loads(quiz.questions_json)
    total = len(questions)
    correct = 0

    for q in questions:
        qid = str(q["id"])
        selected = payload.answers.get(qid)
        if selected is not None and int(selected) == q["correct_index"]:
            correct += 1

    score = round((correct / total) * 100, 1) if total > 0 else 0.0

    # Save quiz result
    qr = QuizResult(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=score,
        answers_json=json.dumps(payload.answers),
        time_spent_seconds=payload.time_spent_seconds,
    )
    db.add(qr)

    new_mastery = score
    action = "teach"
    difficulty = "standard"

    lesson_result = await db.execute(
        select(Lesson).where(Lesson.id == quiz.lesson_id)
    )
    lesson = lesson_result.scalar_one_or_none()
    topic_id = lesson.topic_id if lesson else None

    if topic_id:
        tm_result = await db.execute(
            select(StudentTopicMastery).where(
                StudentTopicMastery.user_id == current_user.id,
                StudentTopicMastery.topic_id == topic_id,
            )
        )
        tm = tm_result.scalar_one_or_none()
        is_first = tm is None

        if is_first:
            tm = StudentTopicMastery(
                user_id=current_user.id,
                topic_id=topic_id,
                mastery=0.0,
                confidence=0.0,
                learning_speed=1.0,
            )
            db.add(tm)
            await db.flush()

        previous_mastery = tm.mastery
        new_mastery = updater.update_mastery(previous_mastery, score, is_first)
        new_confidence = updater.update_confidence(
            tm.confidence, payload.confidence, is_first
        )
        mastery_gain = new_mastery - previous_mastery
        new_speed = updater.update_learning_speed(
            tm.learning_speed, mastery_gain, payload.time_spent_seconds
        )

        tm.mastery = new_mastery
        tm.confidence = new_confidence
        tm.learning_speed = new_speed
        tm.recent_score = score
        tm.assessment_count += 1
        tm.total_learning_time += payload.time_spent_seconds
        tm.last_assessed = datetime.utcnow()

        sm_result = await db.execute(
            select(StudentModel).where(StudentModel.user_id == current_user.id)
        )
        sm = sm_result.scalar_one_or_none()
        if sm:
            sm.recent_performance = score
            sm.current_lesson_id = quiz.lesson_id
            sm.last_activity = datetime.utcnow()
            await recompute_overall_student_model(db, current_user.id, sm)

        # Recommend BEFORE commit so adaptive_action is saved in the same transaction
        action, difficulty, _ = await agent.recommend(
            db, current_user.id, quiz.lesson_id
        )

        progress = Progress(
            user_id=current_user.id,
            lesson_id=quiz.lesson_id,
            score=score,
            confidence=payload.confidence,
            time_spent_seconds=payload.time_spent_seconds,
            adaptive_action=action,
            completed=True,
        )
        db.add(progress)

    await db.commit()

    # Build explanations (correct answers only AFTER submit)
    explanations = []
    for q in questions:
        qid = str(q["id"])
        selected = payload.answers.get(qid)
        is_correct = (
            selected is not None and int(selected) == q["correct_index"]
        )
        explanations.append(
            QuizExplanation(
                question_id=q["id"],
                question=q["question"],
                selected_index=int(selected) if selected is not None else None,
                correct_index=q["correct_index"],
                is_correct=is_correct,
                correct_option=q["options"][q["correct_index"]],
                explanation=(
                    f"Correct. The right answer is: {q['options'][q['correct_index']]}"
                    if is_correct
                    else (
                        f"Incorrect. The correct answer is: "
                        f"{q['options'][q['correct_index']]}. "
                        f"Review the lesson material on this concept."
                    )
                ),
            )
        )

    return QuizSubmitOut(
        score=score,
        correct_count=correct,
        total_questions=total,
        adaptive_action=action,
        difficulty=difficulty,
        new_mastery=round(new_mastery, 1),
        message=(
            f"You scored {score}%. Student model updated. "
            f"Next recommended action: {action} ({difficulty})."
        ),
        explanations=explanations,
    )