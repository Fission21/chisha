# 推荐引擎：规则打分 + 单日推荐 + 一周餐单
MEAL_SPLIT = [("breakfast", "早餐", 0.30), ("lunch", "午餐", 0.35),
              ("dinner", "晚餐", 0.25), ("snack", "加餐", 0.10)]

GOAL_TAGS = {
    "cut": ["减脂", "低碳水", "低脂", "低卡", "高蛋白"],
    "bulk": ["增肌", "高蛋白", "优质脂肪"],
    "maintain": ["高蛋白", "低脂"],
}

def score_recipe(recipe, meal_kcal: float, meal_protein: float, goal: str,
                 preferred_cuisines, chosen_cuisines: list, chosen_ids: set) -> float:
    n = recipe["nutrition"]
    kcal = n.get("energyKCal", 0) or 1
    protein = n.get("protein", 0)
    diff = abs(kcal - meal_kcal) / meal_kcal
    kcal_score = max(0.0, 1.0 - diff * 1.4)
    prot_score = min(1.0, protein / max(meal_protein, 1))
    goal_tags = GOAL_TAGS.get(goal, [])
    tag_score = sum(1 for t in recipe.get("tags", []) if t in goal_tags) / max(len(goal_tags), 1)
    cuisine = recipe.get("cuisine", "")
    cuisine_score = 1.0 if (preferred_cuisines and cuisine in preferred_cuisines) else 0.0
    diversity = 0.6 if cuisine not in chosen_cuisines else 0.0
    if recipe["id"] in chosen_ids:
        return -1.0
    score = (kcal_score * 0.45 + prot_score * 0.30 + tag_score * 0.15
             + cuisine_score * 0.05 + diversity * 0.05)
    return round(score, 4)

def recommend(recipes, daily_kcal: float, daily_protein: float, goal: str,
              allergies, preferred_cuisines) -> list:
    meals_out = []
    chosen_ids = set()
    chosen_cuisines = []
    for meal, label, split in MEAL_SPLIT:
        meal_kcal = daily_kcal * split
        meal_protein = daily_protein * split
        candidates = [r for r in recipes if meal in r.get("mealTypes", [])]
        scored = []
        for r in candidates:
            if set(r.get("allergens", [])) & set(allergies):
                continue
            s = score_recipe(r, meal_kcal, meal_protein, goal, preferred_cuisines,
                             chosen_cuisines, chosen_ids)
            if s >= 0:
                scored.append((s, r))
        scored.sort(key=lambda x: -x[0])
        top = scored[:3]
        meal_recs = []
        for s, r in top:
            meal_recs.append(r)
            chosen_ids.add(r["id"])
            chosen_cuisines.append(r.get("cuisine", ""))
        meals_out.append({
            "meal": meal,
            "mealLabel": label,
            "targetKcal": round(meal_kcal),
            "targetProtein": round(meal_protein, 1),
            "recommendations": meal_recs,
        })
    return meals_out

def _pick_one(candidates, meal_kcal, meal_protein, goal, preferred_cuisines, chosen_cuisines, used):
    scored = []
    for r in candidates:
        if r["id"] in used:
            continue
        s = score_recipe(r, meal_kcal, meal_protein, goal, preferred_cuisines, chosen_cuisines, used)
        if s >= 0:
            scored.append((s, r))
    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else None

def recommend_week(recipes, daily_kcal: float, daily_protein: float, goal: str,
                   allergies, preferred_cuisines, n_days: int = 7) -> dict:
    """生成一周餐单：每天每餐 1 道，整周尽量不重复；并汇总购物清单。"""
    used = set()
    week = []
    week_picks = []
    for d in range(n_days):
        chosen_cuisines = []
        meals = []
        day_picks = []
        for meal, label, split in MEAL_SPLIT:
            meal_kcal = daily_kcal * split
            meal_protein = daily_protein * split
            candidates = [r for r in recipes if meal in r.get("mealTypes", [])
                          and not (set(r.get("allergens", [])) & set(allergies))]
            pick = _pick_one(candidates, meal_kcal, meal_protein, goal, preferred_cuisines,
                             chosen_cuisines, used)
            if pick is None and candidates:
                # 允许重复：热量最接近的兜底
                pick = sorted(candidates, key=lambda r: abs(r["nutrition"].get("energyKCal", 0) - meal_kcal))[0]
            meals.append({
                "meal": meal, "mealLabel": label,
                "targetKcal": round(meal_kcal), "targetProtein": round(meal_protein, 1),
                "recommendations": [pick] if pick else [],
            })
            if pick:
                used.add(pick["id"])
                chosen_cuisines.append(pick.get("cuisine", ""))
                day_picks.append(pick)
        week.append(meals)
        week_picks.extend(day_picks)

    agg = {}
    for r in week_picks:
        servings = max(1, r.get("servings", 1))
        for ing in r.get("ingredients", []):
            key = (ing.get("name", ""), ing.get("unit", "g"), ing.get("note", ""))
            amt = ing.get("amount", 0) / servings
            if key not in agg:
                agg[key] = {"name": key[0], "unit": key[1], "note": key[2], "amount": 0.0}
            agg[key]["amount"] += amt
    shopping = [{"name": v["name"], "unit": v["unit"], "note": v["note"],
                 "amount": round(v["amount"], 1)} for v in agg.values()]
    shopping.sort(key=lambda x: -x["amount"])
    return {"days": week, "shoppingList": shopping}
