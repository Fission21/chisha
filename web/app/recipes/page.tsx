"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";
import { IconClock, IconArrow, IconFlame, IconProtein, IconCarbs, IconFat, IconStar } from "@/components/icons";
import DishMark from "@/components/dish-mark";
import { toggleFavorite, syncFavoritesFromServer, pushFavoritesToServer } from "@/lib/favorites";
import AuthNav from "@/components/auth-nav";

type Nutrition = { energyKCal: number; protein: number; fat: number; CHO: number };
type RecipeSummary = {
  id: string; title: string; titleEn: string; cuisine: string; difficulty: string;
  complexity: string;
  cookingMethods: string[]; equipment: string[];
  cookTimeMin: number; servings: number; summary: string; coverEmoji: string;
  mealTypes: string[]; tags: string[]; allergens: string[]; nutrition: Nutrition;
};
type RecipeFacets = {
  cuisines: string[]; difficulties: string[]; cookingMethods: string[]; equipment: string[];
};
type RecipePage = {
  items: RecipeSummary[]; total: number; page: number; pageSize: number; totalPages: number;
  facets: RecipeFacets;
};
type FilterOption = { value: string; label: string };

const PAGE_SIZE = 12;
const EMPTY_FACETS: RecipeFacets = { cuisines: [], difficulties: [], cookingMethods: [], equipment: [] };
const MEALS: FilterOption[] = [
  { value: "", label: "全部" },
  { value: "breakfast", label: "早餐" },
  { value: "lunch", label: "午餐" },
  { value: "dinner", label: "晚餐" },
  { value: "snack", label: "加餐" },
];
const DIFFICULTY_ORDER = ["简单", "中等", "困难"];
const COMPLEXITY_OPTIONS: FilterOption[] = [
  { value: "", label: "全部做法" },
  { value: "简单", label: "简单" },
  { value: "复杂", label: "复杂" },
];
const OVEN_OPTIONS: FilterOption[] = [
  { value: "", label: "全部工具" },
  { value: "yes", label: "需要烤箱" },
  { value: "no", label: "不需要烤箱" },
];

