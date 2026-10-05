import React, { useEffect, useState } from "react";
import {
  getStudents,
  getMe,
  createTeacher,
  getStudentDetail,
  exportAllStudentsCsv,
} from "../services/api";
import Navbar from "../components/Navbar";

export default function Admin() {
  const [students, setStudents] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // detail panel
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // create form
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
        const [studentsRes, meRes] = await Promise.all([getStudents(), getMe()]);
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

  const formatMinutes = (seconds) => {
    if (!seconds) return "0 min";
    const m = Math.round(seconds / 60);
    return m < 60 ? `${m} min` : `${Math.floor(m / 60)}h ${m % 60}m`;
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

  const openDetail = async (student) => {
    setSelected(student);
    setDetail(null);
    setDetailLoading(true);
    try {
      const res = await getStudentDetail(student.user_id);
      setDetail(res.data);
    } catch {
      setError("Failed to load student detail.");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleExportAll = async () => {
    try {
      const res = await exportAllStudentsCsv();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "all_students_data.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      setError("Export failed.");
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="skeleton" style={{ height: 40, width: 250, marginBottom: 20 }} />
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
          Teacher Dashboard
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
          Overview of all students — pre/post tests, quiz history, and time spent.
        </p>

        {error && <p className="error">{error}</p>}

        <div style={{ marginBottom: "1.25rem" }}>
          <button className="btn-secondary" onClick={handleExportAll}>
            Download all student data (CSV)
          </button>
        </div>

        {/* ===== Summary table ===== */}
        <div className="card" style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontSize: "1.15rem", marginBottom: "1rem" }}>
            Students ({students.length})
          </h2>

          {students.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>No students registered yet.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.9rem",
                }}
              >
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                    <th style={{ padding: "0.6rem" }}>Name</th>
                    <th style={{ padding: "0.6rem" }}>Pre</th>
                    <th style={{ padding: "0.6rem" }}>Post</th>
                    <th style={{ padding: "0.6rem" }}>Mastery</th>
                    <th style={{ padding: "0.6rem" }}>Time</th>
                    <th style={{ padding: "0.6rem" }}>Last Active</th>
                    <th style={{ padding: "0.6rem" }}></th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.user_id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "0.7rem", fontWeight: 500 }}>
                        {s.full_name}
                        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                          {s.email}
                        </div>
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {s.pre_test_score != null ? `${s.pre_test_score}%` : "—"}
                      </td>
                      <td style={{ padding: "0.7rem", fontWeight: 600, color: "var(--primary)" }}>
                        {s.post_test_score != null ? `${s.post_test_score}%` : "—"}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {s.mastery_score?.toFixed(0) ?? 0}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        {formatMinutes(s.total_time_seconds)}
                      </td>
                      <td style={{ padding: "0.7rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                        {formatDate(s.last_activity)}
                      </td>
                      <td style={{ padding: "0.7rem" }}>
                        <button
                          className="btn-secondary"
                          style={{ padding: "0.35rem 0.7rem", fontSize: "0.85rem" }}
                          onClick={() => openDetail(s)}
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ===== Student detail panel ===== */}
        {selected && (
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h2 style={{ fontSize: "1.15rem", margin: 0 }}>
                {selected.full_name}
              </h2>
              <button className="btn-secondary" onClick={() => { setSelected(null); setDetail(null); }}>
                Close
              </button>
            </div>

            {detailLoading && <p style={{ color: "var(--text-muted)" }}>Loading…</p>}

            {detail && (
              <>
                <div className="stats-grid" style={{ marginBottom: "1.25rem" }}>
                  <div className="stat-card">
                    <div className="stat-value">{detail.pre_test_score != null ? `${detail.pre_test_score}%` : "—"}</div>
                    <div className="stat-label">Pre-test</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{detail.post_test_score != null ? `${detail.post_test_score}%` : "—"}</div>
                    <div className="stat-label">Post-test</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{detail.mastery_score?.toFixed(0)}</div>
                    <div className="stat-label">Mastery</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{formatMinutes(detail.total_time_seconds)}</div>
                    <div className="stat-label">Total time</div>
                  </div>
                </div>

                <h3 style={{ fontSize: "1.05rem", marginBottom: "0.5rem" }}>Quiz history</h3>
                {detail.quiz_history.length === 0 ? (
                  <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>No quizzes yet.</p>
                ) : (
                  <div style={{ overflowX: "auto", marginBottom: "1.25rem" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                          <th style={{ padding: "0.5rem" }}>Lesson</th>
                          <th style={{ padding: "0.5rem" }}>Score</th>
                          <th style={{ padding: "0.5rem" }}>Time</th>
                          <th style={{ padding: "0.5rem" }}>Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.quiz_history.map((q, i) => (
                          <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                            <td style={{ padding: "0.5rem" }}>{q.lesson_title}</td>
                            <td style={{ padding: "0.5rem", fontWeight: 600 }}>{q.score}%</td>
                            <td style={{ padding: "0.5rem" }}>{formatMinutes(q.time_spent_seconds)}</td>
                            <td style={{ padding: "0.5rem", color: "var(--text-muted)" }}>{formatDate(q.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <h3 style={{ fontSize: "1.05rem", marginBottom: "0.5rem" }}>Activity history</h3>
                {detail.activity_history.length === 0 ? (
                  <p style={{ color: "var(--text-muted)" }}>No activity yet.</p>
                ) : (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                          <th style={{ padding: "0.5rem" }}>Activity</th>
                          <th style={{ padding: "0.5rem" }}>Score</th>
                          <th style={{ padding: "0.5rem" }}>Type</th>
                          <th style={{ padding: "0.5rem" }}>Time</th>
                          <th style={{ padding: "0.5rem" }}>Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.activity_history.map((a, i) => (
                          <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                            <td style={{ padding: "0.5rem" }}>{a.title}</td>
                            <td style={{ padding: "0.5rem" }}>{a.score != null ? `${a.score}%` : "—"}</td>
                            <td style={{ padding: "0.5rem" }}>{a.adaptive_action || "—"}</td>
                            <td style={{ padding: "0.5rem" }}>{formatMinutes(a.time_spent_seconds)}</td>
                            <td style={{ padding: "0.5rem", color: "var(--text-muted)" }}>{formatDate(a.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ===== Create teacher (admin only) ===== */}
        {isAdmin && (
          <div className="card">
            <h2 style={{ fontSize: "1.2rem", marginBottom: "0.35rem" }}>
              Create teacher / admin
            </h2>
            <p style={{ color: "var(--text-muted)", marginBottom: "1.25rem", fontSize: "0.95rem" }}>
              Only existing admins can create teachers or additional admins.
            </p>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="label">Full name</label>
                <input
                  className="input"
                  type="text"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
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
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
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
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
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
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                >
                  <option value="teacher">Teacher</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {createError && <p className="error" style={{ marginBottom: "0.75rem" }}>{createError}</p>}
              {createMsg && (
                <p className="success" style={{ marginBottom: "0.75rem", color: "var(--success)" }}>
                  {createMsg}
                </p>
              )}

              <button type="submit" className="btn-primary" disabled={creating}>
                {creating ? "Creating…" : "Create user"}
              </button>
            </form>
          </div>
        )}
      </div>
    </>
  );
}