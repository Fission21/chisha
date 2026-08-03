from app.recommend import recommend, score_recipe

def make_recipe(rid, meal, kcal, protein, cuisine="中餐", tags=None, allergens=None):
    return {
        "id": rid, "title": rid, "cuisine": cuisine, "mealTypes": [meal],
        "tags": tags or [], "allergens": allergens or [],
        "nutrition": {"energyKCal": kcal, "protein": protein, "fat": 10, "CHO": 50},
    }

def test_recommend_excludes_allergens():
    recipes = [
        make_recipe("a", "lunch", 500, 30, allergens=["虾"]),
        make_recipe("b", "lunch", 500, 35, allergens=[]),
        make_recipe("c", "lunch", 600, 40, allergens=["花生"]),
    ]
    meals = recommend(recipes, 2000, 120, "cut", ["虾"], [])
    lunch = next(m for m in meals if m["meal"] == "lunch")
    ids = {r["id"] for r in lunch["recommendations"]}
    assert "a" not in ids

def test_recommend_returns_top3_per_meal():
    recipes = [make_recipe(f"r{i}", "dinner", 500 + i * 20, 30 + i, cuisine="中餐") for i in range(10)]
    meals = recommend(recipes, 2000, 120, "maintain", [], [])
    dinner = next(m for m in meals if m["meal"] == "dinner")
    assert len(dinner["recommendations"]) == 3

def test_recommend_no_repeat():
    recipes = [make_recipe(f"r{i}", "lunch", 500, 30, cuisine=c) for i, c in enumerate(["中餐", "西式", "日式", "韩式", "泰式", "印度"])]
    meals = recommend(recipes, 2000, 120, "cut", [], [])
    ids = [r["id"] for m in meals for r in m["recommendations"]]
    assert len(ids) == len(set(ids)), "同一道菜不应在多个餐次重复出现"

def test_score_prefers_cuisine():
    r = make_recipe("x", "lunch", 500, 30, cuisine="西式")
    s1 = score_recipe(r, 700, 42, "cut", ["西式"], [], set())
    s2 = score_recipe(r, 700, 42, "cut", ["中餐"], [], set())
    assert s1 > s2
