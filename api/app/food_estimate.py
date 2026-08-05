"""把日常中文份量换成可计算的食物重量。

这是一个有意受限的估算器：只有明确克数/毫升或已收录的家庭份量才会计算，
无法可靠换算时返回原因而不是伪造精确结果。
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import FOOD_PORTIONS_FILE
from app.models import Food


MAX_ITEMS = 12
_SPLIT_RE = re.compile(r"[，,；;\n]+")
_NUMBER_RE = r"(?:\d+(?:\.\d+)?|[一二两三四五六七八九十半])"
_WEIGHT_RE = re.compile(rf"(?P<number>{_NUMBER_RE})\s*(?P<unit>公斤|千克|kg|克|g|毫升|ml)", re.I)
_COUNT_RE = re.compile(rf"(?P<number>{_NUMBER_RE})\s*(?P<unit>个|根|只|片|杯|碗|份|颗|粒|把|块|勺|串|瓶|罐|盒|袋|条|节|瓣|朵|棵|球|张|听)")
_SIZE_RE = re.compile(r"特大|中等(?:大小|长度)?|中号|大号|小号|大|中|小")
_SPACE_RE = re.compile(r"\s+")
_CHINESE_NUMBERS = {"一": 1.0, "二": 2.0, "两": 2.0, "三": 3.0, "四": 4.0, "五": 5.0,
                    "六": 6.0, "七": 7.0, "八": 8.0, "九": 9.0, "十": 10.0, "半": 0.5}


def _normalise(value: str) -> str:
    return _SPACE_RE.sub("", unicodedata.normalize("NFKC", value).strip().lower())


def _number(value: str) -> float:
    if value in _CHINESE_NUMBERS:
        return _CHINESE_NUMBERS[value]
    return float(value)


def _size(value: str) -> str:
    if value in {"大", "大号", "特大"}:
        return "large"
    if value in {"小", "小号"}:
        return "small"
    return "medium"


@lru_cache(maxsize=1)
def portion_profiles() -> dict[str, Any]:
    data = json.loads(Path(FOOD_PORTIONS_FILE).read_text(encoding="utf-8"))
    return {profile["key"]: profile for profile in data.get("profiles", [])}


@lru_cache(maxsize=1)
def portion_source_note() -> str:
    data = json.loads(Path(FOOD_PORTIONS_FILE).read_text(encoding="utf-8"))
    return str(data.get("source", {}).get("note", "份量为估算值。"))


def split_query(query: str) -> list[str]:
    items = [part.strip() for part in _SPLIT_RE.split(query) if part.strip()]
    if len(items) > MAX_ITEMS:
        raise ValueError(f"一次最多计算 {MAX_ITEMS} 项食材")
    return items


def _profile_for(text: str) -> dict[str, Any] | None:
    normalised = _normalise(text)
    for profile in portion_profiles().values():
        if any(_normalise(alias) in normalised for alias in profile.get("aliases", [])):
            return profile
    return None


def _food_term(text: str) -> str:
    value = _normalise(text)
    value = _WEIGHT_RE.sub("", value)
    value = _COUNT_RE.sub("", value)
    value = _SIZE_RE.sub("", value)
    value = re.sub(r"(?:的|约|大约|一份|一杯|一碗|一个|一根)", "", value)
    return value.strip("，,。.!！？?（）()")


def _lookup_food(db: Session, text: str, profile: dict[str, Any] | None) -> Food | None:
    if profile:
        row = db.query(Food).filter(Food.name == profile["foodName"]).first()
        if row:
            return row

    term = _food_term(text)
    if not term:
        return None
    rows = db.query(Food).filter(Food.name.like(f"%{term}%")).limit(20).all()
    if not rows:
        rows = db.query(Food).filter(Food.name.like(f"%{text.strip()}%")).limit(20).all()
    if not rows:
        return None

    def score(row: Food) -> tuple[int, int]:
        name = _normalise(row.name)
        if name == term:
            return (3, -len(name))
        if term in name:
            return (2, -len(name))
        return (1, -len(name))

    return max(rows, key=score)


def _explicit_weight(text: str, profile: dict[str, Any] | None) -> tuple[float, str] | None:
    match = _WEIGHT_RE.search(_normalise(text))
    if not match:
        return None
    amount = _number(match.group("number"))
    unit = match.group("unit").lower()
    if unit in {"公斤", "千克", "kg"}:
        return amount * 1000, f"按输入的 {amount:g} kg 计算"
    if unit in {"克", "g"}:
        return amount, f"按输入的 {amount:g} g 计算"
    factor = float((profile or {}).get("mlToGram", 1.0))
    weight = amount * factor
    if factor == 1:
        return weight, f"按输入的 {amount:g} ml（1 ml≈1 g）计算"
    return weight, f"按输入的 {amount:g} ml 和密度换算计算"


def _household_weight(text: str, profile: dict[str, Any] | None) -> tuple[float, str] | None:
    if not profile:
        return None
    match = _COUNT_RE.search(_normalise(text))
    unit = match.group("unit") if match else profile.get("defaultUnit")
    count = _number(match.group("number")) if match else 1.0
    weights = profile.get("unitWeightsG", {}).get(unit)
    # “一个香蕉”在口语中很常见；当输入的是泛用量词而该食材只定义了
    # 更准确的量词（例如“根”）时，回退到食材的默认份量。
    if not weights:
        unit = profile.get("defaultUnit")
        weights = profile.get("unitWeightsG", {}).get(unit)
    if not weights:
        return None
    size_match = _SIZE_RE.search(_normalise(text))
    size = _size(size_match.group(0)) if size_match else "medium"
    per_unit = float(weights.get(size, weights.get("default", 0)))
    if per_unit <= 0:
        return None
    size_label = {"large": "大", "medium": "中等", "small": "小"}.get(size, "")
    return count * per_unit, f"按 {count:g}{unit}{size_label}份量估算（约 {per_unit:g} g/份）"


def nutrition_for(food: Food, amount_g: float) -> dict[str, float]:
    factor = amount_g / 100.0
    return {
        "energyKCal": round(food.energy_kcal * factor, 1),
        "protein": round(food.protein * factor, 1),
        "fat": round(food.fat * factor, 1),
        "CHO": round(food.carbohydrate * factor, 1),
        "dietaryFiber": round(food.dietary_fiber * factor, 1),
        "sodium": round(food.sodium * factor, 1),
    }


def estimate_item(db: Session, text: str) -> dict[str, Any]:
    profile = _profile_for(text)
    food = _lookup_food(db, text, profile)
    if not food:
        return {"input": text, "reason": "没有找到对应食材；可尝试写明食材名称和克数，例如“200g 鸡胸肉”。"}

    portion = _explicit_weight(text, profile) or _household_weight(text, profile)
    if not portion:
        return {
            "input": text,
            "reason": f"已找到“{food.name}”，但缺少可换算的份量；请补充克数、毫升或常见单位。",
        }
    amount_g, amount_note = portion
    if amount_g <= 0 or amount_g > 10000:
        return {"input": text, "reason": "份量需大于 0 且不超过 10 kg。"}
    return {
        "input": text,
        "food": {"id": food.id, "name": food.name, "source": food.source},
        "amountG": round(amount_g, 1),
        "amountNote": amount_note,
        "nutrition": nutrition_for(food, amount_g),
    }


def estimate_query(db: Session, query: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    unmatched: list[dict[str, str]] = []
    for text in split_query(query):
        result = estimate_item(db, text)
        if "reason" in result:
            unmatched.append(result)
        else:
            items.append(result)

    total = {key: 0.0 for key in ("energyKCal", "protein", "fat", "CHO", "dietaryFiber", "sodium")}
    for item in items:
        for key, value in item["nutrition"].items():
            total[key] += value
    return {
        "items": items,
        "unmatched": unmatched,
        "total": {key: round(value, 1) for key, value in total.items()},
        "notice": f"{portion_source_note()} 结果用于饮食记录参考，包装营养标签和实际可食重量优先。",
    }
