# Adaptive AI Tutor – Misinformation Literacy

**Final-year BSc thesis prototype**

An intelligent adaptive learning system (not just a chatbot) that personalizes instruction on misinformation literacy using a measurable student model.

## Core Adaptive Loop

```
Student activity → Assessment / Quiz
        ↓
Student Model updated (mastery, confidence, learning speed)
        ↓
Adaptive Planner decides next action
  (review / practice / teach / advance / verify_and_review)
        ↓
Difficulty changes (easy → challenging)
        ↓
AI generates personalized lesson + feedback
```

## Complete Feature List

### Core
| Feature | Status |
|---------|--------|
| User registration and login (JWT) | ✅ |
| Adaptive AI lesson generation | ✅ |
| Quiz generation + automatic grading | ✅ |
| Per-question answer explanations | ✅ |
| Learning progress dashboard | ✅ |
| Visual progress bars + score trend | ✅ |
| Adaptive difficulty | ✅ |
| Learning path based on performance | ✅ |
| Confidence tracking | ✅ |
| Personalized feedback | ✅ |
| Admin / Teacher dashboard | ✅ |

### Extra (thesis standout)
| Feature | Status |
|---------|--------|
| AI Chat Tutor (course-grounded) | ✅ |
| Misinformation detection exercises | ✅ |
| Daily study goals | ✅ |
| Spaced repetition review list | ✅ |
| Pre-test / Post-test evaluation | ✅ |
| CSV export of results | ✅ |
| Citation of course sources in chat | ✅ |
| Explain why answers are correct/incorrect | ✅ |

### Not included (intentionally)
| Feature | Reason |
|---------|--------|
| Full PDF upload + vector RAG | Adds heavy dependencies (embeddings, vector DB). Can be future work. Current chat is grounded in seeded course content. |
| Social media monitoring | Outside thesis scope (educational tutor, not detection platform). |

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), SQLite, JWT, OpenRouter
- **Frontend**: React 18, React Router, Axios, react-markdown
- **AI**: OpenRouter free model (configurable)

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # add OPENROUTER_API_KEY
python -m uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm start
```

- Frontend: http://localhost:3000
- Swagger:  http://127.0.0.1:8000/docs

## Pages

| Route | Purpose |
|-------|---------|
| /dashboard | Stats, daily goal, recommended action, spaced review |
| /lesson/:id | Personalized AI lesson + quiz + explanations |
| /chat | Open AI Chat Tutor |
| /exercises | Interactive misinformation detection practice |
| /progress | History, score charts, mastery bars |
| /evaluation | Pre-test / Post-test + CSV export |
| /admin | Teacher view of all students |

## Adaptive Policy

```
confidence_gap >= 20     → verify_and_review (easy_with_verification)
mastery < 50             → review (easy)
recent_score < 70        → practice (moderate)
mastery >= 85 & score >= 85 → advance (challenging)
else                     → teach (standard)
```

## Thesis Evaluation Flow

1. Student takes **Pre-test** (Evaluation page)
2. Uses adaptive lessons + quizzes + detection exercises
3. Takes **Post-test**
4. Compare scores + export CSV
5. Teacher view shows multiple students

## License

For academic use only.
