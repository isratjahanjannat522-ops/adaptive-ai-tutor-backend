import React, { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { getMe } from "../services/api";

function getInitialTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") return saved;
  return "light";
}

/**
 * Optional prop: recommendedLessonId — when provided (e.g. from Dashboard),
 * "Lessons" navigates there instead of hardcoded /lesson/1.
 */
export default function Navbar({ recommendedLessonId }) {
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem("access_token");
  const [theme, setTheme] = useState(getInitialTheme);
  const [user, setUser] = useState(null);
  const [lessonLink, setLessonLink] = useState(
    recommendedLessonId ? `/lesson/${recommendedLessonId}` : "/lesson/1"
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!token) return;
    getMe()
      .then((res) => setUser(res.data))
      .catch(() => setUser(null));
  }, [token]);

  useEffect(() => {
    if (recommendedLessonId) {
      setLessonLink(`/lesson/${recommendedLessonId}`);
      try {
        localStorage.setItem(
          "recommended_lesson_id",
          String(recommendedLessonId)
        );
      } catch (_) {}
    } else {
      try {
        const saved = localStorage.getItem("recommended_lesson_id");
        if (saved) setLessonLink(`/lesson/${saved}`);
      } catch (_) {}
    }
  }, [recommendedLessonId]);

  const toggleTheme = () => {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("recommended_lesson_id");
    navigate("/login");
  };

  if (!token) return null;

  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  const isTeacher =
    user?.role === "teacher" || user?.role === "admin";

  return (
    <nav className="navbar">
      <Link to={isTeacher ? "/admin" : "/dashboard"} className="navbar-brand">
        Adaptive AI Tutor
      </Link>
      <div className="navbar-links">
        {!isTeacher && (
          <>
            <Link
              to="/dashboard"
              className={isActive("/dashboard") ? "active" : ""}
            >
              Dashboard
            </Link>
            <Link
              to={lessonLink}
              className={isActive("/lesson") ? "active" : ""}
            >
              Lessons
            </Link>
            <Link to="/chat" className={isActive("/chat") ? "active" : ""}>
              Chat
            </Link>
            <Link
              to="/exercises"
              className={isActive("/exercises") ? "active" : ""}
            >
              Exercises
            </Link>
            <Link
              to="/progress"
              className={isActive("/progress") ? "active" : ""}
            >
              Progress
            </Link>
            <Link
              to="/evaluation"
              className={isActive("/evaluation") ? "active" : ""}
            >
              Evaluation
            </Link>
          </>
        )}
        {isTeacher && (
          <Link to="/admin" className={isActive("/admin") ? "active" : ""}>
            Teacher
          </Link>
        )}
        <button type="button" className="theme-toggle" onClick={toggleTheme}>
          {theme === "light" ? "Dark" : "Light"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={logout}
          style={{ padding: "0.45rem 0.95rem", fontSize: "0.95rem" }}
        >
          Logout
        </button>
      </div>
    </nav>
  );
}