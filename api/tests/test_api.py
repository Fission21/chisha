from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_recipes_list():
    # 分页接口返回总数（菜谱库主入口）
    r = client.get("/api/recipes", params={"page": 1, "page_size": 100})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 200
    assert len(body["items"]) == 100
    # 兼容旧数组模式有界返回
    legacy = client.get("/api/recipes", params={"limit": 200})
    assert legacy.status_code == 200
    assert len(legacy.json()) <= 100
    # 覆盖全球菜系
    cuisines = {x["cuisine"] for x in body["items"]}
    assert "中餐" in cuisines and "西式" in cuisines

def test_recipes_filter_meal():
    r = client.get("/api/recipes", params={"meal": "breakfast", "limit": 200})
    assert r.status_code == 200
    assert len(r.json()) >= 10

def test_recipes_pagination_and_kitchen_filters():
    r = client.get("/api/recipes", params={
        "page": 1, "page_size": 5, "cooking_method": "烤", "equipment": "烤箱",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1
    assert body["pageSize"] == 5
    assert body["total"] > 0
    assert len(body["items"]) <= 5
    assert all("烤" in item["cookingMethods"] for item in body["items"])
    assert all("烤箱" in item["equipment"] for item in body["items"])
    assert "简单" in body["facets"]["difficulties"]
    assert "healthLabels" in body["facets"]
    assert "严格控油控盐" in body["facets"]["healthLabels"]

def test_recipe_filters_equipment_health_and_nutrition():
    air = client.get("/api/recipes", params={
        "page": 1, "page_size": 20, "equipment": "空气炸锅",
    })
    assert air.status_code == 200
    air_body = air.json()
    assert air_body["total"] > 0
    assert all("空气炸锅" in item["equipment"] for item in air_body["items"])

    strict = client.get("/api/recipes", params={
        "page": 1, "page_size": 100, "health_profile": "strict",
        "max_sodium": 700, "max_added_oil": 10,
    })
    assert strict.status_code == 200
    strict_body = strict.json()
    assert strict_body["total"] > 0
    assert all(item["health"]["strictEligible"] for item in strict_body["items"])
    assert all(item["nutrition"]["sodium"] <= 700 for item in strict_body["items"])
    assert all(item["health"]["addedOilG"] <= 10 for item in strict_body["items"])

    no_egg = client.get("/api/recipes", params={
        "page": 1, "page_size": 100, "exclude_allergens": "鸡蛋",
    })
    assert no_egg.status_code == 200
    assert all("鸡蛋" not in item["allergens"] for item in no_egg.json()["items"])

def test_recipe_available_equipment_mode():
    r = client.get("/api/recipes", params={
        "page": 1, "page_size": 100,
        "equipment": "平底锅,炒锅,汤锅,蒸锅,烤箱,空气炸锅,微波炉,电饭煲,搅拌机,无需加热",
        "equipment_mode": "available",
    })
    assert r.status_code == 200
    body = r.json()
    selected = {"平底锅", "炒锅", "汤锅", "蒸锅", "烤箱", "空气炸锅", "微波炉", "电饭煲", "搅拌机", "无需加热"}
    for item in body["items"]:
        assert set(item["equipment"]) - {"无需加热"} <= selected

def test_recipes_complexity_and_oven_filters():
    simple = client.get("/api/recipes", params={"page": 1, "page_size": 50, "complexity": "简单"})
    assert simple.status_code == 200
    assert simple.json()["total"] > 0
    assert all(item["complexity"] == "简单" for item in simple.json()["items"])
    assert any(item["complexity"] == "复杂" for item in client.get("/api/recipes", params={"page": 1, "page_size": 50}).json()["items"])

    oven = client.get("/api/recipes", params={"page": 1, "page_size": 50, "oven": "true"})
    assert oven.status_code == 200
    assert oven.json()["total"] > 0
    assert all("烤箱" in item["equipment"] for item in oven.json()["items"])

    hard = client.get("/api/recipes", params={"page": 1, "page_size": 50, "complexity": "复杂", "oven": "true"})
    assert hard.json()["total"] > 0

def test_recipes_oven_false_excludes_oven():
    r = client.get("/api/recipes", params={"page": 1, "page_size": 50, "oven": "false"})
    body = r.json()
    assert body["total"] > 0
    assert all("烤箱" not in item["equipment"] for item in body["items"])

def test_recipe_detail():
    r = client.get("/api/recipes", params={"limit": 1})
    rid = r.json()[0]["id"]
    d = client.get(f"/api/recipes/{rid}")
    assert d.status_code == 200
    body = d.json()
    assert body["ingredients"], "菜谱应含食材"
    assert body["steps"], "菜谱应含步骤"
    assert body["tips"], "菜谱应含技巧"
    assert body["nutrition"]["energyKCal"] > 0
    assert body["cookingMethods"]
    assert body["equipment"]

def test_recipe_detail_404():
    r = client.get("/api/recipes/not-exist")
    assert r.status_code == 404

def test_foods_search():
    r = client.get("/api/foods", params={"q": "鸡", "limit": 10})
    assert r.status_code == 200
    assert len(r.json()) > 0

def test_oil_energy_footnote_is_preserved():
    r = client.get("/api/foods", params={"q": "橄榄油", "limit": 10})
    assert r.status_code == 200
    olive_oil = next(item for item in r.json() if item["name"] == "橄榄油")
    assert olive_oil["energyKCal"] == 899.0

def test_howtocook_recipe_has_pinned_source_provenance():
    r = client.get("/api/recipes/howtocook-gyudon")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == {
        "name": "Anduin2017/HowToCook",
        "url": "https://github.com/Anduin2017/HowToCook/blob/c05758fa661ac4efa0361a987b700a351a22159b/dishes/staple/日式肥牛丼饭/日式肥牛丼饭.md",
        "license": "Unlicense",
        "revision": "c05758fa661ac4efa0361a987b700a351a22159b",
    }
    assert body["nutrition"]["energyKCal"] > 0

def test_food_estimate_natural_language_portions():
    r = client.post("/api/foods/estimate", json={
        "query": "一个大苹果，一个中等长度的香蕉，一杯250毫升的牛奶",
    })
    assert r.status_code == 200
    body = r.json()
    assert not body["unmatched"]
    assert [item["food"]["name"] for item in body["items"]] == [
        "苹果（代表值）", "香蕉 [甘蕉]", "纯牛奶（代表值，全脂）",
    ]
    assert [item["amountG"] for item in body["items"]] == [223.0, 118.0, 250.0]
    assert body["total"]["energyKCal"] == 390.4
    assert "估算" in body["notice"]

def test_food_estimate_daily_staples():
    r = client.post("/api/foods/estimate", json={
        "query": "一碗米饭，一个鸡蛋，一片全麦面包，一罐可乐",
    })
    assert r.status_code == 200
    body = r.json()
    assert not body["unmatched"]
    assert [item["food"]["name"] for item in body["items"]] == [
        "米饭（蒸，代表值）", "鸡蛋（代表值）", "全麦面包", "可乐（含糖）",
    ]
    # 一碗米饭 150g、一个鸡蛋 60g、一片全麦面包 35g、一罐可乐 330g
    assert [item["amountG"] for item in body["items"]] == [150.0, 60.0, 35.0, 330.0]

def test_food_estimate_veg_fruit_and_half():
    r = client.post("/api/foods/estimate", json={
        "query": "半个西瓜，一根黄瓜，两颗草莓，两勺白糖",
    })
    assert r.status_code == 200
    body = r.json()
    assert not body["unmatched"]
    assert [item["food"]["name"] for item in body["items"]] == [
        "西瓜（代表值）", "黄瓜（鲜）[胡瓜]", "草莓 [洋莓, 凤阳草莓]", "白糖",
    ]
    assert [item["amountG"] for item in body["items"]] == [1000.0, 250.0, 24.0, 24.0]

def test_food_estimate_ml_density_and_noodle_note():
    r = client.post("/api/foods/estimate", json={
        "query": "一杯豆浆，一小把花生，一碗面条",
    })
    assert r.status_code == 200
    body = r.json()
    assert not body["unmatched"]
    assert [item["food"]["name"] for item in body["items"]] == [
        "豆浆", "花生仁（生）", "挂面（代表值）",
    ]
    assert [item["amountG"] for item in body["items"]] == [250.0, 15.0, 125.0]

def test_food_estimate_reports_unmatched_items_without_guessing():
    r = client.post("/api/foods/estimate", json={"query": "一碗火星果, 200g 苹果"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["amountG"] == 200.0
    assert body["unmatched"] == [{
        "input": "一碗火星果",
        "reason": "没有找到对应食材；可尝试写明食材名称和克数，例如“200g 鸡胸肉”。",
    }]

def test_calorie_plan_generates_day_meals():
    r = client.post("/api/calorie-plan", json={"targetKcal": 2000})
    assert r.status_code == 200
    p = r.json()
    assert p["targetKcal"] == 2000
    assert len(p["meals"]) == 4
    for m in p["meals"]:
        assert m["mealLabel"]
        assert m["targetKcal"] > 0
        assert len(m["recommendations"]) == 3
        for rec in m["recommendations"]:
            assert rec["nutrition"]["energyKCal"] > 0
    # 首选合计应接近目标（±35% 容差，餐次拆分后单菜热量波动大）
    assert 0.65 * 2000 < p["actualKcal"] < 1.35 * 2000
    assert p["shoppingList"], "热量菜谱应返回购物清单"

def test_calorie_plan_meal_subset_and_filters():
    r = client.post("/api/calorie-plan", json={
        "targetKcal": 1500,
        "meals": ["breakfast", "lunch"],
        "allergies": ["鸡蛋"],
        "preferred_cuisines": ["中式"],
    })
    assert r.status_code == 200
    p = r.json()
    assert {m["meal"] for m in p["meals"]} == {"breakfast", "lunch"}
    for m in p["meals"]:
        for rec in m["recommendations"]:
            assert "鸡蛋" not in rec["allergens"]
            assert rec["cuisine"] == "中式"

def test_calorie_plan_strict_health_and_equipment():
    r = client.post("/api/calorie-plan", json={
        "targetKcal": 1800,
        "health_profile": "strict",
        "equipment": ["平底锅", "炒锅", "汤锅", "蒸锅", "无需加热"],
        "equipment_mode": "available",
    })
    assert r.status_code == 200
    p = r.json()
    assert any(m["recommendations"] for m in p["meals"])
    for m in p["meals"]:
        for rec in m["recommendations"]:
            assert rec["health"]["strictEligible"]
            assert set(rec["equipment"]) - {"无需加热"} <= {"平底锅", "炒锅", "汤锅", "蒸锅", "无需加热"}

def test_calorie_plan_rejects_out_of_range():
    r = client.post("/api/calorie-plan", json={"targetKcal": 100})
    assert r.status_code == 422

def test_plan_male_cut():
    body = {
        "sex": "male", "age": 28, "height_cm": 175, "weight_kg": 70,
        "activity_level": "moderate", "goal": "cut",
        "allergies": [], "preferences": [], "preferred_cuisines": [],
    }
    r = client.post("/api/plan", json=body)
    assert r.status_code == 200
    p = r.json()
    assert 1800 < p["daily"]["kcal"] < 2800
    assert p["daily"]["protein"] >= 100
    assert len(p["meals"]) == 4
    assert p["shoppingList"], "计划应返回购物清单"
    for m in p["meals"]:
        assert len(m["recommendations"]) == 3
        assert m["targetKcal"] > 0

def test_plan_female_bulk():
    body = {
        "sex": "female", "age": 25, "height_cm": 165, "weight_kg": 55,
        "activity_level": "active", "goal": "bulk",
        "allergies": [], "preferences": [], "preferred_cuisines": [],
    }
    r = client.post("/api/plan", json=body)
    assert r.status_code == 200
    p = r.json()
    assert p["daily"]["kcal"] > 2000
    assert p["daily"]["protein"] >= 90

def test_plan_allergen_filter():
    body = {
        "sex": "male", "age": 30, "height_cm": 178, "weight_kg": 75,
        "activity_level": "moderate", "goal": "cut",
        "allergies": ["虾", "花生"], "preferences": [], "preferred_cuisines": [],
    }
    r = client.post("/api/plan", json=body)
    assert r.status_code == 200
    for m in r.json()["meals"]:
        for rec in m["recommendations"]:
            assert not (set(rec["allergens"]) & {"虾", "花生"}), f"推荐含过敏原: {rec['title']}"

def test_plan_swap_recipe():
    body = {
        "sex": "male", "age": 28, "height_cm": 175, "weight_kg": 70,
        "activity_level": "moderate", "goal": "cut",
        "allergies": [], "preferences": [], "preferred_cuisines": [],
    }
    plan = client.post("/api/plan", json=body).json()
    lunch = next(m for m in plan["meals"] if m["meal"] == "lunch")
    replace_id = lunch["recommendations"][0]["id"]
    keep_ids = [rec["id"] for m in plan["meals"] for rec in m["recommendations"]]
    swap_body = {"meal": "lunch", "replaceId": replace_id, "keepIds": keep_ids, "user": body}
    r = client.post("/api/plan/swap", json=swap_body)
    assert r.status_code == 200
    data = r.json()
    assert data["recipe"], "应返回新菜谱"
    assert data["recipe"]["id"] != replace_id
    assert data["recipe"]["id"] not in keep_ids
    assert "lunch" in data["recipe"]["mealTypes"]
    assert data["shoppingList"], "应返回更新后的购物清单"

def test_plan_swap_no_candidates():
    body = {
        "sex": "male", "age": 28, "height_cm": 175, "weight_kg": 70,
        "activity_level": "moderate", "goal": "cut",
        "allergies": [], "preferences": [], "preferred_cuisines": ["韩式"],
    }
    plan = client.post("/api/plan", json=body).json()
    keep_ids = [rec["id"] for m in plan["meals"] for rec in m["recommendations"]]
    lunch = next(m for m in plan["meals"] if m["meal"] == "lunch")
    # 韩式午餐菜谱有限，把全部候选都排除后应返回 recipe=None 且不报错
    swap_body = {"meal": "lunch", "replaceId": lunch["recommendations"][0]["id"],
                 "keepIds": keep_ids, "user": body}
    data = client.post("/api/plan/swap", json=swap_body).json()
    assert "recipe" in data and "shoppingList" in data
