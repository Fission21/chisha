"use client";

import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import { IconClock, IconArrow, IconFlame, IconProtein, IconCarbs, IconFat } from "@/components/icons";
import DishMark from "@/components/dish-mark";

type RecipeSummary = {
  id: string; title: string; titleEn: string; cuisine: string; difficulty: string;
  cookTimeMin: number; servings: number; summary: string; coverEmoji: string;
  mealTypes: string[]; tags: string[]; allergens: string[]; nutrition: { energyKCal: number; protein: number; fat: number; CHO: number };
};

const MEALS = [
  ["", "全部"],
  ["breakfast", "早餐"],
  ["lunch", "午餐"],
  ["dinner", "晚餐"],
];

export default function RecipesPage() {
  const [list, setList] = useState<RecipeSummary[]>([]);
  const [meal, setMeal] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true); setError("");
      try {
        const params = new URLSearchParams({ limit: "200" });
        if (meal) params.set("meal", meal);
        if (cuisine) params.set("cuisine", cuisine);
        const res = await fetch(`${API_URL}/api/recipes?${params}`);
        if (!res.ok) throw new Error("加载失败");
        setList(await res.json());
      } catch {
        setError("菜谱柜没打开，请稍后再试。");
      } finally {
        setLoading(false);
      }
    })();
  }, [meal, cuisine]);

  const cuisines = useMemo(() => [...new Set(list.map((r) => r.cuisine))], [list]);

  return (
    <div className="container">
      <a className="back-link" href="/"><IconArrow size={15} /> 返回首页</a>
      <header className="masthead" style={{ marginTop: 0 }}>
        <div className="brand">
          <span className="brand-mark">吃</span>
          <div>
            <div className="brand-name">菜谱库</div>
            <div className="brand-sub">中餐 + 全球做法 · 共 {list.length} 道，每道都算好了营养</div>
          </div>
        </div>
      </header>

      <div className="panel section">
        <div className="option-row" style={{ marginBottom: 14 }}>
          {MEALS.map(([v, l]) => (
            <span key={v} className={`option ${meal === v ? "on" : ""}`} onClick={() => setMeal(v)}>{l}</span>
          ))}
        </div>
        <div className="option-row">
          <span className={`option ${cuisine === "" ? "on" : ""}`} onClick={() => setCuisine("")}>全部菜系</span>
          {cuisines.map((c) => (
            <span key={c} className={`option ${cuisine === c ? "on" : ""}`} onClick={() => setCuisine(c)}>{c}</span>
          ))}
        </div>
      </div>

      {loading && <div className="panel section"><div className="loading">正在翻菜谱…</div></div>}
      {error && (
        <div className="error section">
          <IconAlertInline />
          <div>
            {error}{" "}
            <button className="btn ghost" style={{ marginLeft: 8, padding: "4px 12px" }} onClick={() => { setMeal(""); setCuisine(""); window.location.reload(); }}>重试</button>
          </div>
        </div>
      )}
      {!loading && !error && (
        <div className="panel section">
          {list.map((r) => (
            <div className="menu-row" key={r.id}>
              <DishMark title={r.title} size={44} />
              <div className="menu-body">
                <div className="menu-title"><a href={`/recipes/${r.id}`}>{r.title}</a></div>
                <div className="menu-meta">
                  <span>{r.cuisine}</span><span>·</span><span>{r.difficulty}</span><span>·</span>
                  <span><IconClock size={13} style={{ verticalAlign: -1 }} /> {r.cookTimeMin} 分钟</span>
                </div>
                <div className="menu-nutri">
                  <span className="price kcal"><IconFlame size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.energyKCal)}</b> kcal</span>
                  <span className="price protein"><IconProtein size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.protein)}</b> g 蛋白</span>
                  <span className="price carb"><IconCarbs size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.CHO)}</b> g 碳水</span>
                  <span className="price fat"><IconFat size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.fat)}</b> g 脂肪</span>
                </div>
                <div className="stamp-row">{r.tags.slice(0, 4).map((t) => <span className="stamp green" key={t}>{t}</span>)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function IconAlertInline() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 2 }}>
      <path d="M12 3.5 21 20H3L12 3.5Z" /><path d="M12 10v4.5M12 17.5v.5" />
    </svg>
  );
}
