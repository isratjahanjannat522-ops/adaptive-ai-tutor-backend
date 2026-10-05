import React, { useEffect, useState, useRef, useCallback } from "react";
import { getTestQuestions, submitTest, getMyTests, exportCsv } from "../services/api";
import Navbar from "../components/Navbar";

const TIME_LIMIT_SECONDS = 10 * 60; // 10 minutes

export default function Evaluation() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [testType, setTestType] = useState("pre");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [pastTests, setPastTests] = useState([]);
  const [error, setError] = useState("");
  const [meta, setMeta] = useState({ knowledge_count: 14, likert_count: 6 });

  // Timer state
  const [timeLeft, setTimeLeft] = useState(TIME_LIMIT_SECONDS);
  const [startTime, setStartTime] = useState(null);
  const timerRef = useRef(null);
  const hasSubmittedRef = useRef(false);

  // Format mm:ss
  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // Submit function (used by button + auto-submit)
  const doSubmit = useCallback(
    async (force = false) => {
      if (hasSubmittedRef.current || submitting) return;
      hasSubmittedRef.current = true;

      if (!force && Object.keys(answers).length < questions.length) {
        setError("Please answer all questions.");
        hasSubmittedRef.current = false;
        return;
      }

      setSubmitting(true);
      setError("");

      // Clear timer
      if (timerRef.current) clearInterval(timerRef.current);

      try {
        const spent = startTime
          ? Math.round((Date.now() - startTime) / 1000)
          : TIME_LIMIT_SECONDS - timeLeft;

        const payload = {
          test_type: testType,
          answers: Object.entries(answers).map(([qid, idx]) => ({
            question_id: parseInt(qid),
            selected_index: idx,
          })),
          time_spent_seconds: Math.min(spent, TIME_LIMIT_SECONDS),
        };

        const res = await submitTest(payload);
        setResult(res.data);

        const tRes = await getMyTests();
        setPastTests(tRes.data || []);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to submit test.");
        hasSubmittedRef.current = false;
      } finally {
        setSubmitting(false);
      }
    },
    [answers, questions, testType, startTime, timeLeft, submitting]
  );

  // Load questions
  useEffect(() => {
    async function load() {
      try {
        const [qRes, tRes] = await Promise.all([getTestQuestions(), getMyTests()]);
        setQuestions(qRes.data.questions || []);
        setMeta({
          knowledge_count: qRes.data.knowledge_count ?? 14,
          likert_count: qRes.data.likert_count ?? 6,
        });
        setPastTests(tRes.data || []);

        // Start the 10-minute timer only after questions load
        setStartTime(Date.now());
        setTimeLeft(TIME_LIMIT_SECONDS);
      } catch (err) {
        setError("Failed to load evaluation data.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Countdown timer
  useEffect(() => {
    if (!startTime || result) return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          // Auto-submit when time runs out
          doSubmit(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [startTime, result, doSubmit]);

  const handleSelect = (qid, idx) => {
    if (result || timeLeft === 0) return;
    setAnswers((prev) => ({ ...prev, [qid]: idx }));
  };

  const handleSubmit = () => doSubmit(false);

  const handleExport = async () => {
    try {
      const res = await exportCsv();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "adaptive_tutor_progress.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError("Export failed.");
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="skeleton" style={{ height: 40, width: 280, marginBottom: 20 }} />
          <div className="skeleton" style={{ height: 300 }} />
        </div>
      </>
    );
  }

  const knowledgeQs = questions.filter((q) => q.type === "mcq" || !q.type);
  const likertQs = questions.filter((q) => q.type === "likert");

  // Timer color
  const timerColor =
    timeLeft <= 60 ? "#ef4444" : timeLeft <= 180 ? "#f59e0b" : "var(--primary)";

  return (
    <>
      <Navbar />
      <div className="container">
        <h1 style={{ fontSize: "1.6rem", marginBottom: "0.4rem" }}>
          Pre-test / Post-test
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
          Same test before and after using the tutor so you can measure change.
          You have <strong>10 minutes</strong>.
        </p>

        {error && (
          <p className="error" style={{ marginBottom: "1rem" }}>
            {error}
          </p>
        )}

        {pastTests.length > 0 && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ marginBottom: "0.75rem", fontSize: "1.15rem" }}>
              Previous results
            </h2>
            <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
              {pastTests.map((t, i) => (
                <div key={i} className="stat-card" style={{ minWidth: 140 }}>
                  <div className="stat-value" style={{ fontSize: "1.4rem" }}>
                    {t.score}%
                  </div>
                  <div className="stat-label">
                    {t.test_type === "pre_test" ? "Pre-test" : "Post-test"}
                  </div>
                </div>
              ))}
            </div>
            {pastTests.some((t) => t.test_type === "pre_test") &&
              pastTests.some((t) => t.test_type === "post_test") && (
                <p style={{ marginTop: "1rem", color: "var(--success)" }}>
                  Both pre and post scores are available for comparison.
                </p>
              )}
          </div>
        )}

        <div style={{ marginBottom: "1.5rem" }}>
          <button className="btn-secondary" onClick={handleExport}>
            Download results as CSV
          </button>
        </div>

        {!result ? (
          <div className="card">
            {/* Sticky timer bar */}
            <div
              style={{
                position: "sticky",
                top: 0,
                zIndex: 10,
                background: "var(--card-bg, #fff)",
                padding: "0.75rem 0",
                marginBottom: "1.25rem",
                borderBottom: "1px solid var(--border, #e5e7eb)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "0.75rem",
              }}
            >
              <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                <label style={{ fontWeight: 600 }}>Test type:</label>
                <select
                  className="input"
                  style={{ width: "auto" }}
                  value={testType}
                  onChange={(e) => setTestType(e.target.value)}
                  disabled={timeLeft === 0}
                >
                  <option value="pre">Pre-test (before using the tutor)</option>
                  <option value="post">Post-test (after using the tutor)</option>
                </select>
              </div>

              <div
                style={{
                  fontSize: "1.4rem",
                  fontWeight: 700,
                  color: timerColor,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                ⏱ {formatTime(timeLeft)}
              </div>
            </div>

            <p
              style={{
                color: "var(--text-muted)",
                marginBottom: "1.25rem",
                fontSize: "0.95rem",
              }}
            >
              Answer all {questions.length} questions. First {meta.knowledge_count} are
              multiple choice. Last {meta.likert_count} ask how much you agree.
            </p>

            {knowledgeQs.length > 0 && (
              <>
                <h3 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
                  Questions 1–{knowledgeQs.length}
                </h3>
                {knowledgeQs.map((q, i) => (
                  <div key={q.id} style={{ marginBottom: "1.75rem" }}>
                    <p
                      style={{
                        fontWeight: 600,
                        marginBottom: "0.6rem",
                        whiteSpace: "pre-line",
                        lineHeight: 1.5,
                      }}
                    >
                      {i + 1}. {q.question}
                    </p>
                    {q.options.map((opt, idx) => (
                      <button
                        key={idx}
                        className={`quiz-option ${
                          answers[q.id] === idx ? "selected" : ""
                        }`}
                        onClick={() => handleSelect(q.id, idx)}
                        style={{ textAlign: "left" }}
                        disabled={timeLeft === 0}
                      >
                        <span style={{ fontWeight: 600, marginRight: 6 }}>
                          {String.fromCharCode(97 + idx)}.
                        </span>
                        {opt}
                      </button>
                    ))}
                  </div>
                ))}
              </>
            )}

            {likertQs.length > 0 && (
              <>
                <h3
                  style={{
                    fontSize: "1.1rem",
                    marginTop: "1.5rem",
                    marginBottom: "1rem",
                  }}
                >
                  Questions {knowledgeQs.length + 1}–{questions.length}
                </h3>
                <p
                  style={{
                    color: "var(--text-muted)",
                    marginBottom: "1rem",
                    fontSize: "0.9rem",
                  }}
                >
                  How much do you agree? (1 = Strongly Disagree, 5 = Strongly Agree)
                </p>
                {likertQs.map((q, i) => (
                  <div key={q.id} style={{ marginBottom: "1.75rem" }}>
                    <p style={{ fontWeight: 600, marginBottom: "0.6rem" }}>
                      {knowledgeQs.length + i + 1}. {q.question}
                    </p>
                    <div
                      style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}
                    >
                      {q.options.map((opt, idx) => (
                        <button
                          key={idx}
                          className={`quiz-option ${
                            answers[q.id] === idx ? "selected" : ""
                          }`}
                          onClick={() => handleSelect(q.id, idx)}
                          style={{
                            flex: "1 1 120px",
                            minWidth: 100,
                            textAlign: "center",
                            padding: "0.6rem 0.5rem",
                            fontSize: "0.85rem",
                          }}
                          disabled={timeLeft === 0}
                        >
                          <div style={{ fontWeight: 700, marginBottom: 2 }}>
                            {idx + 1}
                          </div>
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </>
            )}

            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={submitting || timeLeft === 0}
              style={{ marginTop: "0.5rem" }}
            >
              {submitting
                ? "Submitting..."
                : timeLeft === 0
                ? "Time's up – submitting..."
                : `Submit ${testType === "pre" ? "Pre-test" : "Post-test"}`}
            </button>
          </div>
        ) : (
          <div className="card">
            <h2 style={{ marginBottom: "0.75rem" }}>
              {result.test_type === "pre" ? "Pre-test" : "Post-test"} result
            </h2>
            <p
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: "var(--primary)",
              }}
            >
              Score: {result.knowledge_score ?? result.score}% (
              {result.correct_count}/{result.total_questions})
            </p>
            {result.attitude_score != null && (
              <p style={{ fontSize: "1.15rem", marginTop: "0.5rem" }}>
                Average agreement: {result.attitude_score} / 5
              </p>
            )}
            <p style={{ marginTop: "0.75rem", color: "var(--text-muted)" }}>
              {result.message}
            </p>
            <button
              className="btn-secondary"
              style={{ marginTop: "1.25rem" }}
              onClick={() => {
                setResult(null);
                setAnswers({});
                hasSubmittedRef.current = false;
                setStartTime(Date.now());
                setTimeLeft(TIME_LIMIT_SECONDS);
              }}
            >
              Take another test
            </button>
          </div>
        )}
      </div>
    </>
  );
}