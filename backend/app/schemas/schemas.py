from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class UserCreate(BaseModel):
    """Public registration — students only. Role is NOT accepted from the client."""
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)


class AdminCreateUser(BaseModel):
    """Admin-only: create a teacher or another admin."""
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: Literal["teacher", "admin"] = "teacher"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Student Model ----------

class TopicMasteryOut(BaseModel):
    topic_id: int
    topic_title: str
    mastery: float
    confidence: float
    learning_speed: float
    recent_score: Optional[float]
    assessment_count: int

    class Config:
        from_attributes = True


class StudentModelOut(BaseModel):
    mastery_score: float
    confidence: float
    confidence_gap: float
    learning_speed: float
    recent_performance: float
    current_lesson_id: Optional[int]
    last_activity: Optional[datetime]
    topics: List[TopicMasteryOut] = []

    class Config:
        from_attributes = True


class AssessmentIn(BaseModel):
    lesson_id: int
    score: float = Field(ge=0, le=100)
    confidence: Optional[float] = Field(default=None, ge=0, le=100)
    time_spent_seconds: int = Field(default=0, ge=0, le=86400)


class AssessmentOut(BaseModel):
    message: str
    new_mastery: float
    new_confidence: float
    adaptive_action: str
    difficulty: str


# ---------- Recommendation (Dashboard, no LLM) ----------

class RecommendationOut(BaseModel):
    lesson_id: int
    lesson_title: str
    adaptive_action: str
    difficulty: str
    mastery: float
    confidence: float
    learning_speed: float
    recent_score: float
    reason: str = ""


# ---------- Course / Lesson ----------

class LessonOut(BaseModel):
    id: int
    title: str
    learning_objective: str
    order_number: int
    difficulty: str

    class Config:
        from_attributes = True


class ModuleOut(BaseModel):
    id: int
    title: str
    order_number: int
    lessons: List[LessonOut] = []

    class Config:
        from_attributes = True


class CourseOut(BaseModel):
    id: int
    title: str
    description: str
    modules: List[ModuleOut] = []

    class Config:
        from_attributes = True


# ---------- Adaptive / Lesson Generation ----------

class GeneratedLessonOut(BaseModel):
    lesson_id: int
    lesson_title: str
    adaptive_action: str
    difficulty: str
    mastery: float
    confidence: float
    learning_speed: float
    recent_score: float
    content: str  # markdown content from LLM


# ---------- Quiz ----------
# Public schema: NEVER expose correct_index to the client

class QuizQuestionPublic(BaseModel):
    id: int
    question: str
    options: List[str]


class QuizOut(BaseModel):
    quiz_id: int
    lesson_id: int
    title: str
    questions: List[QuizQuestionPublic]


class QuizSubmitIn(BaseModel):
    quiz_id: int
    answers: dict  # {question_id: selected_index}
    confidence: Optional[float] = Field(default=None, ge=0, le=100)
    time_spent_seconds: int = Field(default=0, ge=0, le=86400)


class QuizExplanation(BaseModel):
    question_id: int
    question: str
    selected_index: Optional[int]
    correct_index: int
    is_correct: bool
    correct_option: str
    explanation: str


class QuizSubmitOut(BaseModel):
    score: float
    correct_count: int
    total_questions: int
    adaptive_action: str
    difficulty: str
    new_mastery: float
    message: str
    explanations: List[QuizExplanation] = []