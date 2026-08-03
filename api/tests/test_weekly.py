from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def _input(**kw):
    base = {
        "sex": "male", "age": 28, "height_cm": 175, "weight_kg": 70,
        "activity_level": "moderate", "goal": "cut",
        "allergies": [], "preferences": [], "preferred_cuisines": [],
    }
    base.update(kw)
    return base

def test_weekly_plan_shape():
    r = client.post("/api/weekly-plan", json=_input())
    assert r.status_code == 200
    w = r.json()
    assert len(w["days"]) == 7
    for day in w["days"]:
        assert day["date"]
        assert len(day["meals"]) == 4
        for m in day["meals"]:
            assert len(m["recommendations"]) == 1
            assert m["recommendations"][0]["id"]
    assert w["shoppingList"], "购物清单不应为空"
    for item in w["shoppingList"]:
        assert item["amount"] > 0

def test_weekly_plan_no_repeat():
    r = client.post("/api/weekly-plan", json=_input())
    w = r.json()
    ids = [m["recommendations"][0]["id"] for day in w["days"] for m in day["meals"]]
    assert len(ids) == len(set(ids)), "一周内菜谱不应重复"

def test_weekly_plan_allergen():
    r = client.post("/api/weekly-plan", json=_input(allergies=["虾", "花生"]))
    w = r.json()
    for day in w["days"]:
        for m in day["meals"]:
            for rec in m["recommendations"]:
                assert not (set(rec["allergens"]) & {"虾", "花生"})

def test_weekly_plan_per_meal_coverage():
    r = client.post("/api/weekly-plan", json=_input(goal="bulk"))
    w = r.json()
    for meal in ["breakfast", "lunch", "dinner", "snack"]:
        count = sum(1 for d in w["days"] for m in d["meals"] if m["meal"] == meal and m["recommendations"])
        assert count == 7, f"{meal} 应 7 天都有推荐，实际 {count}"
