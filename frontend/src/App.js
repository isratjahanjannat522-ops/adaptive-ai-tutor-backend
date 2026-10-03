import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Lesson from "./pages/Lesson";
import Progress from "./pages/Progress";
import Admin from "./pages/Admin";
import Evaluation from "./pages/Evaluation";
import Chat from "./pages/Chat";
import Exercises from "./pages/Exercises";
import { getMe } from "./services/api";

function PrivateRoute({ children }) {
  const token = localStorage.getItem("access_token");
  return token ? children : <Navigate to="/login" replace />;
}

function TeacherRoute({ children }) {
  const token = localStorage.getItem("access_token");
  const [ok, setOk] = useState(null);

  useEffect(() => {
    if (!token) {
      setOk(false);
      return;
    }
    getMe()
      .then((res) => {
        setOk(res.data.role === "teacher" || res.data.role === "admin");
      })
      .catch(() => setOk(false));
  }, [token]);

  if (ok === null) return null; // brief wait while checking role
  if (!token || !ok) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/lesson/:lessonId"
        element={
          <PrivateRoute>
            <Lesson />
          </PrivateRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <PrivateRoute>
            <Chat />
          </PrivateRoute>
        }
      />
      <Route
        path="/exercises"
        element={
          <PrivateRoute>
            <Exercises />
          </PrivateRoute>
        }
      />
      <Route
        path="/progress"
        element={
          <PrivateRoute>
            <Progress />
          </PrivateRoute>
        }
      />
      <Route
        path="/evaluation"
        element={
          <PrivateRoute>
            <Evaluation />
          </PrivateRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <TeacherRoute>
            <Admin />
          </TeacherRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}