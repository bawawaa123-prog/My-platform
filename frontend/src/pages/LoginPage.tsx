import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../stores/auth";


type LocationState = {
  from?: {
    pathname?: string;
  };
};

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const redirectPath = (location.state as LocationState | null)?.from?.pathname ?? "/";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    try {
      await login({ email, password });
      navigate(redirectPath, { replace: true });
    } catch {
      setErrorMessage("Login failed. Please verify the account and password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <p className="eyebrow">Enterprise AI Workflow Demo</p>
        <h1>Support teams need more than a chatbot.</h1>
        <p className="auth-hero-copy">
          Sign in to the operations console for tickets, knowledge workflows, AI drafts,
          and multi-agent review trails.
        </p>
        <div className="auth-hero-grid">
          <article className="metric-card">
            <span className="metric-value">RAG</span>
            <span className="metric-label">Knowledge-backed replies</span>
          </article>
          <article className="metric-card">
            <span className="metric-value">HITL</span>
            <span className="metric-label">Human review before reply</span>
          </article>
          <article className="metric-card">
            <span className="metric-value">MCP</span>
            <span className="metric-label">External AI tool surface</span>
          </article>
        </div>
      </section>

      <section className="auth-card">
        <div className="auth-card-header">
          <p className="eyebrow">Sign In</p>
          <h2>Access the back office</h2>
          <p className="auth-helper">
            Use one of the seeded demo accounts to enter the dashboard.
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@example.com"
              autoComplete="email"
              required
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="admin123"
              autoComplete="current-password"
              required
            />
          </label>

          {errorMessage ? <p className="form-error">{errorMessage}</p> : null}

          <button type="submit" className="primary-button" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="demo-accounts">
          <p className="demo-accounts-title">Demo accounts</p>
          <p>`admin@example.com / admin123`</p>
          <p>`agent@example.com / agent123`</p>
          <p>`viewer@example.com / viewer123`</p>
        </div>
      </section>
    </div>
  );
}
