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
