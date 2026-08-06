// 身体档案：localStorage 记住上次输入
const KEY = "chisha-profile-v1";

export type SavedProfile = {
  sex: string;
  age: string;
  height: string;
  weight: string;
  bodyFat: string;
  activity: string;
  goal: string;
  healthProfile: string;
  allergies: string[];
  cuisines: string[];
};

export function loadProfile(): SavedProfile | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveProfile(p: SavedProfile): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(p));
  } catch { /* ignore */ }
}
