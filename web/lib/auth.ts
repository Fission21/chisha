// 登录态与授权请求
import { API_URL } from "@/lib/api";

const TOKEN_KEY = "chisha-token-v1";
const EMAIL_KEY = "chisha-email-v1";

export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
export function getEmail(): string | null {
  try { return localStorage.getItem(EMAIL_KEY); } catch { return null; }
}
export function isLoggedIn(): boolean {
  return !!getToken();
}
export function setAuth(token: string, email: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(EMAIL_KEY, email);
  } catch { /* ignore */ }
}
export function clearAuth(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
  } catch { /* ignore */ }
}

export async function apiFetch(path: string, opts: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = { ...(opts.headers as Record<string, string> | undefined) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (opts.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const res = await fetch(`${API_URL}${path}`, { ...opts, headers });
  if (res.status === 401) clearAuth();
  return res;
}
