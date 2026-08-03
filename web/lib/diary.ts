// 饮食记录与每日目标：localStorage 持久化 + 汇总计算；登录后与账号云端同步
import { isLoggedIn, apiFetch } from "@/lib/auth";

export type DiaryItem = {
  id: string;
  type: "recipe" | "food";
  refId: string;      // recipe id 或 food id
  name: string;       // 显示名
  meal: string;       // breakfast/lunch/dinner/snack
  amount: number;     // 食材克数 或 菜谱份数
  unit: string;       // g 或 份
  nutrition: { energyKCal: number; protein: number; fat: number; CHO: number; dietaryFiber: number; sodium: number };
};

export type DayEntry = { date: string; items: DiaryItem[] };

export type StoredTarget = {
  kcal: number; protein: number; fat: number; carb: number; fiber: number;
  bmr: number; tdee: number; goal: string;
  savedAt: number;
};

const DIARY_KEY = "chisha-diary-v1";
const TARGET_KEY = "chisha-target-v1";

export function dateKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function loadDiary(): Record<string, DiaryItem[]> {
  try {
    const raw = localStorage.getItem(DIARY_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function saveDiary(map: Record<string, DiaryItem[]>): void {
  try {
    localStorage.setItem(DIARY_KEY, JSON.stringify(map));
  } catch { /* ignore */ }
}

export function addToDiary(date: string, item: DiaryItem): Record<string, DiaryItem[]> {
  const map = loadDiary();
  const list = map[date] || [];
  map[date] = [...list, item];
  saveDiary(map);
  return map;
}

export function removeFromDiary(date: string, itemId: string): Record<string, DiaryItem[]> {
  const map = loadDiary();
  map[date] = (map[date] || []).filter((i) => i.id !== itemId);
  if (map[date].length === 0) delete map[date];
  saveDiary(map);
  return map;
}

export function loadTarget(): StoredTarget | null {
  try {
    const raw = localStorage.getItem(TARGET_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveTarget(t: StoredTarget): void {
  try {
    localStorage.setItem(TARGET_KEY, JSON.stringify(t));
  } catch { /* ignore */ }
}

export type Totals = { energyKCal: number; protein: number; fat: number; CHO: number; dietaryFiber: number; sodium: number };

export function computeTotals(items: DiaryItem[]): Totals {
  const t: Totals = { energyKCal: 0, protein: 0, fat: 0, CHO: 0, dietaryFiber: 0, sodium: 0 };
  for (const it of items) {
    const factor = it.type === "food" ? it.amount / 100 : it.amount;
    t.energyKCal += (it.nutrition.energyKCal || 0) * factor;
    t.protein += (it.nutrition.protein || 0) * factor;
    t.fat += (it.nutrition.fat || 0) * factor;
    t.CHO += (it.nutrition.CHO || 0) * factor;
    t.dietaryFiber += (it.nutrition.dietaryFiber || 0) * factor;
    t.sodium += (it.nutrition.sodium || 0) * factor;
  }
  return t;
}

// ---- 云端同步 ----
export async function syncDiaryFromServer(): Promise<Record<string, DiaryItem[]>> {
  if (!isLoggedIn()) return loadDiary();
  try {
    const res = await apiFetch("/api/me/diary");
    if (res.ok) {
      const data = await res.json();
      const map: Record<string, DiaryItem[]> = {};
      for (const [k, v] of Object.entries(data)) map[k] = v as DiaryItem[];
      saveDiary(map);
      return map;
    }
  } catch { /* ignore */ }
  return loadDiary();
}

export async function pushDiaryDateToServer(date: string, items: DiaryItem[]): Promise<void> {
  if (!isLoggedIn()) return;
  try {
    await apiFetch("/api/me/diary", { method: "PUT", body: JSON.stringify({ date, items }) });
  } catch { /* ignore */ }
}
