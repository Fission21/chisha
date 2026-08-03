"use client";

import { useEffect, useState } from "react";
import { isLoggedIn, getEmail, clearAuth, apiFetch } from "@/lib/auth";

export default function AuthNav() {
  const [logged, setLogged] = useState(false);
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    setLogged(isLoggedIn());
    setEmail(getEmail());
  }, []);

  const logout = async () => {
    try { await apiFetch("/api/auth/logout", { method: "POST" }); } catch { /* ignore */ }
    clearAuth();
    window.location.href = "/";
  };

  if (!logged) {
    return <a className="btn ghost" href="/login">登录 / 注册</a>;
  }
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
      <span className="muted" style={{ fontSize: 13 }}>{email}</span>
      <button className="btn ghost" onClick={logout} style={{ padding: "8px 14px", fontSize: 13 }}>退出</button>
    </span>
  );
}
