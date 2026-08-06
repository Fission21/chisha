"use client";

import { FormEvent, useState } from "react";
import { API_URL } from "@/lib/api";
import ShoppingList from "@/components/shopping-list";

type Nutrition = { energyKCal: number; protein: number; fat: number; CHO: number; dietaryFiber: number; sodium: number };

type RecipeSummary = {
  id: string; title: string; cuisine: string; difficulty: string;
  cookTimeMin: number; servings: number; coverEmoji: string;
  allergens: string[]; tags: string[]; nutrition: Nutrition;
  health: { strictEligible: boolean; addedOilG: number; labels: string[] };
};

type MealRec = { meal: string; mealLabel: string; targetKcal: number; targetProtein: number; recommendations: RecipeSummary[] };
type CaloriePlan = {
  targetKcal: number; actualKcal: number; actualProtein: number;
  meals: MealRec[];
  shoppingList: { name: string; amount: number; unit: string; note: string }[];
};

const KCAL_PRESETS = [1200, 1500, 1800, 2000, 2400, 3000];
const ALLERGY_OPTIONS = ["鸡蛋", "牛奶", "乳制品", "小麦", "花生", "虾", "鱼", "大豆"];
const CUISINE_OPTIONS = ["中餐", "西式", "日式", "韩式", "泰式", "东南亚", "印度", "意式", "墨西哥", "越南", "地中海", "中东", "美式", "饮品"];
const HEALTH_OPTIONS = [
  ["balanced", "均衡健身", "蛋白质优先，兼顾热量与日常饮食质量"],
  ["strict", "严格控油控盐", "添加油、钠、脂肪和加工肉都有硬限制"],
];
const EQUIPMENT_OPTIONS = ["平底锅", "炒锅", "汤锅", "蒸锅", "烤箱", "空气炸锅", "微波炉", "电饭煲", "搅拌机", "无需加热"];
const MEAL_ICON: Record<string, string> = { breakfast: "🍳", lunch: "🍱", dinner: "🍲", snack: "🥜" };