export default function RecipesPage() {
  const [list, setList] = useState<RecipeSummary[]>([]);
  const [facets, setFacets] = useState<RecipeFacets>(EMPTY_FACETS);
  const [meal, setMeal] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [complexity, setComplexity] = useState("");
  const [cookingMethod, setCookingMethod] = useState("");
  const [equipment, setEquipment] = useState("");
  const [oven, setOven] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [favs, setFavs] = useState<string[]>([]);
  const [onlyFav, setOnlyFav] = useState(false);

  useEffect(() => { syncFavoritesFromServer().then(setFavs); }, []);

  // 收藏是本地数据；只在收藏筛选打开时用它触发重新分页，普通列表不会因点星而重载。
  const favoriteKey = onlyFav ? favs.join(",") : "";
  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      setLoading(true); setError("");
      try {
        const params = new URLSearchParams();
        if (onlyFav) {
          params.set("limit", "100");
        } else {
          params.set("page", String(page));
          params.set("page_size", String(PAGE_SIZE));
        }
        if (meal) params.set("meal", meal);
        if (cuisine) params.set("cuisine", cuisine);
        if (difficulty) params.set("difficulty", difficulty);
        if (complexity) params.set("complexity", complexity);
        if (cookingMethod) params.set("cooking_method", cookingMethod);
        if (equipment) params.set("equipment", equipment);
        if (oven) params.set("oven", oven === "yes" ? "true" : "false");

        const res = await fetch(`${API_URL}/api/recipes?${params}`, { signal: controller.signal });
        if (!res.ok) throw new Error("加载失败");
        const payload: RecipePage | RecipeSummary[] = await res.json();
        const source = Array.isArray(payload) ? payload : payload.items;
        if (!Array.isArray(payload)) setFacets(payload.facets);

        if (onlyFav) {
          const favoriteItems = source.filter((recipe) => favs.includes(recipe.id));
          const favoriteTotalPages = Math.ceil(favoriteItems.length / PAGE_SIZE);
          const currentPage = favoriteTotalPages > 0 ? Math.min(page, favoriteTotalPages) : 1;
          setTotal(favoriteItems.length);
          setTotalPages(favoriteTotalPages);
          setList(favoriteItems.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));
          if (currentPage !== page) setPage(currentPage);
        } else {
          if (Array.isArray(payload)) throw new Error("分页数据格式错误");
          setTotal(payload.total);
          setTotalPages(payload.totalPages);
          setList(payload.items);
        }
      } catch (err) {
        if (!controller.signal.aborted) setError("菜谱柜没打开，请稍后再试。");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => controller.abort();
  }, [meal, cuisine, difficulty, complexity, cookingMethod, equipment, oven, page, onlyFav, favoriteKey]);

  const difficultyOptions: FilterOption[] = [
    { value: "", label: "全部难度" },
    ...DIFFICULTY_ORDER.filter((value) => facets.difficulties.includes(value)).map((value) => ({ value, label: value })),
  ];
  const cuisineOptions: FilterOption[] = [
    { value: "", label: "全部菜系" },
    ...facets.cuisines.map((value) => ({ value, label: value })),
  ];
  const methodOptions: FilterOption[] = [
    { value: "", label: "全部方式" },
    ...facets.cookingMethods.map((value) => ({ value, label: value })),
  ];
  const equipmentOptions: FilterOption[] = [
    { value: "", label: "全部器材" },
    ...facets.equipment.map((value) => ({ value, label: value })),
  ];

  const choose = (setter: (value: string) => void, value: string) => {
    setter(value);
    setPage(1);
  };
  const clearFilters = () => {
    setMeal(""); setCuisine(""); setDifficulty(""); setComplexity(""); setCookingMethod(""); setEquipment("");
    setOven(""); setOnlyFav(false); setPage(1);
  };

  return (
    <div className="container">
      <a className="back-link" href="/"><IconArrow size={15} /> 返回首页</a>
      <header className="masthead" style={{ marginTop: 0 }}>
        <div className="brand">
          <span className="brand-mark">吃</span>
          <div>
            <div className="brand-name">菜谱库</div>
            <div className="brand-sub">中餐 + 全球做法 · 共 {total} 道，每道都算好了营养</div>
          </div>
        </div>
      </header>

      <div style={{ marginBottom: 16 }}><AuthNav /></div>

      <div className="panel section filter-panel">
        <FilterGroup label="餐次" options={MEALS} value={meal} onChange={(value) => choose(setMeal, value)} />
        <FilterGroup label="菜系" options={cuisineOptions} value={cuisine} onChange={(value) => choose(setCuisine, value)} />
        <FilterGroup label="难度" options={difficultyOptions} value={difficulty} onChange={(value) => choose(setDifficulty, value)} />
        <FilterGroup label="做法" options={COMPLEXITY_OPTIONS} value={complexity} onChange={(value) => choose(setComplexity, value)} />
        <FilterGroup label="烹饪方式" options={methodOptions} value={cookingMethod} onChange={(value) => choose(setCookingMethod, value)} />
        <FilterGroup label="器材" options={equipmentOptions} value={equipment} onChange={(value) => choose(setEquipment, value)} />
        <FilterGroup label="工具" options={OVEN_OPTIONS} value={oven} onChange={(value) => choose(setOven, value)} />
        <div className="filter-row filter-actions">
          <span className="filter-label">收藏</span>
          <div className="option-row">
            <button type="button" className={`option ${onlyFav ? "on" : ""}`} onClick={() => { setOnlyFav(!onlyFav); setPage(1); }} aria-pressed={onlyFav}>
              <IconStar size={15} filled={onlyFav} /> 只看收藏 {favs.length > 0 ? `(${favs.length})` : ""}
            </button>
            {(meal || cuisine || difficulty || complexity || cookingMethod || equipment || oven || onlyFav) && (
              <button type="button" className="btn ghost filter-clear" onClick={clearFilters}>清空筛选</button>
            )}
          </div>
        </div>
      </div>

      {loading && <div className="panel section"><div className="loading">正在翻菜谱…</div></div>}
      {error && (
        <div className="error section">
          <IconAlertInline />
          <div>
            {error}{" "}
            <button className="btn ghost" style={{ marginLeft: 8, padding: "4px 12px" }} onClick={() => window.location.reload()}>重试</button>
          </div>
        </div>
      )}
      {!loading && !error && (
        <div className="panel section">
          {list.length === 0 ? (
            <div className="empty">
              没有符合条件的菜谱，换个做法或器材试试。{" "}
              <button type="button" className="btn ghost" style={{ padding: "5px 12px", fontSize: 13 }} onClick={clearFilters}>清空筛选</button>
            </div>
          ) : (
            list.map((r) => {
              const fav = favs.includes(r.id);
              return (
                <div className="menu-row" key={r.id}>
                  <DishMark title={r.title} size={44} />
                  <div className="menu-body">
                    <div className="menu-title"><a href={`/recipes/${r.id}`}>{r.title}</a></div>
                    <div className="menu-meta">
                      <span>{r.cuisine}</span><span>·</span><span>{r.difficulty}</span><span>·</span>
                      <span>{r.complexity}做法</span><span>·</span>
                      <span><IconClock size={13} style={{ verticalAlign: -1 }} /> {r.cookTimeMin} 分钟</span>
                    </div>
                    <div className="menu-nutri">
                      <span className="price kcal"><IconFlame size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.energyKCal)}</b> kcal</span>
                      <span className="price protein"><IconProtein size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.protein)}</b> g 蛋白</span>
                      <span className="price carb"><IconCarbs size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.CHO)}</b> g 碳水</span>
                      <span className="price fat"><IconFat size={13} style={{ verticalAlign: -1 }} /> <b>{Math.round(r.nutrition.fat)}</b> g 脂肪</span>
                    </div>
                    <div className="stamp-row">
                      {r.tags.slice(0, 3).map((t) => <span className="stamp green" key={`tag-${t}`}>{t}</span>)}
                      {r.cookingMethods.slice(0, 2).map((method) => <span className="stamp red" key={`method-${method}`}>{method}</span>)}
                      {r.equipment.slice(0, 2).map((tool) => <span className="stamp mustard" key={`equipment-${tool}`}>{tool}</span>)}
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn ghost"
                    style={{ padding: "8px 10px", fontSize: 13, flexShrink: 0 }}
                    onClick={() => { const ids = toggleFavorite(r.id); setFavs(ids); pushFavoritesToServer(ids); }}
                    aria-pressed={fav}
                    aria-label={fav ? `取消收藏${r.title}` : `收藏${r.title}`}
                  >
                    <IconStar size={15} filled={fav} />
                  </button>
                </div>
              );
            })
          )}
          {totalPages > 0 && <Pagination page={page} totalPages={totalPages} total={total} onChange={setPage} />}
        </div>
      )}
    </div>
  );
}

