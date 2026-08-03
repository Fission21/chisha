from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import get_current_user
from app.models import User, UserProfile, UserFavorite, UserDiary
from app.schemas import ProfileIn, ProfileOut, FavoritesIn, DiaryIn

router = APIRouter()

@router.put("/api/me/profile", response_model=ProfileOut)
def save_profile(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    profile.sex = body.sex
    profile.age = body.age
    profile.height_cm = body.height_cm
    profile.weight_kg = body.weight_kg
    profile.body_fat = body.body_fat
    profile.activity_level = body.activity_level
    profile.goal = body.goal
    profile.allergies = list(body.allergies)
    profile.preferred_cuisines = list(body.preferred_cuisines)
    db.commit()
    return body

@router.get("/api/me/favorites")
def get_favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(UserFavorite).filter(UserFavorite.user_id == user.id).all()
    return {"ids": [r.recipe_id for r in rows]}

@router.put("/api/me/favorites")
def save_favorites(body: FavoritesIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserFavorite).filter(UserFavorite.user_id == user.id).delete()
    for rid in body.ids:
        db.add(UserFavorite(user_id=user.id, recipe_id=rid))
    db.commit()
    return {"ids": body.ids}

@router.get("/api/me/diary")
def get_diary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(UserDiary).filter(UserDiary.user_id == user.id).all()
    return {r.date: r.items for r in rows}

@router.put("/api/me/diary")
def save_diary_date(body: DiaryIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(UserDiary).filter(UserDiary.user_id == user.id, UserDiary.date == body.date).first()
    if not row:
        row = UserDiary(user_id=user.id, date=body.date)
        db.add(row)
    row.items = list(body.items)
    db.commit()
    return {"date": body.date, "items": body.items}