export default function CalorieRecipePage() {
  const [targetKcal, setTargetKcal] = useState("2000");
  const [allergies, setAllergies] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [healthProfile, setHealthProfile] = useState("balanced");
  const [equipment, setEquipment] = useState<string[]>([]);
  const [equipmentMode, setEquipmentMode] = useState("available");
  const [plan, setPlan] = useState<CaloriePlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const toggle = (list: string[], set: (v: string[]) => void, v: string) =>
    set(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const generate = async (event?: FormEvent) => {
    event?.preventDefault();
    const kcal = Number(targetKcal);
    if (!kcal || kcal < 800 || kcal > 6000) {
      setError("目标热量请在 800-6000 kcal 之间。");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/calorie-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          targetKcal: kcal, goal: "maintain", allergies, preferred_cuisines: cuisines,
          health_profile: healthProfile, equipment, equipment_mode: equipmentMode,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "生成失败");
      setPlan(body);
    } catch (err) {
      setPlan(null);
      setError(err instanceof Error ? err.message : "连不上后厨了，请稍后再试。");
    } finally {
      setLoading(false);
    }
  };

  const diffPct = plan ? Math.round(((plan.actualKcal - plan.targetKcal) / plan.targetKcal) * 100) : 0;

  return (
    <main className="container">
      <a className="back-link" href="/">← 返回首页</a>
      <header className="masthead" style={{ marginTop: 0 }}>
        <div className="brand">
          <span className="brand-mark">配</span>
          <div>
            <div className="brand-name">热量菜谱</div>
            <div className="brand-sub">输入目标热量，自动生成一天的吃法</div>
          </div>
        </div>
        <nav className="nav">
          <a className="btn ghost" href="/calorie">热量查询</a>
          <a className="btn ghost" href="/recipes">菜谱库</a>
          <a className="btn ghost" href="/diary">饮食记录</a>
        </nav>
      </header>

      <form className="panel section" onSubmit={generate}>
        <div className="stall-head">
          <h2>我的目标</h2>
          <span className="rule" />
        </div>
        <div className="field">
          <label htmlFor="target-kcal">每日目标热量（kcal）</label>
          <input
            id="target-kcal"
            type="number"
            min={800}
            max={6000}
            step={50}
            value={targetKcal}
            onChange={(e) => setTargetKcal(e.target.value)}
            placeholder="例如 2000"
          />
        </div>
        <div className="calorie-examples" aria-label="热量预设">
          {KCAL_PRESETS.map((k) => (
            <button key={k} type="button" className="option" onClick={() => setTargetKcal(String(k))}>{k}</button>
          ))}
        </div>

        <div className="stall-head" style={{ marginTop: 24 }}>
          <h2>饮食模式</h2>
          <span className="rule" />
        </div>
        <div className="option-row">
          {HEALTH_OPTIONS.map(([value, label, hint]) => (
            <button key={value} type="button" className={`option ${healthProfile === value ? "on" : ""}`} onClick={() => setHealthProfile(value)} aria-pressed={healthProfile === value}>
              {label}<span style={{ fontSize: 12, opacity: 0.8 }}>{hint}</span>
            </button>
          ))}
        </div>

        <div className="stall-head" style={{ marginTop: 24 }}>
          <h2>过敏 / 忌口</h2>
          <span className="rule" />
        </div>
        <div className="option-row">
          {ALLERGY_OPTIONS.map((v) => (
            <span key={v} className={`option ${allergies.includes(v) ? "on" : ""}`} onClick={() => toggle(allergies, setAllergies, v)} role="button" tabIndex={0}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(allergies, setAllergies, v); } }}>
              {v}
            </span>
          ))}
        </div>

        <div className="stall-head" style={{ marginTop: 24 }}>
          <h2>我有的厨具</h2>
          <span className="rule" />
          <span className="hint">留空 = 不限制</span>
        </div>
        <div className="option-row">
          {EQUIPMENT_OPTIONS.map((value) => (
            <button key={value} type="button" className={`option ${equipment.includes(value) ? "on" : ""}`} onClick={() => toggle(equipment, setEquipment, value)} aria-pressed={equipment.includes(value)}>
              {value}
            </button>
          ))}
        </div>
        {equipment.length > 0 && (
          <div className="option-row" style={{ marginTop: 10 }}>
            {["available", "any", "all"].map((value) => (
              <button key={value} type="button" className={`option ${equipmentMode === value ? "on" : ""}`} onClick={() => setEquipmentMode(value)} aria-pressed={equipmentMode === value}>
                {value === "available" ? "我有这些即可" : value === "any" ? "包含任一" : "包含全部"}
              </button>
            ))}
          </div>
        )}

        <div className="stall-head" style={{ marginTop: 24 }}>
          <h2>偏好菜系</h2>
          <span className="rule" />
          <span className="hint">留空 = 全部菜系都推荐</span>
        </div>
        <div className="option-row">
          {CUISINE_OPTIONS.map((v) => (
            <span key={v} className={`option ${cuisines.includes(v) ? "on" : ""}`} onClick={() => toggle(cuisines, setCuisines, v)} role="button" tabIndex={0}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(cuisines, setCuisines, v); } }}>
              {v}
            </span>
          ))}
        </div>

        <div className="btn-row">
          <button className="btn" type="submit" disabled={loading}>{loading ? "正在配菜…" : "生成热量菜谱"}</button>
        </div>
      </form>

      {error && <div className="error section">{error}</div>}

      {plan && (
        <section className="rise">
          <div className="panel section">
            <div className="stall-head">
              <h2>全天合计</h2>
              <span className="rule" />
              <span className="hint">每餐取第一道计算</span>
            </div>
            <div className="board calorie-board">
              <div className="cell">
                <div className="num">{plan.targetKcal} <small>kcal</small></div>
                <div className="lbl">目标热量</div>
              </div>
              <div className="cell">
                <div className="num">{Math.round(plan.actualKcal)} <small>kcal</small></div>
                <div className="lbl">首选合计</div>
              </div>
              <div className="cell">
                <div className="num">{diffPct > 0 ? "+" : ""}{diffPct}%</div>
                <div className="lbl">偏离目标</div>
              </div>
              <div className="cell">
                <div className="num">{Math.round(plan.actualProtein)} <small>g</small></div>
                <div className="lbl">蛋白质合计</div>
              </div>
            </div>
            <p className="muted calorie-notice">热量按菜谱每份营养计算；“严格控油控盐”是营养估算筛选，不是医疗建议。换成同餐其他选项，热量会随之变化。</p>
          </div>

          {plan.meals.map((m) => (
            <div className="panel section" key={m.meal}>
              <div className="stall-head">
                <h2>{MEAL_ICON[m.meal]} {m.mealLabel}</h2>
                <span className="rule" />
                <span className="hint">目标 {m.targetKcal} kcal · 蛋白 {m.targetProtein} g</span>
              </div>
              {m.recommendations.length === 0 && (
                <div className="empty">这个时段没有合适的菜谱，试试放宽忌口或偏好。</div>
              )}
              <ul className="list-plain estimate-list">
                {m.recommendations.map((r, i) => (
                  <li key={r.id}>
                    <div>
                      <strong>{i === 0 ? "首选 " : "备选 "}<a href={`/recipes/${r.id}`} target="_blank" rel="noopener noreferrer">{r.title}</a></strong>
                      <div className="muted estimate-note">{r.cuisine} · {r.difficulty} · {r.cookTimeMin} 分钟 · {r.servings} 人份 · 油 {r.health.addedOilG}g</div>
                      {r.allergens.length > 0 && (
                        <div className="muted estimate-note">含过敏原：{r.allergens.join("、")}</div>
                      )}
                    </div>
                    <div className="estimate-values">
                      <strong>{Math.round(r.nutrition.energyKCal)} kcal</strong>
                      <span>蛋白 {r.nutrition.protein} g · 碳水 {r.nutrition.CHO} g</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {plan.shoppingList.length > 0 && (
            <div className="panel section">
              <div className="stall-head">
                <h2>购物清单</h2>
                <span className="rule" />
                <span className="hint">按首选菜谱汇总 · 1 人份</span>
              </div>
              <ShoppingList items={plan.shoppingList} storageKey="calorie-recipe" />
            </div>
          )}
        </section>
      )}
    </main>
  );
}
