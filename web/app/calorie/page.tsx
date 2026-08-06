"use client";

import { FormEvent, useState } from "react";
import { API_URL } from "@/lib/api";

type Nutrition = {
  energyKCal: number;
  protein: number;
  fat: number;
  CHO: number;
  dietaryFiber: number;
  sodium: number;
};

type EstimateItem = {
  input: string;
  food: { id: number; name: string; source: string };
  amountG: number;
  amountNote: string;
  nutrition: Nutrition;
};

type Estimate = {
  items: EstimateItem[];
  unmatched: { input: string; reason: string }[];
  total: Nutrition;
  notice: string;
};

const EXAMPLES = [
  "一个大苹果",
  "一碗米饭，一个煎鸡蛋，100g 鸡胸肉",
  "一杯250毫升的牛奶，一片全麦面包",
  "一罐可乐，半块披萨",
  "半个西瓜，一把花生",
];

export default function CaloriePage() {
  const [query, setQuery] = useState(EXAMPLES[3]);
  const [result, setResult] = useState<Estimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const calculate = async (event?: FormEvent) => {
    event?.preventDefault();
    if (!query.trim()) {
      setError("先写下你吃了什么和份量，例如“一个大苹果”。");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/foods/estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "计算失败");
      setResult(body);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "暂时算不出来，请稍后再试。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <a className="back-link" href="/">← 返回首页</a>
      <header className="masthead" style={{ marginTop: 0 }}>
        <div className="brand">
          <span className="brand-mark">算</span>
          <div>
            <div className="brand-name">食材热量查询</div>
            <div className="brand-sub">把“个 / 根 / 杯 / ml”换成可读的营养估算</div>
          </div>
        </div>
        <nav className="nav">
          <a className="btn ghost" href="/calorie-recipe">热量菜谱</a>
          <a className="btn ghost" href="/recipes">菜谱库</a>
          <a className="btn ghost" href="/diary">饮食记录</a>
        </nav>
      </header>

      <form className="panel section" onSubmit={calculate}>
        <div className="stall-head">
          <h2>今天吃了什么？</h2>
          <span className="rule" />
        </div>
        <p className="muted calorie-intro">用中文逗号分隔多种食材。支持克、毫升，以及水果、蔬菜、蛋奶、米饭、饮料、零食等常见家庭份量（个 / 根 / 颗 / 杯 / 碗 / 罐 / 勺 / 把…）。</p>
        <div className="field">
          <label htmlFor="food-query">食材与份量</label>
          <textarea
            id="food-query"
            rows={3}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="例如：一个大苹果，一根中等香蕉，一杯250毫升的牛奶"
          />
        </div>
        <div className="calorie-examples" aria-label="示例查询">
          {EXAMPLES.map((example) => (
            <button key={example} type="button" className="option" onClick={() => setQuery(example)}>{example}</button>
          ))}
        </div>
        <div className="btn-row">
          <button className="btn" type="submit" disabled={loading}>{loading ? "正在换算…" : "计算热量"}</button>
        </div>
      </form>

      {error && <div className="error section">{error}</div>}

      {result && (
        <section className="rise">
          {result.items.length > 0 && (
            <div className="panel section">
              <div className="stall-head">
                <h2>合计</h2>
                <span className="rule" />
                <span className="hint">估算值</span>
              </div>
              <div className="board calorie-board">
                <Metric value={result.total.energyKCal} unit="kcal" label="热量" />
                <Metric value={result.total.protein} unit="g" label="蛋白质" />
                <Metric value={result.total.CHO} unit="g" label="碳水" />
                <Metric value={result.total.fat} unit="g" label="脂肪" />
                <Metric value={result.total.dietaryFiber} unit="g" label="膳食纤维" />
              </div>
              <p className="muted calorie-notice">{result.notice}</p>
            </div>
          )}

          {result.items.length > 0 && (
            <div className="panel section">
              <div className="stall-head">
                <h2>换算明细</h2>
                <span className="rule" />
              </div>
              <ul className="list-plain estimate-list">
                {result.items.map((item) => (
                  <li key={`${item.input}-${item.food.id}`}>
                    <div>
                      <strong>{item.input}</strong>
                      <div className="muted estimate-note">匹配：{item.food.name} · {item.amountNote}</div>
                      <div className="muted estimate-note">来源：{item.food.source}</div>
                    </div>
                    <div className="estimate-values">
                      <strong>{Math.round(item.nutrition.energyKCal)} kcal</strong>
                      <span>{item.amountG} g · 蛋白 {item.nutrition.protein} g</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.unmatched.length > 0 && (
            <div className="error section">
              <div>
                {result.unmatched.map((item) => <p key={item.input} className="calorie-unmatched"><strong>{item.input}</strong>：{item.reason}</p>)}
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

function Metric({ value, unit, label }: { value: number; unit: string; label: string }) {
  return (
    <div className="cell">
      <div className="num">{Math.round(value)} <small>{unit}</small></div>
      <div className="lbl">{label}</div>
    </div>
  );
}
