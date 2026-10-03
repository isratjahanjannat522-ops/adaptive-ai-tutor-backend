import React, { useEffect, useState } from "react";
import { getDetectionExercises, evaluateClaim } from "../services/api";
import Navbar from "../components/Navbar";

export default function Exercises() {
  const [startTime] = useState(Date.now());
  const [exercises, setExercises] = useState([]);
  const [selected, setSelected] = useState(null);
  const [judgment, setJudgment] = useState("unsure");
  const [reasoning, setReasoning] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await getDetectionExercises();
        setExercises(res.data);
      } catch (err) {
        setError("Failed to load exercises.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleEvaluate = async () => {
    if (!selected || reasoning.trim().length < 5) {
      setError("Please write a short reasoning (at least a few words).");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
        const res = await evaluateClaim({
        claim: selected.claim,
        student_judgment: judgment,
        student_reasoning: reasoning,
        time_spent_seconds: Math.round((Date.now() - startTime) / 1000) || 60,
      });
      setFeedback(res.data);
    } catch (err) {
      setError("Failed to get feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="skeleton" style={{ height: 40, width: 280, marginBottom: 20 }} />
          <div className="skeleton" style={{ height: 200 }} />
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container">
        <h1 style={{ fontSize: "1.5rem", marginBottom: "0.4rem" }}>
          Misinformation Detection Exercises
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
          Practice judging claims. Explain your reasoning and receive personalized feedback.
        </p>

        {error && <p className="error" style={{ marginBottom: "1rem" }}>{error}</p>}

        {!selected ? (
          <div className="card">
            <h2 style={{ marginBottom: "1rem", fontSize: "1.15rem" }}>Choose an exercise</h2>
            {exercises.map((ex) => (
              <button
                key={ex.id}
                className="quiz-option"
                style={{ marginBottom: "0.75rem" }}
                onClick={() => {
                  setSelected(ex);
                  setFeedback(null);
                  setReasoning("");
                  setJudgment("unsure");
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 4 }}>
                  Exercise {ex.id} · {ex.difficulty}
                </div>
                <div style={{ fontSize: "0.95rem" }}>{ex.claim}</div>
              </button>
            ))}
          </div>
        ) : (
          <div className="card">
            <button
              className="btn-secondary"
              style={{ marginBottom: "1rem", fontSize: "0.85rem" }}
              onClick={() => {
                setSelected(null);
                setFeedback(null);
              }}
            >
              ← Back to list
            </button>

            <h2 style={{ marginBottom: "0.5rem", fontSize: "1.15rem" }}>
              Claim to evaluate
            </h2>
            <p style={{ marginBottom: "0.75rem", fontWeight: 500 }}>{selected.claim}</p>
            <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1.25rem" }}>
              Context: {selected.context}
            </p>

            {!feedback ? (
              <>
                <div className="form-group">
                  <label className="label">Your judgment</label>
                  <select
                    className="input"
                    value={judgment}
                    onChange={(e) => setJudgment(e.target.value)}
                  >
                    <option value="true">Likely true / credible</option>
                    <option value="false">Likely false / misleading</option>
                    <option value="unsure">Unsure – need more evidence</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="label">Your reasoning</label>
                  <textarea
                    className="input"
                    rows={4}
                    value={reasoning}
                    onChange={(e) => setReasoning(e.target.value)}
                    placeholder="Explain why you think this claim is true, false, or uncertain..."
                  />
                </div>
                <button
                  className="btn-primary"
                  onClick={handleEvaluate}
                  disabled={submitting}
                >
                  {submitting ? "Getting feedback..." : "Submit for Feedback"}
                </button>
              </>
            ) : (
              <div>
                <h3 style={{ marginBottom: "0.75rem", color: "var(--primary)" }}>
                  Tutor Feedback
                </h3>
                <div
                  className="markdown-body"
                  style={{
                    whiteSpace: "pre-wrap",
                    marginBottom: "1.25rem",
                    lineHeight: 1.65,
                  }}
                >
                  {feedback.feedback}
                </div>

                <h4 style={{ marginBottom: "0.5rem" }}>Suggested checks</h4>
                <ul style={{ marginLeft: "1.25rem", marginBottom: "1rem" }}>
                  {feedback.suggested_checks.map((s, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>{s}</li>
                  ))}
                </ul>

                <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                  {feedback.confidence_note}
                </p>

                <button
                  className="btn-secondary"
                  style={{ marginTop: "1.25rem" }}
                  onClick={() => {
                    setSelected(null);
                    setFeedback(null);
                  }}
                >
                  Try another exercise
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
