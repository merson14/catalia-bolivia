from fastapi import APIRouter, HTTPException
from repositories.user_repo import create_user, get_user_by_email, normalize_whatsapp
from schemas.models import UserLogin, UserRegister

router = APIRouter(prefix="/api", tags=["Auth"])


def _authenticate_user(payload: UserLogin):
    user = get_user_by_email(payload.email.strip())
    if not user or user.get("password") != payload.password:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

    return {
        "id": user["id"],
        "business_name": user["business_name"],
        "email": user["email"],
        "whatsapp": normalize_whatsapp(user.get("whatsapp")),
        "plan_type": user.get("plan_type") or "free",
        "flyers_generated": user.get("flyers_generated") or 0,
    }


@router.post("/register")
def register_user(payload: UserRegister):
    email = payload.email.strip().lower()
    business_name = payload.business_name.strip()

    if not business_name or not email or not payload.password:
        raise HTTPException(status_code=400, detail="Completa todos los campos obligatorios.")

    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta registrada con ese correo.")

    return create_user(
        business_name=business_name,
        email=email,
        password=payload.password,
        whatsapp=payload.whatsapp,
        plan_type=payload.plan_type,
    )


@router.post("/login")
def login(payload: UserLogin):
    return _authenticate_user(payload)


@router.post("/auth/login")
def auth_login(payload: UserLogin):
    return _authenticate_user(payload)