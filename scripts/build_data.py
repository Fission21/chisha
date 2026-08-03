# -*- coding: utf-8 -*-
"""吃啥 - 数据管道：将原始食物成分表 + 全球食材 + 菜谱合并为 processed JSON。
用法: python scripts/build_data.py
"""
import json, re, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "china-food"
GLOBAL = ROOT / "data" / "global_foods.json"
RECIPE_DIRS = [ROOT / "data" / "recipes"]
OUT = ROOT / "data" / "processed"

NUTRIENT_FIELDS = ["energyKCal", "protein", "fat", "CHO", "dietaryFiber",
                  "cholesterol", "vitaminA", "vitaminC", "vitaminE", "Ca", "P", "K", "Na", "Mg", "Fe", "Zn", "Se"]
RAW_NUTRIENTS = {"energyKCal": "energyKCal", "energyKJ": "energyKJ", "protein": "protein", "fat": "fat",
                 "CHO": "CHO", "dietaryFiber": "dietaryFiber", "cholesterol": "cholesterol",
                 "vitaminA": "vitaminA", "vitaminC": "vitaminC", "vitaminE": "vitaminETotal",
                 "Ca": "Ca", "P": "P", "K": "K", "Na": "Na", "Mg": "Mg", "Fe": "Fe", "Zn": "Zn", "Se": "Se"}

def to_num(v):
    if v is None: return 0.0
    s = str(v).strip()
    if s in ("", "—", "-", "Tr", "tr", "微量"): return 0.0
    s = s.replace("…", "")
    try: return float(s)
    except ValueError: return 0.0

def norm(s):
    if not s: return ""
    out = []
    for ch in s:
        o = ord(ch)
        if o == 0x3000: o = 32
        elif 0xFF01 <= o <= 0xFF5E: o -= 0xFEE0
        out.append(chr(o))
    t = "".join(out).lower()
    return re.sub(r"\s+", "", t)

def strip_brackets(s):
    t = norm(s)
    t = re.sub(r"[\[（(].*?[\])）)]", "", t)
    return t

def load_foods():
    foods = []
    for f in RAW.glob("merged_*.json"):
        foods.extend(json.loads(f.read_bytes().decode("utf-8-sig")))
    records = []
    for x in foods:
        rec = {"code": str(x.get("foodCode", "")), "name": str(x.get("foodName", "")),
               "edible": to_num(x.get("edible")), "source": "中国食物成分表(第6版)"}
        for k, rawk in RAW_NUTRIENTS.items():
            rec[k] = to_num(x.get(rawk))
        rec["sodium"] = rec["Na"]
        records.append(rec)
    return records

def load_global():
    data = json.loads(GLOBAL.read_bytes().decode("utf-8-sig"))
    records = []
    for x in data:
        rec = {"code": "", "name": str(x.get("name", "")), "edible": 100.0, "source": x.get("source", "global")}
        for k in ["energyKCal", "protein", "fat", "CHO", "dietaryFiber", "sodium"]:
            rec[k] = to_num(x.get(k))
        for k in ["cholesterol", "vitaminA", "vitaminC", "vitaminE", "Ca", "P", "K", "Na", "Mg", "Fe", "Zn", "Se"]:
            rec.setdefault(k, 0.0)
        records.append(rec)
    return records

def build_indexes(foods, globals_):
    idx_food = {}
    idx_food_full = {}
    for f in foods:
        idx_food_full.setdefault(norm(f["name"]), f)
        idx_food.setdefault(strip_brackets(f["name"]), f)
    idx_global = {}
    for g in globals_:
        idx_global.setdefault(norm(g["name"]), g)
        idx_global.setdefault(strip_brackets(g["name"]), g)
    return idx_food, idx_food_full, idx_global

