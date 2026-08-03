"use client";

import { useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import {
  IconBowl, IconFlame, IconProtein, IconCarbs, IconFat, IconClock,
  IconChef, IconBasket, IconScale, IconArrow, IconCheck, IconAlert, IconLeaf,
} from "@/components/icons";
import DishMark from "@/components/dish-mark";

type Nutrition = { energyKCal: number; protein: number; fat: number; CHO: number; dietaryFiber: number; sodium: number };
type RecipeSummary = {
  id: string; title: string; titleEn: string; cuisine: string; difficulty: string;
  cookTimeMin: number; servings: number; summary: string; coverEmoji: string;
  mealTypes: string[]; tags: string[]; allergens: string[]; nutrition: Nutrition;
};
type MealRec = { meal: string; mealLabel: string; targetKcal: number; targetProtein: number; recommendations: RecipeSummary[] };
type Plan = { bmr: number; tdee: number; daily: { kcal: number; protein: number; fat: number; carb: number; fiber: number }; meals: MealRec[] };

const ACTIVITY_OPTIONS = [
  ["sedentary", "久坐"],
  ["light", "轻度活动"],
  ["moderate", "每周 3-5 次运动"],
  ["active", "每天训练"],
  ["very", "极高强度"],
];
const GOAL_OPTIONS = [
  ["cut", "减脂", "热量缺口 350 kcal"],
  ["maintain", "维持", "热量持平"],
  ["bulk", "增肌", "热量盈余 350 kcal"],
];
const ALLERGY_OPTIONS = ["鸡蛋", "牛奶", "乳制品", "小麦", "花生", "虾", "鱼", "大豆"];
const CUISINE_OPTIONS = ["中餐", "西式", "日式", "韩式", "越南", "泰式", "墨西哥", "东南亚", "印度"];

const MEAL_ICON: Record<string, React.ReactNode> = {
  breakfast: <IconBowl size={20} />,
  lunch: <IconBasket size={20} />,
  dinner: <IconChef size={20} />,
  snack: <IconFlame size={20} />,
};
const MEAL_STAMP: Record<string, string> = { breakfast: "stamp mustard", lunch: "stamp red", dinner: "stamp green", snack: "stamp mustard" };

export default function HomePage() {
  const [step, setStep] = useState(1);
  const [sex, setSex] = useState("male");
  const [age, setAge] = useState("28");
  const [height, setHeight] = useState("175");
  const [weight, setWeight] = useState("70");
  const [bodyFat, setBodyFat] = useState("");
  const [activity, setActivity] = useState("moderate");
  const [goal, setGoal] = useState("cut");
  const [allergies, setAllergies] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);

  const toggle = (list: string[], set: (v: string[]) => void, v: string) =>
    set(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const step1Valid = height && weight && age;

  const submit = async () => {
    setLoading(true); setError(""); setPlan(null);
    try {
      const res = await fetch(`${API_URL}/api/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sex, age: Number(age), height_cm: Number(height), weight_kg: Number(weight),
          body_fat: bodyFat ? Number(bodyFat) : null,
          activity_level: activity, goal,
          allergies, preferences: [], preferred_cuisines: cuisines,
        }),
      });
      if (!res.ok) throw new Error(`请求失败 (${res.status})`);
      setPlan(await res.json());
    } catch {
      setError("连不上后厨了，请稍后再试。");
    } finally {
      setLoading(false);
    }
  };

  const macros = useMemo(() => {
    if (!plan) return [];
    const d = plan.daily;
    return [
      { lbl: "每日热量", num: `${d.kcal}`, unit: "kcal", icon: <IconFlame size={14} /> },
      { lbl: "蛋白质", num: `${d.protein}`, unit: "g", icon: <IconProtein size={14} /> },
      { lbl: "碳水化合物", num: `${d.carb}`, unit: "g", icon: <IconCarbs size={14} /> },
      { lbl: "脂肪", num: `${d.fat}`, unit: "g", icon: <IconFat size={14} /> },
      { lbl: "膳食纤维", num: `${d.fiber}`, unit: "g", icon: <IconLeaf size={14} /> },
    ];
  }, [plan]);

  return (
    <div className="container">
      <header className="masthead">
        <div className="brand">
          <span className="brand-mark">吃</span>
          <div>
            <div className="brand-name">吃啥</div>
            <div className="brand-sub">健身吃什么 · 怎么做，一次说清</div>
          </div>
        </div>
        <nav className="nav">
          <a className="btn ghost" href="/recipes">菜谱库</a>
        </nav>
      </header>

      {loading && (
        <div className="panel section" aria-busy="true">
          <div className="loading">正在开摊，稍等片刻…</div>
          <div className="skeleton">
            <div className="bar" style={{ width: "38%" }} />
            <div className="bar" style={{ width: "92%" }} />
            <div className="bar" style={{ width: "85%" }} />
            <div className="bar" style={{ width: "70%" }} />
          </div>
        </div>
      )}

      {!loading && plan && (
        <section className="section">
          <div className="stall-head">
            <h2>今日计划</h2>
            <span className="rule" />
            <span className="hint">BMR {Math.round(plan.bmr)} · TDEE {Math.round(plan.tdee)} kcal</span>
          </div>

          <div className="board rise">
            {macros.map((m) => (
              <div className="cell" key={m.lbl}>
                <div className="num">{m.num}<small> {m.unit}</small></div>
                <div className="lbl">{m.icon}{m.lbl}</div>
              </div>
            ))}
          </div>

          {plan.meals.map((m, i) => (
            <div className={`stall rise rise-${Math.min(i + 1, 4)}`} key={m.meal}>
              <div className="stall-top">
                <div className="stall-name">
                  <span className="ic">{MEAL_ICON[m.meal]}</span>
                  <h3>{m.mealLabel}</h3>
                  <span className={MEAL_STAMP[m.meal]}>目标 {m.targetKcal} kcal · 蛋白 {m.targetProtein} g</span>
                </div>
              </div>
              {m.recommendations.length === 0 && (
                <div className="empty">这个时段没有合适的菜谱，试试放宽忌口。</div>
              )}
              {m.recommendations.length > 0 && (
                <div className="muted" style={{ fontSize: 12, margin: "-4px 0 8px 54px" }}>以下 {m.recommendations.length} 道任选其一，即可接近该餐目标</div>
              )}
              {m.recommendations.map((r) => <MenuRow r={r} key={r.id} />)}
            </div>
          ))}

          <div className="btn-row">
            <a className="btn ghost" href="/recipes">浏览全部菜谱</a>
            <button className="btn ghost" onClick={() => setPlan(null)}>重新填写</button>
          </div>
        </section>
      )}

      {!loading && !plan && (
        <div className="panel section">
          <div className="stepper">
            <div className={`step-item ${step === 1 ? "on" : "done"}`}>
              <span className="dot">{step === 1 ? "1" : <IconCheck size={13} />}</span>
              <span>身体信息</span>
            </div>
            <span className="link" />
            <div className={`step-item ${step === 2 ? "on" : ""}`}>
              <span className="dot">2</span>
              <span>目标与口味</span>
            </div>
          </div>

          {step === 1 && (
            <>
              <div className="stall-head">
                <h2>我的身体信息</h2>
                <span className="rule" />
              </div>
              <div className="grid grid-2">
                <div className="field">
                  <label htmlFor="sex">性别</label>
                  <select id="sex" value={sex} onChange={(e) => setSex(e.target.value)}>
                    <option value="male">男</option>
                    <option value="female">女</option>
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="age">年龄</label>
                  <input id="age" type="number" value={age} onChange={(e) => setAge(e.target.value)} min={10} max={100} />
                </div>
                <div className="field">
                  <label htmlFor="height">身高 (cm)</label>
                  <input id="height" type="number" value={height} onChange={(e) => setHeight(e.target.value)} min={100} max={250} />
                </div>
                <div className="field">
                  <label htmlFor="weight">体重 (kg)</label>
                  <input id="weight" type="number" value={weight} onChange={(e) => setWeight(e.target.value)} min={30} max={300} />
                </div>
                <div className="field">
                  <label htmlFor="bodyFat">体脂率 %（选填）</label>
                  <input id="bodyFat" type="number" value={bodyFat} onChange={(e) => setBodyFat(e.target.value)} min={3} max={70} placeholder="如 18" />
                </div>
                <div className="field">
                  <label htmlFor="activity">活动量</label>
                  <select id="activity" value={activity} onChange={(e) => setActivity(e.target.value)}>
                    {ACTIVITY_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
              </div>
              <div className="btn-row">
                <button className="btn" disabled={!step1Valid} onClick={() => setStep(2)}>
                  下一步<IconArrow size={18} />
                </button>
                {!step1Valid && <span className="muted" style={{ fontSize: 13 }}>先填好身高、体重和年龄</span>}
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className="stall-head">
                <h2>我的目标</h2>
                <span className="rule" />
              </div>
              <div className="option-row">
                {GOAL_OPTIONS.map(([v, l, d]) => (
                  <span key={v} className={`option ${goal === v ? "on" : ""}`} onClick={() => setGoal(v)} role="button" tabIndex={0}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setGoal(v); } }}>
                    {goal === v ? <IconCheck size={15} /> : null}
                    {l}<span style={{ fontSize: 12, opacity: 0.85 }}>{d}</span>
                  </span>
                ))}
              </div>

              <div className="stall-head" style={{ marginTop: 28 }}>
                <h2>过敏 / 忌口</h2>
                <span className="rule" />
              </div>
              <div className="option-row">
                {ALLERGY_OPTIONS.map((v) => (
                  <span key={v} className={`option ${allergies.includes(v) ? "on" : ""}`} onClick={() => toggle(allergies, setAllergies, v)} role="button" tabIndex={0}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(allergies, setAllergies, v); } }}>
                    {allergies.includes(v) ? <IconCheck size={15} /> : null}
                    {v}
                  </span>
                ))}
              </div>

              <div className="stall-head" style={{ marginTop: 28 }}>
                <h2>偏好菜系</h2>
                <span className="rule" />
                <span className="hint">留空 = 中餐 + 全球都推荐</span>
              </div>
              <div className="option-row">
                {CUISINE_OPTIONS.map((v) => (
                  <span key={v} className={`option ${cuisines.includes(v) ? "on" : ""}`} onClick={() => toggle(cuisines, setCuisines, v)} role="button" tabIndex={0}
                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(cuisines, setCuisines, v); } }}>
                    {cuisines.includes(v) ? <IconCheck size={15} /> : null}
                    {v}
                  </span>
                ))}
              </div>

              <div className="btn-row">
                <button className="btn ghost" onClick={() => setStep(1)}>上一步</button>
                <button className="btn" onClick={submit} disabled={loading}>
                  {loading ? "正在算账…" : "生成我的饮食计划"}
                  {!loading && <IconScale size={18} />}
                </button>
              </div>
            </>
          )}

          {error && (
            <div className="error" style={{ marginTop: 18 }}>
              <IconAlert size={18} style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                {error}{" "}
                <button className="btn ghost" style={{ marginLeft: 8, padding: "4px 12px" }} onClick={submit}>重试</button>
              </div>
            </div>
          )}
        </div>
      )}

      {!loading && !plan && (
        <div className="panel section" style={{ marginTop: 24 }}>
          <div className="stall-head">
            <h2>这里能做什么</h2>
            <span className="rule" />
          </div>
          <ul className="list-plain">
            <li><span>用 Mifflin-St Jeor 算出基础代谢与每日消耗</span><span className="amt"><IconScale size={16} /></span></li>
            <li><span>按增肌 / 减脂目标给出每日热量与三大营养素</span><span className="amt"><IconFlame size={16} /></span></li>
            <li><span>从 48 道中餐 + 全球菜谱里按餐推荐（三明治 / 沙拉 / 意面 / 日韩东南亚）</span><span className="amt"><IconBasket size={16} /></span></li>
            <li><span>每道菜有食材克数、步骤、火候、每份营养</span><span className="amt"><IconChef size={16} /></span></li>
          </ul>
        </div>
      )}
    </div>
  );
}

function Price({ icon, value, unit, tone }: { icon: React.ReactNode; value: number; unit: string; tone: string }) {
  return (
    <span className={`price ${tone}`}>
      {icon} <b>{Math.round(value)}</b> {unit}
    </span>
  );
}

function MenuRow({ r }: { r: RecipeSummary }) {
  const n = r.nutrition;
  return (
    <div className="menu-row">
      <DishMark title={r.title} size={44} />
      <div className="menu-body">
        <div className="menu-title"><a href={`/recipes/${r.id}`}>{r.title}</a></div>
        <div className="menu-meta">
          <span>{r.cuisine}</span>
          <span>·</span>
          <span>{r.difficulty}</span>
          <span>·</span>
          <span><IconClock size={13} style={{ verticalAlign: -1 }} /> {r.cookTimeMin} 分钟</span>
          <span>·</span>
          <span>{r.servings} 人份</span>
        </div>
        <div className="menu-nutri">
          <Price tone="kcal" icon={<IconFlame size={13} style={{ verticalAlign: -1 }} />} value={n.energyKCal} unit="kcal" />
          <Price tone="protein" icon={<IconProtein size={13} style={{ verticalAlign: -1 }} />} value={n.protein} unit="g 蛋白" />
          <Price tone="carb" icon={<IconCarbs size={13} style={{ verticalAlign: -1 }} />} value={n.CHO} unit="g 碳水" />
          <Price tone="fat" icon={<IconFat size={13} style={{ verticalAlign: -1 }} />} value={n.fat} unit="g 脂肪" />
        </div>
        <div className="stamp-row">
          {r.tags.slice(0, 4).map((t) => <span className="stamp green" key={t}>{t}</span>)}
        </div>
      </div>
    </div>
  );
}
