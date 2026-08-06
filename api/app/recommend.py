# 推荐引擎：规则打分 + 单日推荐 + 一周餐单
import random

MEAL_SPLIT = [("breakfast", "早餐", 0.30), ("lunch", "午餐", 0.35),
              ("dinner", "晚餐", 0.25), ("snack", "加餐", 0.10)]

GOAL_TAGS = {
    "cut": ["减脂", "低碳水", "低脂", "低卡", "高蛋白"],
    "bulk": ["增肌", "高蛋白", "优质脂肪"],
    "maintain": ["高蛋白", "低脂"],
}

ALLERGEN_GROUPS = {
    "牛奶": {"牛奶", "乳制品"},
    "乳制品": {"牛奶", "乳制品"},
    "虾": {"虾", "贝类"},
    "贝类": {"虾", "贝类"},
    "海鲜": {"虾", "鱼", "贝类"},
}


def allergens_overlap(recipe_allergens, user_allergies) -> bool:
    recipe_set = set(recipe_allergens or [])
    expanded = set()
    for allergy in user_allergies or []:
        expanded.update(ALLERGEN_GROUPS.get(allergy, {allergy}))
    return bool(recipe_set & expanded)


def health_allowed(recipe, health_profile: str) -> bool:
    if health_profile in {"strict", "strict_healthy"}:
        return bool((recipe.get("health") or {}).get("strictEligible", False))
    return True


def equipment_allowed(recipe, selected_equipment, equipment_mode: str = "available") -> bool:
    selected = set(selected_equipment or [])
    if not selected:
        return True
    required = set(recipe.get("equipment", []))
    if equipment_mode == "available":
        return (required - {"无需加热"}).issubset(selected)
    if equipment_mode == "all":
        return selected.issubset(required)
    return bool(required & selected)

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
              allergies, preferred_cuisines, health_profile: str = "balanced") -> list:
    meals_out = []
    chosen_ids = set()
    chosen_cuisines = []
    for meal, label, split in MEAL_SPLIT:
        meal_kcal = daily_kcal * split
        meal_protein = daily_protein * split
        candidates = [r for r in recipes
                      if meal in r.get("mealTypes", [])
                      and health_allowed(r, health_profile)]
        if preferred_cuisines:
            candidates = [r for r in candidates if r.get("cuisine", "") in preferred_cuisines]
        scored = []
        for r in candidates:
            if allergens_overlap(r.get("allergens", []), allergies):
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

# 每千卡热量对应的蛋白质参考（g）：用于热量菜谱的蛋白目标展示。
PROTEIN_PER_KCAL = 0.06

def recommend_for_calories(recipes, target_kcal: float, goal: str, allergies,
                           preferred_cuisines, meal_keys=None, top_n: int = 3,
                           health_profile: str = "balanced", equipment=None,
                           equipment_mode: str = "available") -> dict:
    """按目标热量生成一天菜谱：每餐按固定比例拆分，各挑热量最接近的 top_n 道。

    与推荐引擎的差异：不按身体档案，只按用户输入的目标热量；排序只看热量贴近度。
    """
    meals = list(MEAL_SPLIT) if not meal_keys else [m for m in MEAL_SPLIT if m[0] in meal_keys]
    if not meals:
        meals = list(MEAL_SPLIT)
    total_split = sum(split for _, _, split in meals)
    used: set = set()
    out = []
    picks = []
    for meal, label, split in meals:
        meal_kcal = target_kcal * split / total_split
        meal_protein = meal_kcal * PROTEIN_PER_KCAL
        candidates = [r for r in recipes
                      if meal in r.get("mealTypes", [])
                      and r["id"] not in used
                      and health_allowed(r, health_profile)
                      and equipment_allowed(r, equipment, equipment_mode)
                      and not allergens_overlap(r.get("allergens", []), allergies)]
        if preferred_cuisines:
            candidates = [r for r in candidates if r.get("cuisine", "") in preferred_cuisines]
        scored = sorted(candidates,
                        key=lambda r: abs(r["nutrition"].get("energyKCal", 0) - meal_kcal))
        top = scored[:top_n]
        meal_recs = []
        for r in top:
            meal_recs.append(r)
            used.add(r["id"])
        out.append({
            "meal": meal, "mealLabel": label,
            "targetKcal": round(meal_kcal), "targetProtein": round(meal_protein, 1),
            "recommendations": meal_recs,
        })
        if top:
            picks.append(top[0])
    actual_kcal = sum(r["nutrition"].get("energyKCal", 0) for r in picks)
    actual_protein = sum(r["nutrition"].get("protein", 0) for r in picks)
    return {
        "meals": out,
        "actualKcal": round(actual_kcal, 1),
        "actualProtein": round(actual_protein, 1),
        "shoppingList": aggregate_shopping_list(picks),
    }

def aggregate_shopping_list(recipes: list) -> list:
    """按每道菜 1 人份汇总购物清单（复用一周餐单的聚合口径）。"""
    agg = {}
    for r in recipes:
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
    return shopping

def pick_swap_recipe(recipes, meal, meal_kcal, meal_protein, goal,
                     allergies, preferred_cuisines, exclude_ids,
                     health_profile: str = "balanced"):
    """「换一道」：同餐次、同条件，从排除列表之外挑一道，在前几名里随机换口味。"""
    candidates = [r for r in recipes
                  if meal in r.get("mealTypes", [])
                  and r["id"] not in exclude_ids
                  and health_allowed(r, health_profile)
                  and not allergens_overlap(r.get("allergens", []), allergies)]
    if preferred_cuisines:
        candidates = [r for r in candidates if r.get("cuisine", "") in preferred_cuisines]
    if not candidates:
        return None
    scored = []
    for r in candidates:
        s = score_recipe(r, meal_kcal, meal_protein, goal, preferred_cuisines, [], set())
        scored.append((s, r))
    scored.sort(key=lambda x: -x[0])
    return random.choice(scored[:5])[1]

def recommend_week(recipes, daily_kcal: float, daily_protein: float, goal: str,
                   allergies, preferred_cuisines, n_days: int = 7,
                   health_profile: str = "balanced") -> dict:
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
                          and health_allowed(r, health_profile)
                          and not allergens_overlap(r.get("allergens", []), allergies)]
            if preferred_cuisines:
                candidates = [r for r in candidates if r.get("cuisine", "") in preferred_cuisines]
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
