import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const res = await api.post(endpoint, { email, password });
      await login(res.data.access_token, res.data.refresh_token);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{background: 'var(--bg)'}}>
      <div className="w-full max-w-md mx-4">
        <div className="bg-[var(--card-bg)] rounded-2xl shadow-md p-8" style={{boxShadow: 'var(--shadow)'}}>
          <div className="mb-6 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-[var(--accent-bg)] mb-3">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L20 7v6c0 5-4 9-8 9s-8-4-8-9V7l8-5z" stroke="var(--accent-700)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h1 className="text-xl font-semibold" style={{color: 'var(--text-h)'}}>Meeting Minutes</h1>
            <p className="text-sm text-[var(--muted)]">Sign in to manage and summarize your meeting transcripts</p>
          </div>

          <div className="flex mb-6 rounded bg-[var(--bg)] p-1 border" style={{borderColor: 'var(--border)'}}>
            <button
              className={`flex-1 py-2 rounded leading-5 ${mode === "login" ? 'bg-[var(--card-bg)] text-[var(--text-h)] font-medium' : 'text-[var(--muted)]'}`}
              onClick={() => setMode("login")}
            >
              Login
            </button>
            <button
              className={`flex-1 py-2 rounded leading-5 ${mode === "register" ? 'bg-[var(--card-bg)] text-[var(--text-h)] font-medium' : 'text-[var(--muted)]'}`}
              onClick={() => setMode("register")}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2"
                style={{borderColor: 'var(--border)', focus: {ringColor: 'var(--accent)'}}}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full border rounded-lg px-3 py-2"
                style={{borderColor: 'var(--border)'}}
              />
            </div>

            {error && <p className="text-red-600 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[var(--accent)] hover:bg-[var(--accent-700)] text-white py-2 rounded-lg disabled:opacity-50"
            >
              {loading ? "Please wait..." : mode === "login" ? "Login" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}