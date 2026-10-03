import React, { useEffect, useState } from "react";
import { getProgressHistory, getQuizResults, getStudentModel } from "../services/api";
import Navbar from "../components/Navbar";

function ProgressBar({ value, max = 100, color = "var(--primary)" }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div style={{ background: "var(--bg)", borderRadius: 6, height: 10, overflow: "hidden" }}>
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          background: color,
          borderRadius: 6,
          transition: "width 0.4s ease",
        }}
      />
    </div>
  );
}

export default function Progress() {
  const [history, setHistory] = useState([]);
  const [quizResults, setQuizResults] = useState([]);
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [histRes, quizRes, modelRes] = await Promise.all([
          getProgressHistory(),
          getQuizResults(),
          getStudentModel(),
        ]);
        setHistory(histRes.data);
        setQuizResults(quizRes.data);
        setModel(modelRes.data);
      } catch (err) {
        setError("Failed to load progress history.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const badgeClass = (action) => {
    const map = {
      review: "badge-review",
      practice: "badge-practice",
      teach: "badge-teach",
      advance: "badge-advance",
      verify_and_review: "badge-verify",
      pre_test: "badge-teach",
      post_test: "badge-advance",
    };
    return map[action] || "badge-teach";
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleString();
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="skeleton" style={{ height: 40, width: 250, marginBottom: 20 }} />
          <div className="skeleton" style={{ height: 200 }} />
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container">
        <h1 style={{ fontSize: "1.6rem", marginBottom: "1.25rem" }}>My Progress</h1>

        {error && <p className="error">{error}</p>}

        {/* Visual summary */}
        {model && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ marginBottom: "1rem", fontSize: "1.15rem" }}>Current Learning State</h2>
            <div style={{ display: "grid", gap: "1rem" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span>Mastery</span>
                  <strong>{model.mastery_score?.toFixed(0)}%</strong>
                </div>
                <ProgressBar value={model.mastery_score} color="#3b82f6" />
              </div>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span>Confidence</span>
                  <strong>{model.confidence?.toFixed(0)}%</strong>
                </div>
                <ProgressBar value={model.confidence} color="#8b5cf6" />
              </div>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span>Recent Score</span>
                  <strong>{model.recent_performance?.toFixed(0)}%</strong>
                </div>
                <ProgressBar value={model.recent_performance} color="#22c55e" />
              </div>
            </div>
          </div>
        )}

        {/* Simple score trend (last quizzes) */}
        {quizResults.length > 0 && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ marginBottom: "1rem", fontSize: "1.15rem" }}>Recent Quiz Scores</h2>
            <div style={{ display: "flex", alignItems: "flex-end", gap: "0.75rem", height: 120 }}>
              {quizResults
                .slice()
                .reverse()
                .slice(-8)
                .map((r) => (
                  <div
                    key={r.id}
                    style={{
                      flex: 1,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      height: "100%",
                      justifyContent: "flex-end",
                    }}
                  >
                    <span style={{ fontSize: "0.75rem", marginBottom: 4 }}>{r.score}%</span>
                    <div
                      style={{
                        width: "100%",
                        maxWidth: 40,
                        height: `${Math.max(8, r.score)}%`,
                        background: r.score >= 70 ? "var(--success)" : r.score >= 50 ? "var(--warning)" : "var(--danger)",
                        borderRadius: "4px 4px 0 0",
                      }}
                    />
                  </div>
                ))}
            </div>
          </div>
        )}

        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ marginBottom: "1rem" }}>Quiz Results</h2>
          {quizResults.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No quizzes completed yet.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                    <th style={{ padding: "0.6rem" }}>Lesson</th>
                    <th style={{ padding: "0.6rem" }}>Score</th>
                    <th style={{ padding: "0.6rem" }}>Time</th>
                    <th style={{ padding: "0.6rem" }}>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {quizResults.map((r) => (
                    <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "0.7rem" }}>{r.lesson_title}</td>
                      <td style={{ padding: "0.7rem", fontWeight: 600, color: "var(--primary)" }}>
                        {r.score}%
                      </td>
                      <td style={{ padding: "0.7rem" }}>{r.time_spent_seconds}s</td>
                      <td style={{ padding: "0.7rem", color: "var(--text-muted)" }}>
                        {formatDate(r.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card">
          <h2 style={{ marginBottom: "1rem" }}>Learning Activity</h2>
          {history.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No activity recorded yet.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                    <th style={{ padding: "0.6rem" }}>Lesson</th>
                    <th style={{ padding: "0.6rem" }}>Score</th>
                    <th style={{ padding: "0.6rem" }}>Action</th>
                    <th style={{ padding: "0.6rem" }}>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "0.7rem" }}>{h.lesson_title}</td>
                      <td style={{ padding: "0.7rem" }}>
                        {h.score != null ? `${h.score}%` : "—"}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {h.adaptive_action ? (
                          <span className={`badge ${badgeClass(h.adaptive_action)}`}>
                            {h.adaptive_action.replace("_", " ")}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td style={{ padding: "0.7rem", color: "var(--text-muted)" }}>
                        {formatDate(h.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
