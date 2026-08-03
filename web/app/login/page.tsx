"use client";

import { useState } from "react";
import { API_URL } from "@/lib/api";
import { setAuth } from "@/lib/auth";
import { IconArrow, IconAlert } from "@/components/icons";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${API_URL}/api/auth/${mode === "login" ? "login" : "register"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        setError(d.detail || "操作失败，请重试");
        return;
      }
      const data = await res.json();
      setAuth(data.token, data.email);
      window.location.href = "/";
    } catch {
      setError("连不上服务，请稍后再试。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 480 }}>
      <a className="back-link" href="/"><IconArrow size={15} /> 返回首页</a>
      <header className="masthead" style={{ marginTop: 0 }}>
        <div className="brand">
          <span className="brand-mark">账</span>
          <div>
            <div className="brand-name">{mode === "login" ? "登录" : "注册"}</div>
            <div className="brand-sub">登录后档案 / 收藏 / 记录云端同步</div>
          </div>
        </div>
      </header>

      <div className="panel">
        <div className="option-row" style={{ marginBottom: 18 }}>
          <span className={`option ${mode === "login" ? "on" : ""}`} onClick={() => { setMode("login"); setError(""); }}>登录</span>
          <span className={`option ${mode === "register" ? "on" : ""}`} onClick={() => { setMode("register"); setError(""); }}>注册</span>
        </div>
        <div className="field">
          <label htmlFor="email">邮箱</label>
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" />
        </div>
        <div className="field">
          <label htmlFor="password">密码（至少 6 位）</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} />
        </div>
        <button className="btn" onClick={submit} disabled={loading || !email || password.length < 6}>
          {loading ? "请稍候…" : mode === "login" ? "登录" : "注册并登录"}
        </button>
        {error && (
          <div className="error" style={{ marginTop: 14 }}>
            <IconAlert size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
