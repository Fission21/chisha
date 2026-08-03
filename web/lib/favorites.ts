// 收藏：localStorage 存菜谱 id 集合，登录后与账号同步
import { isLoggedIn, apiFetch } from "@/lib/auth";

const KEY = "chisha-favorites-v1";

export function loadFavorites(): string[] {
  try {
    const raw = localStorage.getItem(KEY);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

export function saveFavorites(ids: string[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(ids));
  } catch { /* ignore */ }
}

export function isFavorite(id: string): boolean {
  return loadFavorites().includes(id);
}

export function toggleFavorite(id: string): string[] {
  const set = new Set(loadFavorites());
  if (set.has(id)) set.delete(id); else set.add(id);
  const arr = [...set];
  saveFavorites(arr);
  return arr;
}

export async function syncFavoritesFromServer(): Promise<string[]> {
  if (!isLoggedIn()) return loadFavorites();
  try {
    const res = await apiFetch("/api/me/favorites");
    if (res.ok) {
      const data = await res.json();
      const ids = Array.isArray(data?.ids) ? data.ids : [];
      saveFavorites(ids);
      return ids;
    }
  } catch { /* ignore */ }
  return loadFavorites();
}

export async function pushFavoritesToServer(ids: string[]): Promise<void> {
  if (!isLoggedIn()) return;
  try {
    await apiFetch("/api/me/favorites", { method: "PUT", body: JSON.stringify({ ids }) });
  } catch { /* ignore */ }
}
