"use client";

import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import {
  addToDiary, removeFromDiary, loadDiary, loadTarget, computeTotals, dateKey,
  type DiaryItem, type DayEntry, type StoredTarget, type Totals,
} from "@/lib/diary";
import { IconBowl, IconFlame, IconProtein, IconCarbs, IconFat, IconLeaf, IconArrow, IconCheck, IconAlert } from "@/components/icons";
import AuthNav from "@/components/auth-nav";

type SearchResult = {
  id: string; title?: string; name?: string; cuisine?: string; difficulty?: string;
  cookTimeMin?: number; servings?: number; nutrition?: { energyKCal: number; protein: number; fat: number; CHO: number; dietaryFiber: number; sodium: number };
};

const MEALS = [
  ["breakfast", "早餐"],
  ["lunch", "午餐"],
  ["dinner", "晚餐"],
  ["snack", "加餐"],
];
const MEAL_ICON: Record<string, React.ReactNode> = {
  breakfast: <IconBowl size={18} />, lunch: <IconArrow size={18} style={{ transform: "rotate(-45deg)" }} />,
  dinner: <IconArrow size={18} style={{ transform: "rotate(45deg)" }} />, snack: <IconFlame size={18} />,
};

export default function DiaryPage() {
  const [today, setToday] = useState("");
  const [date, setDate] = useState("");
  const [diary, setDiary] = useState<Record<string, DiaryItem[]>>({});
  const [target, setTarget] = useState<StoredTarget | null>(null);

  const [meal, setMeal] = useState("lunch");
  const [mode, setMode] = useState<"recipe" | "food">("recipe");
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [picked, setPicked] = useState<SearchResult | null>(null);
  const [amount, setAmount] = useState("");

  useEffect(() => {
    const t = dateKey(new Date());
    setToday(t);
    setDate(t);
    setDiary(loadDiary());
    setTarget(loadTarget());
  }, []);
  useEffect(() => {
    if (!picked) setAmount("");
    else setAmount(picked.servings ? "1" : "100");
  }, [picked]);

  const items = useMemo(() => (date ? diary[date] || [] : []), [diary, date]);
  const totals = useMemo(() => computeTotals(items), [items]);

  const search = async (text: string) => {
    setQ(text);
    if (!text.trim()) { setResults([]); return; }
    try {
      const url = mode === "recipe"
        ? `${API_URL}/api/recipes?q=${encodeURIComponent(text)}&limit=8`
        : `${API_URL}/api/foods?q=${encodeURIComponent(text)}&limit=8`;
      const res = await fetch(url);
      if (!res.ok) throw new Error();
      const data = await res.json();
      // /api/foods 营养字段在顶层，统一归一化到 nutrition
      const norm = data.map((r: any) => ({
        id: r.id,
        title: r.title || r.name,
        name: r.name,
        cuisine: r.cuisine,
        difficulty: r.difficulty,
        cookTimeMin: r.cookTimeMin,
        servings: r.servings,
        nutrition: r.nutrition || {
          energyKCal: r.energyKCal || 0, protein: r.protein || 0, fat: r.fat || 0,
          CHO: r.CHO || 0, dietaryFiber: r.dietaryFiber || 0, sodium: r.sodium || 0,
        },
      }));
      setResults(norm);
    } catch {
      setResults([]);
    }
  };

  const add = () => {
    if (!picked) return;
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) return;
    const n = picked.nutrition || { energyKCal: 0, protein: 0, fat: 0, CHO: 0, dietaryFiber: 0, sodium: 0 };
    const item: DiaryItem = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      type: mode,
      refId: picked.id,
      name: picked.title || picked.name || picked.id,
      meal,
      amount: amt,
      unit: mode === "food" ? "g" : "份",
      nutrition: n,
    };
    setDiary(addToDiary(date, item));
    setPicked(null); setResults([]); setQ("");
  };

  const remove = (id: string) => setDiary(removeFromDiary(date, id));

  const shiftDay = (delta: number) => {
    const base = date || today;
    if (!base) return;
    const d = new Date(base + "T00:00:00");
    d.setDate(d.getDate() + delta);
    setDate(dateKey(d));
  };

  const macros: { lbl: string; cur: number; goal: number; unit: string; icon: React.ReactNode }[] = target ? [
    { lbl: "热量", cur: totals.energyKCal, goal: target.kcal, unit: "kcal", icon: <IconFlame size={14} /> },
    { lbl: "蛋白质", cur: totals.protein, goal: target.protein, unit: "g", icon: <IconProtein size={14} /> },
    { lbl: "碳水", cur: totals.CHO, goal: target.carb, unit: "g", icon: <IconCarbs size={14} /> },
    { lbl: "脂肪", cur: totals.fat, goal: target.fat, unit: "g", icon: <IconFat size={14} /> },
    { lbl: "纤维", cur: totals.dietaryFiber, goal: target.fiber, unit: "g", icon: <IconLeaf size={14} /> },
  ] : [];

  const mealItems = (m: string) => items.filter((i) => i.meal === m);

  return (
    <div className="container">
      <a className="back-link" href="/"><IconArrow size={15} /> 返回首页</a>
      <header className="masthead" style={{ marginTop: 0 }}>
        <div className="brand">
          <span className="brand-mark">记</span>
          <div>
            <div className="brand-name">饮食记录</div>
            <div className="brand-sub">今天吃了什么，对照目标一清二楚</div>
          </div>
        </div>
        <div className="nav">
          <AuthNav />
          <span className="btn ghost" onClick={() => shiftDay(-1)} style={{ cursor: "pointer" }}>← 前一天</span>
          <span className="btn ghost" onClick={() => shiftDay(1)} style={{ cursor: "pointer" }}>后一天 →</span>
        </div>
      </header>

      <div className="cols" style={{ marginBottom: 26 }}>
        {/* 左侧：记录 */}
        <div className="panel">
          <div className="stall-head">
            <h2>{date || "…"}</h2>
            <span className="rule" />
            {date !== today && <span className="hint">今天 {today}</span>}
          </div>

          <div className="option-row" style={{ marginBottom: 12 }}>
            {MEALS.map(([v, l]) => (
              <span key={v} className={`option ${meal === v ? "on" : ""}`} onClick={() => setMeal(v)}>
                {MEAL_ICON[v]} {l}
              </span>
            ))}
          </div>

          <div className="option-row" style={{ marginBottom: 10 }}>
            <span className={`option ${mode === "recipe" ? "on" : ""}`} onClick={() => { setMode("recipe"); setResults([]); setPicked(null); }}>按菜谱</span>
            <span className={`option ${mode === "food" ? "on" : ""}`} onClick={() => { setMode("food"); setResults([]); setPicked(null); }}>按食材</span>
          </div>

          <input
            className="pick-input"
            style={{ width: "100%", padding: "10px 12px", border: "1.5px solid var(--line-strong)", borderRadius: 10, background: "var(--paper)", fontSize: 15 }}
            placeholder={mode === "recipe" ? "搜索菜谱，如：鸡胸、三明治…" : "搜索食材，如：鸡蛋、燕麦…"}
            value={q}
            onChange={(e) => search(e.target.value)}
          />

          {results.length > 0 && (
            <div className="result-list">
              {results.map((r) => (
                <div key={r.id} className="menu-row" style={{ cursor: "pointer" }} onClick={() => setPicked(r)}>
                  <div style={{ flex: 1 }}>
                    <div className="menu-title" style={{ fontSize: 15 }}>{r.title || r.name}</div>
                    <div className="menu-meta">
                      {r.cuisine ? <span>{r.cuisine}</span> : null}
                      {r.nutrition ? <span>· {Math.round(r.nutrition.energyKCal)} kcal · 蛋白 {Math.round(r.nutrition.protein)} g</span> : null}
                      {r.servings ? <span>· {r.servings} 人份</span> : null}
                    </div>
                  </div>
                  {picked?.id === r.id && <span className="stamp red"><IconCheck size={12} /> 已选</span>}
                </div>
              ))}
            </div>
          )}

          {picked && (
            <div className="pick-row" style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 12, flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: 180 }}>
                <div className="menu-title" style={{ fontSize: 15 }}>{picked.title || picked.name}</div>
                <div className="menu-meta">
                  每{picked.servings ? "份" : "100g"} {Math.round((picked.nutrition?.energyKCal || 0) / (picked.servings || 1))} kcal
                  · 蛋白 {Math.round((picked.nutrition?.protein || 0) / (picked.servings || 1))} g
                </div>
              </div>
              <input
                type="number" min={1} value={amount}
                onChange={(e) => setAmount(e.target.value)}
                style={{ width: 90, padding: "9px 10px", border: "1.5px solid var(--line-strong)", borderRadius: 10, background: "var(--paper)", fontSize: 15 }}
              />
              <span className="muted" style={{ fontSize: 13 }}>{picked.servings ? "份" : "g"}</span>
              <button className="btn" style={{ padding: "10px 18px", fontSize: 14 }} onClick={add}>记一笔</button>
            </div>
          )}

          <div className="stall-head" style={{ marginTop: 24 }}>
            <h2>当日记录</h2>
            <span className="rule" />
            <span className="hint">{items.length} 条</span>
          </div>
          {items.length === 0 && <div className="empty">这一天还没记录，从上面搜索添加吧。</div>}
          {MEALS.map(([m, label]) => {
            const list = mealItems(m);
            if (list.length === 0) return null;
            return (
              <div key={m} style={{ marginBottom: 14 }}>
                <div className="menu-meta" style={{ fontWeight: 700, color: "var(--ink)" }}>{label}</div>
                <ul className="list-plain">
                  {list.map((it) => (
                    <li key={it.id}>
                      <span>
                        {it.name}
                        <span className="muted" style={{ fontSize: 12.5 }}> · {it.amount}{it.unit} · {Math.round(it.nutrition.energyKCal)} kcal</span>
                      </span>
                      <span className="amt" style={{ cursor: "pointer" }} onClick={() => remove(it.id)}>删除</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        {/* 右侧：目标与进度 */}
        <div className="panel">
          <div className="stall-head">
            <h2>今日进度</h2>
            <span className="rule" />
          </div>
          {!target && (
            <div className="empty">
              还没有每日目标。先到首页生成一份饮食计划，目标会自动带到这里。
              <div style={{ marginTop: 14 }}><a className="btn" href="/">去生成计划</a></div>
            </div>
          )}
          {target && (
            <>
              <div className="board" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
                <div className="cell"><div className="num">{Math.round(totals.energyKCal)}<small> kcal</small></div><div className="lbl"><IconFlame size={14} /> 目标 {target.kcal}</div></div>
                <div className="cell"><div className="num">{Math.round(totals.protein)}<small> g</small></div><div className="lbl"><IconProtein size={14} /> 目标 {target.protein} g</div></div>
                <div className="cell"><div className="num">{Math.round(totals.CHO)}<small> g</small></div><div className="lbl"><IconCarbs size={14} /> 目标 {target.carb} g</div></div>
              </div>
              <div style={{ marginTop: 18 }}>
                {macros.map((m) => {
                  const pct = Math.min(100, Math.round((m.cur / m.goal) * 100));
                  return (
                    <div className="macro-row" key={m.lbl}>
                      <div className="top">
                        <span>{m.icon} {m.lbl} · {Math.round(m.cur)} / {m.goal} {m.unit}</span>
                        <span className={pct >= 100 ? "stamp red" : "stamp green"} style={{ padding: "1px 6px", fontSize: 11 }}>{pct}%</span>
                      </div>
                      <div className="bar"><div style={{ width: `${pct}%` }} /></div>
                    </div>
                  );
                })}
              </div>
              <p className="muted" style={{ marginTop: 16, fontSize: 13 }}>
                目标来自最近一次生成的计划（BMR {Math.round(target.bmr)} · TDEE {Math.round(target.tdee)}）。
              </p>
            </>
          )}
        </div>
      </div>

      {!target && <div className="error"><IconAlert size={18} style={{ flexShrink: 0, marginTop: 2 }} />记录前建议先生成饮食计划，才能对照每日目标。</div>}
    </div>
  );
}