def resolve(ing, idx_food, idx_food_full, idx_global, foods, globals_):
    name = ing.get("name", "")
    ref = ing.get("ref")
    if ref:
        rn = norm(ref); rs = strip_brackets(ref)
        if rs in idx_food: return idx_food[rs], "food"
        if rn in idx_food_full: return idx_food_full[rn], "food"
        if rn in idx_global: return idx_global[rn], "global"
        hits = [f for f in foods if len(rs) >= 2 and (rs in strip_brackets(f["name"]) or strip_brackets(f["name"]) in rs)]
        if hits:
            hits.sort(key=lambda f: len(f["name"]))
            return hits[0], "food-fuzzy"
        hits = [g for g in globals_ if len(rs) >= 2 and rs in norm(g["name"])]
        if hits:
            hits.sort(key=lambda g: len(g["name"]))
            return hits[0], "global-fuzzy"
        return None, "unresolved"
    else:
        nn = norm(name); ns = strip_brackets(name)
        if ns in idx_food: return idx_food[ns], "food"
        if nn in idx_global: return idx_global[nn], "global"
        hits = [f for f in foods if len(ns) >= 2 and ns in strip_brackets(f["name"])]
        if hits:
            hits.sort(key=lambda f: len(f["name"]))
            return hits[0], "food-fuzzy"
        hits = [g for g in globals_ if len(ns) >= 2 and ns in norm(g["name"])]
        if hits:
            hits.sort(key=lambda g: len(g["name"]))
            return hits[0], "global-fuzzy"
        return None, "unresolved"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    foods = load_foods()
    globals_ = load_global()
    idx_food, idx_food_full, idx_global = build_indexes(foods, globals_)
    print(f"foods(中): {len(foods)}, global: {len(globals_)}")

    recipes = []
    for d in RECIPE_DIRS:
        for f in sorted(d.glob("*.json")):
            recipes.extend(json.loads(f.read_bytes().decode("utf-8-sig")))

    # 先全部解析，收集问题
    all_resolved = []
    problems = []
    for r in recipes:
        resolved = []
        for ing in r.get("ingredients", []):
            res, how = resolve(ing, idx_food, idx_food_full, idx_global, foods, globals_)
            resolved.append((res, how))
            if res is None:
                problems.append((r.get("id"), ing.get("name"), ing.get("ref", "")))
        all_resolved.append(resolved)

    if problems:
        print("== UNRESOLVED INGREDIENTS ==")
        for p in problems:
            print(p)
        sys.exit(1)

    out_recipes = []
    for r, resolved in zip(recipes, all_resolved):
        total = {k: 0.0 for k in NUTRIENT_FIELDS}
        total["sodium"] = 0.0
        items = []
        for ing, (res, how) in zip(r.get("ingredients", []), resolved):
            amount = to_num(ing.get("amount"))
            factor = amount / 100.0
            items.append({
                "name": ing.get("name", ""),
                "unit": ing.get("unit", "g"),
                "amount": amount,
                "note": ing.get("note", ""),
                "food": {"name": res["name"], "source": res["source"], "code": res.get("code", "")},
                "match": how,
            })
            for k in NUTRIENT_FIELDS:
                total[k] += res[k] * factor
            total["sodium"] += res.get("sodium", res.get("Na", 0.0)) * factor
        servings = max(1, int(r.get("servings", 1)))
        per_serving = {k: round(total[k] / servings, 1) for k in NUTRIENT_FIELDS}
        per_serving["sodium"] = round(total["sodium"] / servings, 1)
        recipe_out = {
            "id": r["id"], "title": r["title"], "titleEn": r.get("titleEn", ""),
            "cuisine": r.get("cuisine", ""), "mealTypes": r.get("mealTypes", []),
            "difficulty": r.get("difficulty", ""), "cookTimeMin": r.get("cookTimeMin", 0),
            "servings": servings, "summary": r.get("summary", ""), "coverEmoji": r.get("coverEmoji", ""),
            "ingredients": items, "steps": r.get("steps", []), "tips": r.get("tips", []),
            "tags": r.get("tags", []), "allergens": r.get("allergens", []),
            "nutrition": per_serving,
        }
        out_recipes.append(recipe_out)

    print(f"recipes: {len(out_recipes)}")
    all_foods = foods + [dict(g, source=g["source"]) for g in globals_]
    with open(OUT / "foods.json", "w", encoding="utf-8") as f:
        json.dump(all_foods, f, ensure_ascii=False, indent=1)
    with open(OUT / "recipes.json", "w", encoding="utf-8") as f:
        json.dump(out_recipes, f, ensure_ascii=False, indent=1)
    print("written:", OUT / "foods.json", OUT / "recipes.json")

if __name__ == "__main__":
    main()
