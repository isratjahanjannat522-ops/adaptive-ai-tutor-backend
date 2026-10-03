import json
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import Course, Module, Topic, Lesson, Quiz
from app.api.deps import hash_password
from app.models.models import User

async def seed_database():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Course))
        if result.scalar_one_or_none():
            return

        # ---------- Course ----------
        course = Course(
            title="Misinformation Literacy",
            description=(
                "An adaptive course that helps Higher Education students identify, "
                "evaluate, and prevent misinformation using evidence-based reasoning."
            ),
        )
        db.add(course)
        await db.flush()

        # ---------- Module 1 ----------
        mod1 = Module(
            course_id=course.id,
            title="Foundations of Misinformation",
            description="Core concepts and why false information spreads.",
            order_number=1,
        )
        db.add(mod1)
        await db.flush()

        topic1 = Topic(
            module_id=mod1.id,
            title="Understanding Misinformation",
            description="Definitions and basic distinctions.",
            order_number=1,
        )
        db.add(topic1)
        await db.flush()

        lesson1 = Lesson(
            topic_id=topic1.id,
            title="Understanding Misinformation",
            learning_objective=(
                "Students will be able to distinguish misinformation from disinformation "
                "and explain why false information spreads online."
            ),
            teaching_content=(
                "Misinformation is false or inaccurate information that is shared without "
                "intent to deceive. Disinformation is false information that is deliberately "
                "created or shared to mislead. Fake news is a common label but is often used "
                "too broadly. False information spreads because of emotional appeal, "
                "speed of social media, lack of verification habits, and cognitive biases."
            ),
            example_activity=(
                "Examine a social media post and decide whether it is more likely "
                "misinformation or disinformation, giving reasons."
            ),
            course_outcome=(
                "Students can accurately classify information and identify common "
                "reasons for the spread of false claims."
            ),
            order_number=1,
            difficulty="standard",
        )
        db.add(lesson1)
        await db.flush()

        # Quiz for Lesson 1
        questions = [
            {
                "id": 1,
                "question": "What is the main difference between misinformation and disinformation?",
                "options": [
                    "Misinformation is always intentional; disinformation is accidental",
                    "Misinformation is shared without intent to deceive; disinformation is deliberate",
                    "There is no difference",
                    "Disinformation only appears on television",
                ],
                "correct_index": 1,
            },
            {
                "id": 2,
                "question": "A person shares a false post because they genuinely believe it is true. Which category fits best?",
                "options": [
                    "Disinformation",
                    "Misinformation",
                    "Satire",
                    "Propaganda only",
                ],
                "correct_index": 1,
            },
            {
                "id": 3,
                "question": "Which factor can contribute to the spread of false information online?",
                "options": [
                    "Emotional language that triggers strong reactions",
                    "Always reading the full article before sharing",
                    "Checking the original source first",
                    "Waiting 24 hours before reacting",
                ],
                "correct_index": 0,
            },
            {
                "id": 4,
                "question": "When evaluating a surprising claim, what should a student examine first?",
                "options": [
                    "How many likes the post has",
                    "The source, evidence, and context",
                    "Whether their friends already shared it",
                    "The emotional tone only",
                ],
                "correct_index": 1,
            },
            {
                "id": 5,
                "question": "A post makes a strong claim but provides no evidence. What should the student do?",
                "options": [
                    "Share it immediately so others can see",
                    "Assume it is true because it looks professional",
                    "Treat it with caution and look for supporting evidence",
                    "Ignore all posts from that platform forever",
                ],
                "correct_index": 2,
            },
        ]

        quiz1 = Quiz(
            lesson_id=lesson1.id,
            title="Quiz: Understanding Misinformation",
            questions_json=json.dumps(questions),
        )
        db.add(quiz1)

        # ---------- Module 2 ----------
        mod2 = Module(
            course_id=course.id,
            title="Evaluating Information",
            description="Source credibility, evidence, and context.",
            order_number=2,
        )
        db.add(mod2)
        await db.flush()

        topic2 = Topic(
            module_id=mod2.id,
            title="Source Credibility & Evidence",
            description="How to evaluate sources and supporting evidence.",
            order_number=1,
        )
        db.add(topic2)
        await db.flush()

        lesson2 = Lesson(
            topic_id=topic2.id,
            title="Evaluating Sources and Evidence",
            learning_objective=(
                "Students will be able to assess source credibility and identify "
                "strong versus weak evidence for a claim."
            ),
            teaching_content=(
                "Credible sources usually have transparent authorship, editorial standards, "
                "and a track record of corrections. Strong evidence is specific, verifiable, "
                "and comes from primary or high-quality secondary sources. Weak evidence "
                "includes anonymous claims, emotional anecdotes without data, and "
                "unverified screenshots."
            ),
            example_activity=(
                "Compare two articles on the same topic and rank which provides stronger evidence."
            ),
            course_outcome=(
                "Students can justify credibility judgments using clear criteria."
            ),
            order_number=1,
            difficulty="standard",
        )
        db.add(lesson2)
        await db.flush()

        questions2 = [
            {
                "id": 1,
                "question": "Which of the following is generally a stronger indicator of source credibility?",
                "options": [
                    "High number of social media followers",
                    "Transparent authorship and clear editorial standards",
                    "Use of emotional language",
                    "Being the first to publish a claim",
                ],
                "correct_index": 1,
            },
            {
                "id": 2,
                "question": "What makes evidence stronger?",
                "options": [
                    "It is specific, verifiable, and from a reliable source",
                    "It uses many exclamation marks",
                    "It matches what the student already believes",
                    "It is shared by many friends",
                ],
                "correct_index": 0,
            },
            {
                "id": 3,
                "question": "An anonymous screenshot of a private chat is usually considered:",
                "options": [
                    "Strong primary evidence",
                    "Weak or unverifiable evidence",
                    "Official documentation",
                    "Peer-reviewed research",
                ],
                "correct_index": 1,
            },
            {
                "id": 4,
                "question": "Why is context important when evaluating a claim?",
                "options": [
                    "Context never matters",
                    "A true statement can be misleading if important context is removed",
                    "Context only matters for images",
                    "Context is only useful for historians",
                ],
                "correct_index": 1,
            },
            {
                "id": 5,
                "question": "What should a student do when a claim lacks supporting evidence?",
                "options": [
                    "Accept it if it feels true",
                    "Treat it cautiously and seek independent verification",
                    "Share it to get more opinions",
                    "Assume the opposite is true",
                ],
                "correct_index": 1,
            },
        ]

        quiz2 = Quiz(
            lesson_id=lesson2.id,
            title="Quiz: Evaluating Sources and Evidence",
            questions_json=json.dumps(questions2),
        )
        db.add(quiz2)

        # ---------- Module 3 ----------
        mod3 = Module(
            course_id=course.id,
            title="Prevention Strategies",
            description="Practical habits to reduce the spread of misinformation.",
            order_number=3,
        )
        db.add(mod3)
        await db.flush()

        topic3 = Topic(
            module_id=mod3.id,
            title="Stopping the Spread",
            description="Personal strategies and responsible sharing.",
            order_number=1,
        )
        db.add(topic3)
        await db.flush()

        lesson3 = Lesson(
            topic_id=topic3.id,
            title="Strategies to Prevent Misinformation",
            learning_objective=(
                "Students will be able to apply practical strategies that reduce "
                "the creation and spread of misinformation."
            ),
            teaching_content=(
                "Prevention includes pausing before sharing, checking the original source, "
                "looking for corroboration, being aware of emotional triggers, and "
                "correcting false information politely when appropriate. Universities "
                "and individuals both play roles in building information literacy."
            ),
            example_activity=(
                "Create a personal checklist for verifying information before sharing."
            ),
            course_outcome=(
                "Students develop a practical verification habit they can use daily."
            ),
            order_number=1,
            difficulty="standard",
        )
        db.add(lesson3)
        await db.flush()

        questions3 = [
            {
                "id": 1,
                "question": "What is a simple first step before sharing a surprising claim?",
                "options": [
                    "Share it immediately while it is trending",
                    "Pause and check the original source",
                    "Add an emotional comment",
                    "Tag as many friends as possible",
                ],
                "correct_index": 1,
            },
            {
                "id": 2,
                "question": "Why is emotional language a useful cue?",
                "options": [
                    "Emotional language always means the claim is true",
                    "Strong emotions can reduce careful thinking and increase sharing",
                    "Only professional journalists use emotional language",
                    "Emotional language has no effect on credibility",
                ],
                "correct_index": 1,
            },
            {
                "id": 3,
                "question": "What does corroboration mean in this context?",
                "options": [
                    "Finding the same claim repeated by many accounts without evidence",
                    "Finding independent, reliable sources that support the claim",
                    "Getting likes from friends",
                    "Translating the claim into another language",
                ],
                "correct_index": 1,
            },
            {
                "id": 4,
                "question": "When is it appropriate to correct misinformation?",
                "options": [
                    "Never – it is always rude",
                    "Politely and with evidence when the situation allows",
                    "Only by publicly shaming the person",
                    "Only if you are a professional fact-checker",
                ],
                "correct_index": 1,
            },
            {
                "id": 5,
                "question": "A good personal verification checklist should include:",
                "options": [
                    "Source, evidence, date, and possible emotional triggers",
                    "Only the number of shares",
                    "Whether the post matches your political views",
                    "How attractive the images are",
                ],
                "correct_index": 0,
            },
        ]

        quiz3 = Quiz(
            lesson_id=lesson3.id,
            title="Quiz: Prevention Strategies",
            questions_json=json.dumps(questions3),
        )
        db.add(quiz3)

        await db.commit()
        print("Database seeded successfully with Misinformation Literacy course.")
async def ensure_first_admin(db):
    result = await db.execute(select(User).where(User.role == "admin"))
    if result.scalar_one_or_none():
        return  # already have an admin

    admin = User(
        email="admin@example.com",
        full_name="System Admin",
        hashed_password=hash_password("ChangeMeNow123!"),
        role="admin",
        is_verified=True,  # admin is already verified
    )
    db.add(admin)
    await db.commit()
    print("First admin created: admin@example.com / ChangeMeNow123!")