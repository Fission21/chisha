import type { Metadata } from "next";
import { promises as fs } from "fs";
import path from "path";
import { IconBowl, IconClock, IconChef, IconScale, IconFlame, IconProtein,
  IconCarbs, IconFat, IconLeaf, IconAlert, IconArrow } from "@/components/icons";
import DishMark from "@/components/dish-mark";
import FavButton from "@/components/fav-button";
import DiaryAddButton from "@/components/diary-add-button";

type Nutrition = { energyKCal: number; protein: number; fat: number; CHO: number; dietaryFiber: number; sodium: number };
type Ingredient = { name: string; unit: string; amount: number; note: string; food: { name: string; source: string } };
type Step = { text: string; durationMin: number | null; heat: string | null };
type RecipeSource = { name: string; url: string; license: string; revision: string };
type RecipeDetail = {
  id: string; title: string; titleEn: string; cuisine: string; difficulty: string;
  complexity: string;
  cookingMethods: string[]; equipment: string[];
  cookTimeMin: number; servings: number; summary: string; coverEmoji: string;
  source: RecipeSource;
  mealTypes: string[]; tags: string[]; allergens: string[]; nutrition: Nutrition;
  ingredients: Ingredient[]; steps: Step[]; tips: string[];
};

// 菜谱数据在构建时从 data/processed/recipes.json 读取，静态导出无需后端
const RECIPES_FILE = path.join(process.cwd(), "..", "data", "processed", "recipes.json");

async function loadRecipes(): Promise<RecipeDetail[]> {
  try {
    const raw = await fs.readFile(RECIPES_FILE, "utf-8");
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function getRecipe(id: string): Promise<RecipeDetail | null> {
  const recipes = await loadRecipes();
  return recipes.find((r) => r.id === id) ?? null;
}

export const dynamicParams = false;

export async function generateStaticParams(): Promise<{ id: string }[]> {
  const recipes = await loadRecipes();
  return recipes.map((r) => ({ id: r.id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const r = await getRecipe(id);
  return { title: r ? `${r.title} · 吃啥` : "菜谱未找到 · 吃啥" };
}

export default async function RecipePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const r = await getRecipe(id);
  if (!r) {
    return (
      <div className="container">
        <a className="back-link" href="/"><IconArrow size={15} /> 返回首页</a>
        <div className="error"><IconAlert size={18} style={{ flexShrink: 0, marginTop: 2 }} />菜谱不存在或服务暂不可用，回首页再挑一道吧。</div>
      </div>
    );
  }
  const n = r.nutrition;
  const nutriRows = [
    ["热量", `${Math.round(n.energyKCal)} kcal`],
    ["蛋白质", `${Math.round(n.protein)} g`],
    ["碳水化合物", `${Math.round(n.CHO)} g`],
    ["脂肪", `${Math.round(n.fat)} g`],
    ["膳食纤维", `${Math.round(n.dietaryFiber)} g`],
    ["钠", `${Math.round(n.sodium)} mg`],
  ];
  const mealLabel: Record<string, string> = { breakfast: "早餐", lunch: "午餐", dinner: "晚餐", snack: "加餐" };

  return (
    <div className="container">
      <a className="back-link" href="/"><IconArrow size={15} /> 返回首页</a>

      <div className="detail-hero">
        <DishMark title={r.title} size={76} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <h1>{r.title}</h1>
          {r.titleEn && <div className="en">{r.titleEn}</div>}
          <div className="meta-pills">
            <FavButton recipeId={r.id} />
            <DiaryAddButton recipeId={r.id} title={r.title} nutrition={r.nutrition} />
            <span className="pill">{r.cuisine}</span>
            <span className="pill">{r.difficulty}</span>
            <span className="pill">{r.complexity}做法</span>
            <span className="pill"><IconClock size={14} /> {r.cookTimeMin} 分钟</span>
            <span className="pill"><IconChef size={14} /> {r.servings} 人份</span>
            <span className="pill"><IconBowl size={14} /> {r.mealTypes.map((m) => mealLabel[m] || m).join(" / ")}</span>
          </div>
          <div className="detail-tools">
            <div className="detail-tool-line">
              <span className="detail-tool-label">做法</span>
              {r.cookingMethods.map((method) => <span className="stamp red" key={method}>{method}</span>)}
            </div>
            <div className="detail-tool-line">
              <span className="detail-tool-label">器材</span>
              {r.equipment.map((tool) => <span className="stamp mustard" key={tool}>{tool}</span>)}
            </div>
          </div>
        </div>
      </div>

      <p className="summary">{r.summary}</p>

      {r.source.url && (
        <p className="muted recipe-source">
          做法来源：<a href={r.source.url} target="_blank" rel="noreferrer">{r.source.name}</a>
          {r.source.license ? ` · ${r.source.license}` : ""}
          {r.source.revision ? ` · 版本 ${r.source.revision.slice(0, 12)}` : ""}
          {"；营养按本项目食材和克数推算。"}
        </p>
      )}

      <div className="cols" style={{ marginBottom: 26 }}>
        <div className="panel">
          <div className="stall-head">
            <h2>每份营养</h2>
            <span className="rule" />
          </div>
          <table className="nutri-table">
            <tbody>
              {nutriRows.map(([k, v]) => (
                <tr key={k}><td>{k}</td><td>{v}</td></tr>
              ))}
            </tbody>
          </table>
          <div className="stamp-row" style={{ marginTop: 14 }}>
            {r.tags.map((t) => <span className="stamp green" key={t}>{t}</span>)}
          </div>
          {r.allergens.length > 0 && (
            <p className="muted" style={{ marginTop: 12, fontSize: 13 }}>
              含过敏原：{r.allergens.join("、")}
            </p>
          )}
        </div>

        <div className="panel">
          <div className="stall-head">
            <h2>食材清单</h2>
            <span className="rule" />
            <span className="hint">按克数备料</span>
          </div>
          <ul className="list-plain">
            {r.ingredients.map((i, idx) => (
              <li key={idx}>
                <span>{i.name}{i.note ? <span className="note">（{i.note}）</span> : null}</span>
                <span className="amt">{i.amount}{i.unit}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: 26 }}>
        <div className="stall-head">
          <h2>做法步骤</h2>
          <span className="rule" />
          <span className="hint"><IconScale size={14} /> 火候与时间都标好了</span>
        </div>
        <ol className="steps">
          {r.steps.map((s, idx) => (
            <li key={idx}>
              <div className="step-no">{idx + 1}</div>
              <div>
                <div>{s.text}</div>
                {(s.heat || s.durationMin) && (
                  <div className="meta">
                    {s.heat ? `火候 · ${s.heat}` : ""}
                    {s.heat && s.durationMin ? "　" : ""}
                    {s.durationMin ? `约 ${s.durationMin} 分钟` : ""}
                  </div>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>

      {r.tips.length > 0 && (
        <div className="tip-box">
          <div className="tip-title"><IconLeaf size={18} /> 师傅说</div>
          <ul>
            {r.tips.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
