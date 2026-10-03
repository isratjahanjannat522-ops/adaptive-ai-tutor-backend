from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY or "dummy",
    base_url=settings.OPENROUTER_BASE_URL,
)


async def generate_content(prompt: str) -> str:
    """Simple generation helper."""
    if not settings.OPENROUTER_API_KEY:
        return (
            "## Learn\n"
            "This is a **placeholder lesson** because OPENROUTER_API_KEY is not set.\n\n"
            "## Example\n"
            "Example content would appear here.\n\n"
            "## Question\n"
            "What is the difference between misinformation and disinformation?\n\n"
            "## Practice\n"
            "Try evaluating a claim you saw recently.\n\n"
            "## Reflection\n"
            "How confident are you in your answer?\n\n"
            "## Summary\n"
            "Always check the source, evidence, and purpose of information."
        )

    response = await client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an Adaptive AI Tutor for Higher Education students. "
                    "You teach misinformation literacy. "
                    "Write clear, educational content in Markdown. "
                    "Never use political bias. Stay neutral and evidence-focused."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=1800,
    )
    return response.choices[0].message.content or "No content generated."


async def generate_lesson(
    lesson_title: str,
    learning_objective: str,
    teaching_content: str,
    example_activity: str,
    course_outcome: str,
    mastery: float,
    confidence: float,
    learning_speed: float,
    recent_score: float,
    adaptive_action: str,
    difficulty: str,
) -> str:
    """
    Generate a personalized lesson that respects the adaptive action and difficulty.
    """

    difficulty_instructions = {
        "easy": (
            "- Use simple language and short sentences.\n"
            "- Teach ONE concept at a time.\n"
            "- Give familiar, everyday examples.\n"
            "- Provide strong scaffolding and clear guidance.\n"
            "- Avoid ambiguous or tricky cases."
        ),
        "moderate": (
            "- Use normal academic language.\n"
            "- Include some independent reasoning.\n"
            "- Provide clear but not excessive guidance.\n"
            "- Use realistic examples."
        ),
        "standard": (
            "- Teach at normal university level.\n"
            "- Balance explanation and application.\n"
            "- Include both straightforward and slightly deeper points."
        ),
        "challenging": (
            "- Assume basic concepts are already understood.\n"
            "- Reduce unnecessary explanation.\n"
            "- Use more ambiguous, realistic scenarios.\n"
            "- Require deeper evidence-based reasoning.\n"
            "- Stay strictly within the learning objective."
        ),
        "easy_with_verification": (
            "- Use simplified language.\n"
            "- Explicitly distinguish evidence vs assumptions.\n"
            "- Guide the student to verify claims step by step.\n"
            "- Gently address possible overconfidence."
        ),
    }

    action_goal = {
        "review": "Help the student rebuild foundational understanding.",
        "practice": "Give the student focused practice to strengthen weak areas.",
        "teach": "Teach the next suitable concept clearly.",
        "advance": "Challenge the student with deeper reasoning and harder examples.",
        "verify_and_review": "Help the student verify their understanding and correct overconfidence.",
    }

    prompt = f"""
Create a personalized lesson for a Higher Education student on the topic of misinformation literacy.

LESSON TITLE: {lesson_title}
LEARNING OBJECTIVE: {learning_objective}
BASE TEACHING CONTENT: {teaching_content}
EXAMPLE ACTIVITY: {example_activity}
COURSE OUTCOME: {course_outcome}

STUDENT STATE:
- Mastery: {mastery:.1f}/100
- Confidence: {confidence:.1f}/100
- Learning speed: {learning_speed:.2f}
- Recent score: {recent_score:.1f}/100
- Adaptive action chosen by the tutor: {adaptive_action}
- Target difficulty: {difficulty}

GOAL OF THIS LESSON: {action_goal.get(adaptive_action, "Teach the concept.")}

DIFFICULTY RULES:
{difficulty_instructions.get(difficulty, difficulty_instructions["standard"])}

STRUCTURE YOUR RESPONSE EXACTLY LIKE THIS (use Markdown headings):

## Learn
(Clear explanation adapted to the difficulty)

## Example
(One concrete example that matches the difficulty)

## Question
(One thoughtful question for the student to think about)

## Practice
(A short practical activity)

## Reflection
(A short reflection prompt about confidence or evidence)

## Summary
(3-5 key takeaways)

Keep the tone professional, encouraging, and neutral. Do not mention the adaptive action or difficulty labels to the student.
"""

    return await generate_content(prompt)