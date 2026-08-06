from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import hash_password, verify_password, new_token, get_current_user
from app.models import User, UserProfile
from app.schemas import RegisterIn, LoginIn, TokenOut, ProfileOut

router = APIRouter()

def _issue(user: User, db: Session) -> TokenOut:
    user.token = new_token()
    db.commit()
    return TokenOut(token=user.token, email=user.email)

@router.post("/api/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="该邮箱已注册")
    salt, digest = hash_password(body.password)
    user = User(email=email, password_hash=digest, salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue(user, db)

@router.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.salt, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码不正确")
    return _issue(user, db)

@router.post("/api/auth/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.token = None
    db.commit()
    return {"ok": True}

@router.get("/api/auth/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    p = None
    if profile:
        p = ProfileOut(
            sex=profile.sex, age=profile.age, height_cm=profile.height_cm,
            weight_kg=profile.weight_kg, body_fat=profile.body_fat,
            activity_level=profile.activity_level, goal=profile.goal,
            allergies=list(profile.allergies or []),
            preferred_cuisines=list(profile.preferred_cuisines or []),
            health_profile=profile.health_profile or "balanced",
        ).model_dump()
    return {"email": user.email, "profile": p}
