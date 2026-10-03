from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import StudentModel, StudentTopicMastery, Lesson, Topic
from app.agent.planner import AdaptivePlanner, StudentState, action_to_difficulty


class TutorAgent:
    def __init__(self):
        self.planner = AdaptivePlanner()

    async def get_student_state(
        self, db: AsyncSession, user_id: int, topic_id: int | None = None
    ) -> StudentState:
        # Overall student model
        result = await db.execute(
            select(StudentModel).where(StudentModel.user_id == user_id)
        )
        sm = result.scalar_one_or_none()

        mastery = 0.0
        confidence = 0.0
        learning_speed = 1.0
        recent_score = None

        if sm:
            mastery = sm.mastery_score or 0.0
            confidence = sm.confidence or 0.0
            learning_speed = sm.learning_speed or 1.0
            recent_score = sm.recent_performance

        # Prefer topic-level if available
        if topic_id:
            tm_result = await db.execute(
                select(StudentTopicMastery).where(
                    StudentTopicMastery.user_id == user_id,
                    StudentTopicMastery.topic_id == topic_id,
                )
            )
            tm = tm_result.scalar_one_or_none()
            if tm:
                mastery = tm.mastery
                confidence = tm.confidence
                learning_speed = tm.learning_speed
                recent_score = tm.recent_score

        confidence_gap = confidence - mastery

        return StudentState(
            mastery=mastery,
            confidence=confidence,
            learning_speed=learning_speed,
            recent_score=recent_score,
            confidence_gap=confidence_gap,
        )

    async def recommend(
        self, db: AsyncSession, user_id: int, lesson_id: int
    ) -> tuple[str, str, StudentState]:
        """
        Returns (adaptive_action, difficulty, state)
        """
        # Find topic of the lesson
        result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = result.scalar_one_or_none()
        topic_id = lesson.topic_id if lesson else None

        state = await self.get_student_state(db, user_id, topic_id)
        action = self.planner.choose(state)
        difficulty = action_to_difficulty(action)
        return action, difficulty, state