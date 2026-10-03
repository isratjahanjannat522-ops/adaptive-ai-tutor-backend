from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional
from app.db.session import get_db
from app.models.models import User, Lesson
from app.api.deps import get_current_user
from app.llm.openrouter import generate_content
from sqlalchemy import select

router = APIRouter(prefix="/chat", tags=["AI Chat Tutor"])


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    lesson_id: Optional[int] = None
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []


@router.post("", response_model=ChatResponse)
async def chat_with_tutor(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Open AI chat tutor grounded in the misinformation literacy course.
    Optionally focused on a specific lesson.
    """
    context = ""
    sources = []

    if payload.lesson_id:
        result = await db.execute(select(Lesson).where(Lesson.id == payload.lesson_id))
        lesson = result.scalar_one_or_none()
        if lesson:
            context = (
                f"Current lesson: {lesson.title}\n"
                f"Learning objective: {lesson.learning_objective}\n"
                f"Teaching content: {lesson.teaching_content}\n"
                f"Example activity: {lesson.example_activity}\n"
            )
            sources.append(f"Lesson: {lesson.title}")

    # Always include core course knowledge
    core_knowledge = """
Core course knowledge (Misinformation Literacy):
- Misinformation: false information shared without intent to deceive.
- Disinformation: false information shared with intent to deceive.
- Key evaluation criteria: source credibility, evidence quality, context, date, author, emotional language, purpose.
- Strong evidence is specific, verifiable, and comes from reliable sources.
- Prevention strategies: pause before sharing, check original source, look for corroboration, be aware of emotional triggers.
"""
    sources.append("Course core knowledge: Misinformation Literacy")

    history_text = ""
    for msg in payload.history[-6:]:  # last 6 messages for context
        history_text += f"{msg.role.upper()}: {msg.content}\n"

    prompt = f"""
You are a helpful Adaptive AI Tutor for Higher Education students learning misinformation literacy.
Stay neutral, evidence-focused, and educational. Do not be political.

{core_knowledge}

{context}

Conversation so far:
{history_text}

Student: {payload.message}

Reply clearly and helpfully. If relevant, explain concepts using the course knowledge above.
When you reference a concept, briefly mention the source (e.g. "According to the course material on source credibility...").
Keep answers concise but complete (under 300 words unless the student asks for more depth).
"""

    reply = await generate_content(prompt)
    return ChatResponse(reply=reply, sources=sources)