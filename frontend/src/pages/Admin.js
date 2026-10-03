import React, { useEffect, useState } from "react";
import { getStudents, getMe, createTeacher } from "../services/api";
import Navbar from "../components/Navbar";

export default function Admin() {
  const [students, setStudents] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Create teacher / admin form (admin only)
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    password: "",
    role: "teacher",
  });
  const [creating, setCreating] = useState(false);
  const [createMsg, setCreateMsg] = useState("");
  const [createError, setCreateError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [studentsRes, meRes] = await Promise.all([
          getStudents(),
          getMe(),
        ]);
        setStudents(studentsRes.data);
        setUser(meRes.data);
      } catch (err) {
        const status = err.response?.status;
        if (status === 403) {
          setError("Teachers and admins only. Log in with a teacher account.");
        } else if (status === 401) {
          setError("Please log in again.");
        } else {
          setError("Failed to load students.");
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const formatDate = (iso) => {
    if (!iso) return "Never";
    return new Date(iso).toLocaleString();
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateMsg("");
    setCreateError("");
    setCreating(true);
    try {
      await createTeacher(form);
      setCreateMsg(
        form.role === "admin"
          ? "Admin created successfully."
          : "Teacher created successfully."
      );
      setForm({ email: "", full_name: "", password: "", role: "teacher" });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setCreateError(
        typeof detail === "string"
          ? detail
          : "Failed to create user. Check email is unique and password is at least 8 characters."
      );
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div
            className="skeleton"
            style={{ height: 40, width: 250, marginBottom: 20 }}
          />
          <div className="skeleton" style={{ height: 250 }} />
        </div>
      </>
    );
  }

  const isAdmin = user?.role === "admin";

  return (
    <>
      <Navbar />
      <div className="container">
        <h1 style={{ fontSize: "1.6rem", marginBottom: "0.5rem" }}>
          Teacher View
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
          Overview of all registered students and their current learning state.
        </p>

        {error && <p className="error">{error}</p>}

        <div className="card">
          {students.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>
              No students registered yet.
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.95rem",
                }}
              >
                <thead>
                  <tr
                    style={{
                      borderBottom: "1px solid var(--border)",
                      textAlign: "left",
                    }}
                  >
                    <th style={{ padding: "0.6rem" }}>Name</th>
                    <th style={{ padding: "0.6rem" }}>Email</th>
                    <th style={{ padding: "0.6rem" }}>Mastery</th>
                    <th style={{ padding: "0.6rem" }}>Confidence</th>
                    <th style={{ padding: "0.6rem" }}>Speed</th>
                    <th style={{ padding: "0.6rem" }}>Recent Score</th>
                    <th style={{ padding: "0.6rem" }}>Assessments</th>
                    <th style={{ padding: "0.6rem" }}>Last Active</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr
                      key={s.user_id}
                      style={{ borderBottom: "1px solid var(--border)" }}
                    >
                      <td style={{ padding: "0.7rem", fontWeight: 500 }}>
                        {s.full_name}
                      </td>
                      <td
                        style={{ padding: "0.7rem", color: "var(--text-muted)" }}
                      >
                        {s.email}
                      </td>
                      <td
                        style={{
                          padding: "0.7rem",
                          fontWeight: 600,
                          color: "var(--primary)",
                        }}
                      >
                        {s.mastery_score.toFixed(0)}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {s.confidence.toFixed(0)}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {s.learning_speed.toFixed(2)}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {s.recent_performance.toFixed(0)}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {s.total_assessments}
                      </td>
                      <td
                        style={{
                          padding: "0.7rem",
                          color: "var(--text-muted)",
                          fontSize: "0.85rem",
                        }}
                      >
                        {formatDate(s.last_activity)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Admin-only: create teacher or another admin */}
        {isAdmin && (
          <div className="card" style={{ marginTop: "1.5rem" }}>
            <h2 style={{ fontSize: "1.2rem", marginBottom: "0.35rem" }}>
              Create teacher / admin
            </h2>
            <p
              style={{
                color: "var(--text-muted)",
                marginBottom: "1.25rem",
                fontSize: "0.95rem",
              }}
            >
              Only existing admins can create teachers or additional admins.
              Public registration is limited to students.
            </p>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="label">Full name</label>
                <input
                  className="input"
                  type="text"
                  value={form.full_name}
                  onChange={(e) =>
                    setForm({ ...form, full_name: e.target.value })
                  }
                  required
                  placeholder="Jane Teacher"
                />
              </div>

              <div className="form-group">
                <label className="label">Email</label>
                <input
                  className="input"
                  type="email"
                  value={form.email}
                  onChange={(e) =>
                    setForm({ ...form, email: e.target.value })
                  }
                  required
                  placeholder="teacher@example.com"
                />
              </div>

              <div className="form-group">
                <label className="label">Password (min 8 characters)</label>
                <input
                  className="input"
                  type="password"
                  value={form.password}
                  onChange={(e) =>
                    setForm({ ...form, password: e.target.value })
                  }
                  required
                  minLength={8}
                  placeholder="••••••••"
                />
              </div>

              <div className="form-group">
                <label className="label">Role</label>
                <select
                  className="input"
                  value={form.role}
                  onChange={(e) =>
                    setForm({ ...form, role: e.target.value })
                  }
                >
                  <option value="teacher">Teacher</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {createError && (
                <p className="error" style={{ marginBottom: "0.75rem" }}>
                  {createError}
                </p>
              )}
              {createMsg && (
                <p
                  className="success"
                  style={{ marginBottom: "0.75rem", color: "var(--success)" }}
                >
                  {createMsg}
                </p>
              )}

              <button
                type="submit"
                className="btn-primary"
                disabled={creating}
              >
                {creating ? "Creating…" : "Create user"}
              </button>
            </form>
          </div>
        )}
      </div>
    </>
  );
}