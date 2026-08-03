# 营养计算：BMR / TDEE / 每日宏量营养素目标
ACTIVITY_FACTORS = {
    "sedentary": 1.2,   # 久坐
    "light": 1.375,     # 轻度活动
    "moderate": 1.55,   # 中度活动（规律运动3-5次/周）
    "active": 1.725,    # 高度活动
    "very": 1.9,        # 极高活动
}

GOAL_ADJUST = {"cut": -350, "maintain": 0, "bulk": 350}
GOAL_PROTEIN = {"cut": 2.0, "maintain": 1.7, "bulk": 1.9}   # g/kg
FAT_PER_KG = {"cut": 0.7, "maintain": 0.9, "bulk": 1.0}     # g/kg

MEAL_SPLIT = [
    ("breakfast", "早餐", 0.30),
    ("lunch", "午餐", 0.35),
    ("dinner", "晚餐", 0.25),
    ("snack", "加餐", 0.10),
]

def bmr_mifflin(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161

def daily_targets(sex: str, weight_kg: float, height_cm: float, age: int,
                  activity_level: str, goal: str) -> dict:
    bmr = bmr_mifflin(sex, weight_kg, height_cm, age)
    factor = ACTIVITY_FACTORS.get(activity_level, 1.55)
    tdee = bmr * factor
    kcal = tdee + GOAL_ADJUST.get(goal, 0)
    protein = weight_kg * GOAL_PROTEIN.get(goal, 1.7)
    fat = weight_kg * FAT_PER_KG.get(goal, 0.9)
    carb = max(0, (kcal - protein * 4 - fat * 9) / 4)
    fiber = 25.0 if goal != "cut" else 30.0
    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "daily": {
            "kcal": round(kcal),
            "protein": round(protein, 1),
            "fat": round(fat, 1),
            "carb": round(carb, 1),
            "fiber": fiber,
        },
    }
