from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="student")  # student | teacher | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    verification_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student_model: Mapped[Optional["StudentModel"]] = relationship(back_populates="user", uselist=False)
    progress_records: Mapped[list["Progress"]] = relationship(back_populates="user")
    quiz_results: Mapped[list["QuizResult"]] = relationship(back_populates="user")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    modules: Mapped[list["Module"]] = relationship(back_populates="course", order_by="Module.order_number")


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    order_number: Mapped[int] = mapped_column(Integer, default=1)

    course: Mapped["Course"] = relationship(back_populates="modules")
    topics: Mapped[list["Topic"]] = relationship(back_populates="module", order_by="Topic.order_number")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    order_number: Mapped[int] = mapped_column(Integer, default=1)

    module: Mapped["Module"] = relationship(back_populates="topics")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="topic", order_by="Lesson.order_number")
    student_masteries: Mapped[list["StudentTopicMastery"]] = relationship(back_populates="topic")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    learning_objective: Mapped[str] = mapped_column(Text, default="")
    teaching_content: Mapped[str] = mapped_column(Text, default="")  # base curriculum content
    example_activity: Mapped[str] = mapped_column(Text, default="")
    course_outcome: Mapped[str] = mapped_column(Text, default="")
    order_number: Mapped[int] = mapped_column(Integer, default=1)
    difficulty: Mapped[str] = mapped_column(String(50), default="standard")  # easy | moderate | standard | challenging

    topic: Mapped["Topic"] = relationship(back_populates="lessons")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="lesson")


class StudentModel(Base):
    __tablename__ = "student_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    current_module_id: Mapped[Optional[int]] = mapped_column(ForeignKey("modules.id"), nullable=True)
    current_lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lessons.id"), nullable=True)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)          # overall 0-100
    learning_speed: Mapped[float] = mapped_column(Float, default=1.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)             # 0-100
    recent_performance: Mapped[float] = mapped_column(Float, default=0.0)    # last score
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="student_model")


class StudentTopicMastery(Base):
    __tablename__ = "student_topic_masteries"
    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    mastery: Mapped[float] = mapped_column(Float, default=0.0)               # 0-100
    confidence: Mapped[float] = mapped_column(Float, default=0.0)             # 0-100
    learning_speed: Mapped[float] = mapped_column(Float, default=1.0)
    recent_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assessment_count: Mapped[int] = mapped_column(Integer, default=0)
    total_learning_time: Mapped[int] = mapped_column(Integer, default=0)     # seconds
    last_assessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    topic: Mapped["Topic"] = relationship(back_populates="student_masteries")


class Progress(Base):
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Nullable: pre/post tests and exercises are not tied to a lesson
    lesson_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lessons.id"), index=True, nullable=True
    )
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    adaptive_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="progress_records")


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Lesson Quiz")
    questions_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of questions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lesson: Mapped["Lesson"] = relationship(back_populates="quizzes")
    results: Mapped[list["QuizResult"]] = relationship(back_populates="quiz")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)              # 0-100
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="quiz_results")
    quiz: Mapped["Quiz"] = relationship(back_populates="results")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)