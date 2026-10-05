```markdown
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
(practice / teach / advance)
↓
Difficulty changes (moderate → standard → challenging)
↓
AI generates personalized lesson + feedback
↓
Score ≥ 90 → Option to jump to next chapter
```

## Complete Feature List

### Core
```
| Feature                             | Status |
| ----------------------------------- | ------ |
| User registration and login (JWT)   | ✅      |
| Adaptive AI lesson generation       | ✅      |
| Quiz generation + automatic grading | ✅      |
| Per-question answer explanations    | ✅      |
| Learning progress dashboard         | ✅      |
| Visual progress bars + score trend  | ✅      |
| Adaptive difficulty                 | ✅      |
| Learning path based on performance  | ✅      |
| Confidence tracking                 | ✅      |
| Personalized feedback               | ✅      |
| Admin / Teacher dashboard           | ✅      |
| Forced pre-test before Dashboard    | ✅      |
| Next Chapter unlock (score ≥ 90)    | ✅      |
```

### Extra (thesis standout)
```
| Feature                                   | Status |
| ----------------------------------------- | ------ |
| AI Chat Tutor (course-grounded)           | ✅      |
| Misinformation detection exercises        | ✅      |
| Daily study goals                         | ✅      |
| Spaced repetition review list             | ✅      |
| Pre-test / Post-test evaluation           | ✅      |
| CSV export of results                     | ✅      |
| Citation of course sources in chat        | ✅      |
| Explain why answers are correct/incorrect | ✅      |
| Domain-whitelisted email validation       | ✅      |
```

### Not included (intentionally)
```
| Feature                      | Reason                                                                                                                  |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Full PDF upload + vector RAG | Adds heavy dependencies (embeddings, vector DB). Can be future work. Current chat is grounded in seeded course content. |
| Social media monitoring      | Outside thesis scope (educational tutor, not detection platform).                                                       |
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), SQLite, JWT, OpenRouter, Resend
- **Frontend**: React 18, React Router, Axios, react-markdown
- **AI**: OpenRouter free model (configurable)

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # add OPENROUTER_API_KEY + RESEND_API_KEY
python -m uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm start
```

- Frontend: http://localhost:3000
- Swagger: http://127.0.0.1:8000/docs

## Pages

```
| Route       | Purpose                                                              |
| ----------- | -------------------------------------------------------------------- |
| /dashboard  | Stats, daily goal, recommended action, spaced review, Next Chapter   |
| /lesson/:id | Personalized AI lesson + quiz + explanations                         |
| /chat       | Open AI Chat Tutor                                                   |
| /exercises  | Interactive misinformation detection practice                        |
| /progress   | History, score charts, mastery bars                                  |
| /evaluation | Pre-test / Post-test + CSV export                                    |
| /admin      | Teacher view of all students                                         |
```

## Adaptive Policy (Updated)

Only three actions are used:

```
| Condition                                      | Action    | Difficulty   |
| ---------------------------------------------- | --------- | ------------ |
| recent_score ≥ 90                              | advance   | challenging  |
| mastery < 55  OR  recent_score < 70            | practice  | moderate     |
| mastery ≥ 85  AND  (recent_score ≥ 80 or None) | advance   | challenging  |
| everything else                                | teach     | standard     |
```

**Special behaviour:**
- When action = `advance` **and** a next chapter exists → Dashboard shows a clear “Go to Next Chapter →” button.
- Students who have never taken the pre-test are automatically redirected to `/evaluation` when they try to open the Dashboard.

## Thesis Evaluation Flow

1. Student is forced to take the **Pre-test** (Evaluation page)
2. Uses adaptive lessons + quizzes + detection exercises
3. Scores ≥ 90 unlock the option to jump to the next chapter
4. Takes **Post-test**
5. Compare scores + export CSV
6. Teacher view shows multiple students

## License

For academic use only.
```
