import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { generateLesson, getQuiz, submitQuiz } from "../services/api";
import Navbar from "../components/Navbar";

export default function Lesson() {
  const { lessonId } = useParams();
  const navigate = useNavigate();

  const [lesson, setLesson] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [showQuiz, setShowQuiz] = useState(false);
  const [startTime] = useState(Date.now());
  const [confidence, setConfidence] = useState(50);
  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      setResult(null);
      setShowQuiz(false);
      setAnswers({});
      try {
        const [lessonRes, quizRes] = await Promise.all([
          generateLesson(lessonId),
          getQuiz(lessonId),
        ]);
        setLesson(lessonRes.data);
        setQuiz(quizRes.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load lesson.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [lessonId]);

  const handleSelect = (qid, idx) => {
    if (result) return;
    setAnswers((prev) => ({ ...prev, [qid]: idx }));
  };

  const handleSubmitQuiz = async () => {
    if (!quiz) return;
    const total = quiz.questions.length;
    if (Object.keys(answers).length < total) {
      setError("Please answer all questions before submitting.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const timeSpent = Math.round((Date.now() - startTime) / 1000);
      const res = await submitQuiz({
        quiz_id: quiz.quiz_id,
        answers,
        confidence: confidence,
        time_spent_seconds: timeSpent,
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  const badgeClass = (action) => {
    const map = {
      review: "badge-review",
      practice: "badge-practice",
      teach: "badge-teach",
      advance: "badge-advance",
      verify_and_review: "badge-verify",
    };
    return map[action] || "badge-teach";
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="skeleton" style={{ height: 32, width: "60%", marginBottom: 16 }} />
          <div className="skeleton" style={{ height: 200, marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 120 }} />
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container">
        {error && <p className="error" style={{ marginBottom: "1rem" }}>{error}</p>}

        {lesson && (
          <>
            <div className="lesson-header">
              <h1 style={{ fontSize: "1.6rem" }}>{lesson.lesson_title}</h1>
              <div className="lesson-meta">
                <span className={`badge ${badgeClass(lesson.adaptive_action)}`}>
                  {lesson.adaptive_action.replace("_", " ")}
                </span>
                <span className="badge" style={{ background: "#1e293b", color: "#94a3b8" }}>
                  Difficulty: {lesson.difficulty}
                </span>
                <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                  Mastery {lesson.mastery} · Confidence {lesson.confidence} · Speed {lesson.learning_speed}
                </span>
              </div>
            </div>

            <div className="section-card markdown-body">
              <ReactMarkdown>{lesson.content}</ReactMarkdown>
            </div>

            {!showQuiz && !result && (
              <button
                className="btn-primary"
                onClick={() => setShowQuiz(true)}
                style={{ marginTop: "0.5rem" }}
              >
                Take Quiz
              </button>
            )}
          </>
        )}

        {showQuiz && quiz && !result && (
          <div className="card" style={{ marginTop: "1.5rem" }}>
            <h2 style={{ marginBottom: "1rem" }}>{quiz.title}</h2>
            {quiz.questions.map((q, i) => (
              <div key={q.id} style={{ marginBottom: "1.5rem" }}>
                <p style={{ fontWeight: 600, marginBottom: "0.6rem" }}>
                  {i + 1}. {q.question}
                </p>
                {q.options.map((opt, idx) => (
                  <button
                    key={idx}
                    className={`quiz-option ${answers[q.id] === idx ? "selected" : ""}`}
                    onClick={() => handleSelect(q.id, idx)}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            ))}
            {/* Confidence rating */}
<div style={{ marginBottom: "1.25rem" }}>
  <label style={{ fontWeight: 600, display: "block", marginBottom: "0.4rem" }}>
    How confident are you about your answers? ({confidence}%)
  </label>
  <input
    type="range"
    min="0"
    max="100"
    step="5"
    value={confidence}
    onChange={(e) => setConfidence(Number(e.target.value))}
    style={{ width: "100%", maxWidth: 320 }}
  />
  <div style={{ display: "flex", justifyContent: "space-between", maxWidth: 320, fontSize: "0.8rem", color: "var(--text-muted)" }}>
    <span>Not sure</span>
    <span>Very sure</span>
  </div>
</div>
            <button
              className="btn-primary"
              onClick={handleSubmitQuiz}
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Answers"}
            </button>
          </div>
        )}

        {result && (
          <div className="card" style={{ marginTop: "1.5rem" }}>
            <h2 style={{ marginBottom: "0.75rem" }}>Quiz Result</h2>
            <p style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--primary)" }}>
              Score: {result.score}% ({result.correct_count}/{result.total_questions})
            </p>
            <p style={{ marginTop: "0.75rem" }}>
              New mastery: <strong>{result.new_mastery}</strong>
            </p>
            <p style={{ marginTop: "0.4rem" }}>
              Next adaptive action:{" "}
              <span className={`badge ${badgeClass(result.adaptive_action)}`}>
                {result.adaptive_action.replace("_", " ")}
              </span>{" "}
              → difficulty: <strong>{result.difficulty}</strong>
            </p>
            <p style={{ marginTop: "0.75rem", color: "var(--text-muted)" }}>
              {result.message}
            </p>

            {result.explanations && result.explanations.length > 0 && (
              <div style={{ marginTop: "1.5rem" }}>
                <h3 style={{ marginBottom: "0.75rem", fontSize: "1.1rem" }}>
                  Answer Explanations
                </h3>
                {result.explanations.map((ex, i) => (
                  <div
                    key={ex.question_id}
                    style={{
                      marginBottom: "1rem",
                      padding: "0.9rem",
                      borderRadius: 8,
                      border: `1px solid ${ex.is_correct ? "var(--success)" : "var(--danger)"}`,
                      background: ex.is_correct
                        ? "rgba(34,197,94,0.08)"
                        : "rgba(239,68,68,0.08)",
                    }}
                  >
                    <p style={{ fontWeight: 600, marginBottom: 4 }}>
                      {i + 1}. {ex.question}
                    </p>
                    <p style={{ fontSize: "0.95rem" }}>{ex.explanation}</p>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: "1.25rem", display: "flex", gap: "0.75rem" }}>
              <button className="btn-primary" onClick={() => navigate("/dashboard")}>
                Back to Dashboard
              </button>
              <button
                className="btn-secondary"
                onClick={() => window.location.reload()}
              >
                Reload Lesson (see new adaptation)
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}