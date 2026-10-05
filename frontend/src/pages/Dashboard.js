import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  getMe,
  getStudentModel,
  getCourse,
  getRecommendation,
  getDailyGoal,
  getReviewItems,
  getMyTests,
} from "../services/api";
import Navbar from "../components/Navbar";

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [model, setModel] = useState(null);
  const [course, setCourse] = useState(null);
  const [nextAction, setNextAction] = useState(null);
  const [dailyGoal, setDailyGoal] = useState(null);
  const [reviewItems, setReviewItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Force pre-test for students
  useEffect(() => {
    async function check() {
      try {
        const me = await getMe();
        if (me.data.role !== "student") return;
        const tests = await getMyTests();
        const hasPreTest = tests.data.some((t) => t.test_type === "pre_test");
        if (!hasPreTest) {
          navigate("/evaluation", { replace: true });
        }
      } catch {
        // ignore
      }
    }
    check();
  }, [navigate]);

  useEffect(() => {
    async function load() {
      try {
        const [meRes, modelRes, courseRes, goalRes, reviewRes, recRes] =
          await Promise.all([
            getMe(),
            getStudentModel(),
            getCourse(),
            getDailyGoal(),
            getReviewItems(),
            getRecommendation(),
          ]);
        setUser(meRes.data);
        setModel(modelRes.data);
        setCourse(courseRes.data);
        setDailyGoal(goalRes.data);
        setReviewItems(reviewRes.data || []);
        if (recRes?.data) {
          setNextAction({
            lessonId: recRes.data.lesson_id,
            action: recRes.data.adaptive_action,
            difficulty: recRes.data.difficulty,
            lessonTitle: recRes.data.lesson_title,
            reason: recRes.data.reason,
          });
        }
      } catch (err) {
        setError("Failed to load dashboard data. Please log in again.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="skeleton" style={{ height: 40, width: 300, marginBottom: 20 }} />
          <div className="stats-grid">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton" style={{ height: 100 }} />
            ))}
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar />
        <div className="container">
          <p className="error">{error}</p>
          <Link to="/login">Go to Login</Link>
        </div>
      </>
    );
  }

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

  const recommendedLessonPath = nextAction?.lessonId
    ? `/lesson/${nextAction.lessonId}`
    : "/lesson/1";

  return (
    <>
      <Navbar recommendedLessonId={nextAction?.lessonId} />
      <div className="container">
        <h1 style={{ fontSize: "1.7rem", marginBottom: "0.3rem" }}>
          Hello, {user?.full_name}
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
          Course: <strong>{course?.title}</strong>
        </p>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{model?.mastery_score?.toFixed(0) ?? 0}</div>
            <div className="stat-label">Mastery</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{model?.confidence?.toFixed(0) ?? 0}</div>
            <div className="stat-label">Confidence</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {model?.learning_speed?.toFixed(2) ?? "1.00"}
            </div>
            <div className="stat-label">Learning Speed</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {model?.recent_performance?.toFixed(0) ?? 0}
            </div>
            <div className="stat-label">Recent Score</div>
          </div>
        </div>

        {dailyGoal && (
          <div className="card" style={{ marginTop: "1.25rem" }}>
            <h2 style={{ marginBottom: "0.6rem", fontSize: "1.15rem" }}>
              Today&apos;s Study Goal
            </h2>
            <p style={{ marginBottom: "0.5rem" }}>{dailyGoal.message}</p>
            <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
              <div>
                Quizzes: <strong>{dailyGoal.completed_quizzes}</strong> /{" "}
                {dailyGoal.target_quizzes}
              </div>
              <div>
                Minutes: <strong>{dailyGoal.completed_minutes}</strong> /{" "}
                {dailyGoal.target_minutes}
              </div>
              <div>
                Status:{" "}
                <strong
                  style={{
                    color: dailyGoal.goal_met
                      ? "var(--success)"
                      : "var(--warning)",
                  }}
                >
                  {dailyGoal.goal_met ? "Completed ✓" : "In progress"}
                </strong>
              </div>
            </div>
          </div>
        )}

        {nextAction && (
          <div
            className="card"
            style={{ marginTop: "1.25rem", borderColor: "var(--primary)" }}
          >
            <h2 style={{ marginBottom: "0.6rem", fontSize: "1.15rem" }}>
              Recommended Next Step
            </h2>
            <p style={{ marginBottom: "0.75rem" }}>
              Lesson: <strong>{nextAction.lessonTitle}</strong>
            </p>
            <p>
              Adaptive action:{" "}
              <span className={`badge ${badgeClass(nextAction.action)}`}>
                {nextAction.action.replace(/_/g, " ")}
              </span>{" "}
              → Difficulty: <strong>{nextAction.difficulty}</strong>
            </p>
            {nextAction.reason && (
              <p
                style={{
                  marginTop: "0.5rem",
                  color: "var(--text-muted)",
                  fontSize: "0.9rem",
                }}
              >
                Why: {nextAction.reason}
              </p>
            )}
            <Link
              to={recommendedLessonPath}
              className="btn-primary"
              style={{ display: "inline-block", marginTop: "1rem" }}
            >
              Start / Continue Lesson
            </Link>
          </div>
        )}

        {reviewItems.length > 0 && (
          <div className="card" style={{ marginTop: "1.25rem" }}>
            <h2 style={{ marginBottom: "0.75rem", fontSize: "1.15rem" }}>
              Topics to Review (Spaced Repetition)
            </h2>
            {reviewItems.slice(0, 5).map((item) => (
              <div
                key={item.topic_id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.5rem 0",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <span>{item.topic_title}</span>
                <span>
                  <span
                    className={`badge ${
                      item.priority === "high"
                        ? "badge-review"
                        : item.priority === "medium"
                        ? "badge-practice"
                        : "badge-teach"
                    }`}
                  >
                    {item.priority}
                  </span>{" "}
                  <span
                    style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}
                  >
                    mastery {item.mastery.toFixed(0)}%
                    {item.days_since_review != null &&
                      ` · ${item.days_since_review}d ago`}
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2 style={{ marginBottom: "1rem" }}>Course Modules</h2>
          {course?.modules?.map((mod) => (
            <div key={mod.id} style={{ marginBottom: "1.25rem" }}>
              <h3 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>
                Module {mod.order_number}: {mod.title}
              </h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem" }}>
                {mod.lessons?.map((les) => (
                  <Link
                    key={les.id}
                    to={`/lesson/${les.id}`}
                    className="btn-secondary"
                    style={{ fontSize: "0.9rem" }}
                  >
                    {les.title}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="card" style={{ marginTop: "1.25rem" }}>
          <h2 style={{ marginBottom: "0.75rem" }}>Quick Links</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
            <Link to="/chat" className="btn-secondary">
              AI Chat Tutor
            </Link>
            <Link to="/exercises" className="btn-secondary">
              Detection Exercises
            </Link>
            <Link to="/evaluation" className="btn-secondary">
              Pre / Post Test
            </Link>
            <Link to="/progress" className="btn-secondary">
              My Progress
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}