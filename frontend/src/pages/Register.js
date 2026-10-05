import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register, login, getMe, getMyTests } from "../services/api";

export default function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // 1. Create account
      await register({
        email,
        full_name: fullName,
        password,
      });

      // 2. Auto-login
      const res = await login(email, password);
      localStorage.setItem("access_token", res.data.access_token);
      if (res.data.refresh_token) {
        localStorage.setItem("refresh_token", res.data.refresh_token);
      }

      // 3. Check role
      const me = await getMe();
      if (me.data.role === "teacher" || me.data.role === "admin") {
        navigate("/admin");
        return;
      }

      // 4. New student → pre-test
      try {
        const tests = await getMyTests();
        const hasPreTest = tests.data.some((t) => t.test_type === "pre_test");
        if (!hasPreTest) {
          navigate("/evaluation");
          return;
        }
      } catch {
        // if getMyTests fails, still go to evaluation for new users
        navigate("/evaluation");
        return;
      }

      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="card auth-card">
        <h1>Create account</h1>
        <p>Start learning how to identify and prevent misinformation.</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="label">Full Name</label>
            <input
              className="input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="label">Password (min 6 characters)</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          {error && <p className="error">{error}</p>}

          <button
            className="btn-primary"
            type="submit"
            disabled={loading}
            style={{ width: "100%", marginTop: "0.5rem" }}
          >
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>

        <p
          style={{
            marginTop: "1.25rem",
            textAlign: "center",
            color: "var(--text-muted)",
          }}
        >
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}