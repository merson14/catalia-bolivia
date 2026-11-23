from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from repositories.product_repo import (
    create_product_record,
    delete_product_record,
    get_flyers_count,
    get_product_order_info,
    increment_flyers_count,
    list_products_by_user,
)
from repositories.user_repo import get_user_by_id, normalize_whatsapp
from schemas.models import ProductCreate
from services.ai_service import (
    analyze_product_with_gemini,
    generate_creative_studio_ideas,
)

router = APIRouter(prefix="/api", tags=["Products & Flyers"])


class CreativeStudioRequest(BaseModel):
    name: str
    price: float = 0.0
    currency: str = "Bs"
    business_name: str = "Mi Negocio"
    instruction: str = ""
    current_headline: str = ""
    image_data: Optional[str] = None


@router.get("/products/{user_id}")
def get_user_products(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Comerciante no encontrado.")
    return list_products_by_user(user_id)


@router.post("/products/{user_id}")
def create_product(user_id: int, payload: ProductCreate):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Comerciante no encontrado.")

    clean_name = (payload.name or "").strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="El nombre del producto es obligatorio.")

    if payload.price is None or payload.price < 0:
        raise HTTPException(status_code=400, detail="El precio no puede ser negativo.")

    clean_currency = (payload.currency or "Bs").strip() or "Bs"

    ai_data = analyze_product_with_gemini(
        name=clean_name,
        price=payload.price,
        currency=clean_currency,
        image_data=payload.image_data,
    )

    return create_product_record(
        user_id=user_id,
        name=clean_name,
        price=payload.price,
        currency=clean_currency,
        ai_data=ai_data,
        image_data=payload.image_data,
    )


@router.delete("/products/{product_id}")
def delete_product(product_id: int):
    deleted = delete_product_record(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return {"message": "Producto eliminado correctamente."}


@router.get("/flyers/count/{user_id}")
def get_user_flyers_count(user_id: int):
    count = get_flyers_count(user_id)
    if count is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return {"user_id": user_id, "flyers_generated": count}


@router.post("/flyers/register/{user_id}")
def register_user_flyer(user_id: int):
    count = increment_flyers_count(user_id)
    if count is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return {"user_id": user_id, "flyers_generated": count}


@router.post("/orders/track/{product_id}")
def track_order(product_id: int):
    info = get_product_order_info(product_id)
    if not info:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    phone = normalize_whatsapp(info.get("whatsapp"))
    business = info.get("business_name") or "el comercio"
    product_name = info.get("name") or "este producto"
    raw_price = info.get("price") or 0
    price_str = f"{float(raw_price):g}"
    currency = info.get("currency") or "Bs"

    text = quote(
        f"Hola {business}, me interesa pedir: {product_name} ({price_str} {currency})."
    )
    wa_url = f"https://wa.me/{phone}?text={text}" if phone else f"https://wa.me/?text={text}"

    return {
        "product_id": product_id,
        "whatsapp_url": wa_url,
        "whatsapp": phone,
    }


@router.post("/ai/creative-studio")
def creative_studio_ideas(payload: CreativeStudioRequest):
    clean_name = (payload.name or "").strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="El nombre del producto es obligatorio.")

    clean_price = payload.price if payload.price is not None and payload.price >= 0 else 0.0

    return generate_creative_studio_ideas(
        name=clean_name,
        price=clean_price,
        currency=(payload.currency or "Bs").strip() or "Bs",
        business_name=(payload.business_name or "Mi Negocio").strip(),
        instruction=(payload.instruction or "").strip(),
        current_headline=(payload.current_headline or "").strip(),
        image_data=payload.image_data,
    )