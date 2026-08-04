from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_recipes_list():
    r = client.get("/api/recipes", params={"limit": 200})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 70
    # 覆盖全球菜系
    cuisines = {x["cuisine"] for x in data}
    for c in ["中餐", "西式", "日式", "泰式", "墨西哥", "印度"]:
        assert c in cuisines, f"缺少菜系 {c}"

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
