import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../services/api";

export default function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const res = await register({
        email,
        full_name: fullName,
        password,
      });

      setSuccess(
        res.data.message ||
          "Registration successful! Please verify your email before logging in."
      );

      // Show the verification link in the UI for easy testing (thesis/demo)
      if (res.data.dev_verification_link) {
        setDevLink(res.data.dev_verification_link);
      }
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

        {success ? (
          <div>
              <p style={{ color: "var(--success, green)", marginBottom: "1.5rem" }}>
                {success}
              </p>
              
             <button
               className="btn-primary"
               style={{ width: "100%" }}
               onClick={() => navigate("/login")}
              >
                  Go to Login
             </button>
            </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="label">Full Name</label>
              <input
                className="input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
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
        )}

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