function FilterGroup({ label, options, value, onChange }: { label: string; options: FilterOption[]; value: string; onChange: (value: string) => void }) {
  return (
    <div className="filter-row">
      <span className="filter-label">{label}</span>
      <div className="option-row">
        {options.map((option) => (
          <button type="button" key={option.value} className={`option ${value === option.value ? "on" : ""}`} onClick={() => onChange(option.value)} aria-pressed={value === option.value}>
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function Pagination({ page, totalPages, total, onChange }: { page: number; totalPages: number; total: number; onChange: (page: number) => void }) {
  const pages = Array.from({ length: totalPages }, (_, index) => index + 1).filter((number) => (
    totalPages <= 7 || number === 1 || number === totalPages || Math.abs(number - page) <= 1
  ));
  const visiblePages: (number | "ellipsis")[] = [];
  pages.forEach((number, index) => {
    if (index > 0 && number - pages[index - 1] > 1) visiblePages.push("ellipsis");
    visiblePages.push(number);
  });

  const move = (nextPage: number) => {
    onChange(nextPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <nav className="pagination" aria-label="菜谱分页">
      <button type="button" className="btn ghost" onClick={() => move(page - 1)} disabled={page <= 1}>上一页</button>
      <div className="pagination-pages">
        {visiblePages.map((number, index) => number === "ellipsis" ? (
          <span className="pagination-ellipsis" key={`ellipsis-${index}`}>…</span>
        ) : (
          <button type="button" key={number} className={`pagination-page ${number === page ? "on" : ""}`} onClick={() => move(number)} aria-current={number === page ? "page" : undefined}>
            {number}
          </button>
        ))}
      </div>
      <button type="button" className="btn ghost" onClick={() => move(page + 1)} disabled={page >= totalPages}>下一页</button>
      <span className="pagination-total">共 {total} 道</span>
    </nav>
  );
}

function IconAlertInline() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 2 }}>
      <path d="M12 3.5 21 20H3L12 3.5Z" /><path d="M12 10v4.5M12 17.5v.5" />
    </svg>
  );
}
