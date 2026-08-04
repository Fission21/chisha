from app.nutrition import bmr_mifflin, daily_targets

def test_bmr_mifflin_male():
    # 男 175cm / 70kg / 28岁: 10*70 + 6.25*175 - 5*28 + 5
    assert bmr_mifflin("male", 70, 175, 28) == 10 * 70 + 6.25 * 175 - 5 * 28 + 5

def test_bmr_mifflin_female():
    # 女 165cm / 55kg / 25岁: 10*55 + 6.25*165 - 5*25 - 161
    assert bmr_mifflin("female", 55, 165, 25) == 10 * 55 + 6.25 * 165 - 5 * 25 - 161

def test_bmr_gender_difference():
    # 同一身体数据下，女性 BMR 比男性低 166 kcal（-161 vs +5）
    male = bmr_mifflin("male", 70, 175, 28)
    female = bmr_mifflin("female", 70, 175, 28)
    assert male - female == 166
    targets_male = daily_targets("male", 70, 175, 28, "moderate", "cut")
    targets_female = daily_targets("female", 70, 175, 28, "moderate", "cut")
    assert targets_female["daily"]["kcal"] < targets_male["daily"]["kcal"]

def test_daily_targets_sanity():
    t = daily_targets("male", 70, 175, 28, "moderate", "cut")
    bmr = bmr_mifflin("male", 70, 175, 28)
    assert t["tdee"] == round(bmr * 1.55, 1)
    # 减脂：TDEE - 350
    assert t["daily"]["kcal"] == round(t["tdee"] - 350)
    # 宏量守恒：蛋白质*4 + 脂肪*9 + 碳水*4 ≈ 热量
    d = t["daily"]
    approx = d["protein"] * 4 + d["fat"] * 9 + d["carb"] * 4
    assert abs(approx - d["kcal"]) < 40, f"宏量不守恒: {approx} vs {d['kcal']}"

def test_daily_targets_bulk_positive_surplus():
    t = daily_targets("male", 75, 178, 30, "active", "bulk")
    assert t["daily"]["kcal"] > t["tdee"]
