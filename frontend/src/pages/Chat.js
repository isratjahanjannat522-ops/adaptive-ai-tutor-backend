import React, { useState, useRef, useEffect } from "react";
import { chatWithTutor } from "../services/api";
import Navbar from "../components/Navbar";

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am your Adaptive AI Tutor for Misinformation Literacy. Ask me anything about evaluating sources, spotting false claims, or the course material.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input.trim() };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const res = await chatWithTutor({
        message: userMsg.content,
        history: newHistory.slice(0, -1).map((m) => ({
          role: m.role,
          content: m.content,
        })),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.reply, sources: res.data.sources },
      ]);
    } catch (err) {
      setError("Failed to get response from the tutor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container" style={{ maxWidth: 800 }}>
        <h1 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>AI Chat Tutor</h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "1.25rem" }}>
          Ask questions about misinformation literacy. Answers are grounded in the course material.
        </p>

        <div
          className="card"
          style={{
            height: "55vh",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
            marginBottom: "1rem",
          }}
        >
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "85%",
                background: m.role === "user" ? "var(--primary)" : "var(--bg)",
                color: m.role === "user" ? "white" : "var(--text)",
                padding: "0.85rem 1.1rem",
                borderRadius: 12,
                border: m.role === "assistant" ? "1px solid var(--border)" : "none",
              }}
            >
              <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
              {m.sources && m.sources.length > 0 && (
                <div style={{ marginTop: 8, fontSize: "0.8rem", opacity: 0.8 }}>
                  Sources: {m.sources.join(" · ")}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              Tutor is thinking...
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && <p className="error">{error}</p>}

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <input
            className="input"
            placeholder="Ask about misinformation, sources, evidence..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            disabled={loading}
          />
          <button className="btn-primary" onClick={send} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </>
  );
}
