from fastapi import APIRouter, HTTPException  # type: ignore[import-not-found]
from repositories.user_repo import (
    PLAN_PRICES_BS,
    delete_user_and_products,
    get_admin_overview_data,
    list_merchants_with_stats,
    update_user_details,
    update_user_plan,
)
from schemas.models import UserAdminUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/overview")
def admin_overview():
    return get_admin_overview_data()


@router.get("/users")
def admin_users():
    return list_merchants_with_stats()


@router.put("/users/{user_id}")
def edit_user(user_id: int, payload: UserAdminUpdate):
    clean_business = (payload.business_name or "").strip()
    clean_email = (payload.email or "").strip().lower()

    if not clean_business or not clean_email:
        raise HTTPException(
            status_code=400,
            detail="El nombre del comercio y el correo son obligatorios.",
        )

    if payload.plan_type not in PLAN_PRICES_BS:
        raise HTTPException(status_code=400, detail="Plan no válido.")

    updated = update_user_details(
        user_id=user_id,
        business_name=clean_business,
        email=clean_email,
        whatsapp=payload.whatsapp,
        plan_type=payload.plan_type,
        flyers_generated=payload.flyers_generated,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    return {
        "message": f"Comercio '{updated['business_name']}' actualizado.",
        "user": updated,
    }


@router.put("/users/{user_id}/plan")
def change_user_plan(user_id: int, new_plan: str):
    if new_plan not in PLAN_PRICES_BS:
        raise HTTPException(status_code=400, detail="Plan no válido.")

    updated = update_user_plan(user_id, new_plan)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    return {"message": f"Plan actualizado a '{new_plan}' para el usuario #{user_id}."}


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    result = delete_user_and_products(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    return {
        "message": (
            f"Usuario '{result['business_name']}' eliminado junto con "
            f"{result['deleted_products']} producto(s)."
        )
    }