import re
from typing import Any, Dict, List, Optional
from database.connection import get_connection

PLAN_PRICES_BS = {
    "free": 0.0,
    "pro_50bs": 65.0,
    "campana": 120.0,
}


def normalize_whatsapp(raw_phone: Optional[str]) -> str:
    if not raw_phone:
        return ""
    return re.sub(r"\D+", "", str(raw_phone))


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    clean_email = (email or "").strip().lower()
    conn = get_connection(row_factory=True)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (clean_email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(row_factory=True)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(
    business_name: str,
    email: str,
    password: str,
    whatsapp: str = "",
    plan_type: str = "free",
) -> Dict[str, Any]:
    clean_business = (business_name or "").strip()
    clean_email = (email or "").strip().lower()
    clean_whatsapp = normalize_whatsapp(whatsapp)
    valid_plan = plan_type if plan_type in PLAN_PRICES_BS else "free"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (business_name, email, password, whatsapp, plan_type, flyers_generated)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (clean_business, clean_email, password, clean_whatsapp, valid_plan, 0),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    return {
        "id": user_id,
        "business_name": clean_business,
        "email": clean_email,
        "whatsapp": clean_whatsapp,
        "plan_type": valid_plan,
        "flyers_generated": 0,
    }


def list_merchants_with_stats() -> List[Dict[str, Any]]:
    conn = get_connection(row_factory=True)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            u.id,
            u.business_name,
            u.email,
            u.whatsapp,
            u.plan_type,
            u.flyers_generated,
            COUNT(p.id) AS products_count
        FROM users u
        LEFT JOIN products p ON p.user_id = u.id
        WHERE u.email != 'admin@catalia.bo'
        GROUP BY u.id
        ORDER BY u.id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_admin_overview_data() -> Dict[str, Any]:
    merchants = list_merchants_with_stats()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COALESCE(SUM(flyers_generated), 0) FROM users WHERE email != 'admin@catalia.bo'")
    total_flyers = cursor.fetchone()[0] or 0
    conn.close()

    estimated_revenue = sum(
        PLAN_PRICES_BS.get(m.get("plan_type") or "free", 0.0) for m in merchants
    )

    return {
        "metrics": {
            "total_merchants": len(merchants),
            "total_products": total_products,
            "total_flyers_generated": total_flyers,
            "estimated_monthly_revenue_bs": estimated_revenue,
        },
        "merchants_list": merchants,
    }


def update_user_plan(user_id: int, new_plan: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan_type = ? WHERE id = ?", (new_plan, user_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_user_and_products(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(row_factory=True)
    cursor = conn.cursor()
    cursor.execute("SELECT id, business_name, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None

    cursor.execute("DELETE FROM products WHERE user_id = ?", (user_id,))
    deleted_products = cursor.rowcount
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {
        "id": user["id"],
        "business_name": user["business_name"],
        "email": user["email"],
        "deleted_products": deleted_products,
    }


def update_user_details(
    user_id: int,
    business_name: str,
    email: str,
    whatsapp: str = "",
    plan_type: str = "free",
    flyers_generated: int = 0,
) -> Optional[Dict[str, Any]]:
    clean_business = (business_name or "").strip()
    clean_email = (email or "").strip().lower()
    clean_whatsapp = normalize_whatsapp(whatsapp)
    valid_plan = plan_type if plan_type in PLAN_PRICES_BS else "free"
    safe_flyers = max(0, int(flyers_generated or 0))

    conn = get_connection(row_factory=True)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute(
        """
        UPDATE users
        SET business_name = ?, email = ?, whatsapp = ?, plan_type = ?, flyers_generated = ?
        WHERE id = ?
        """,
        (clean_business, clean_email, clean_whatsapp, valid_plan, safe_flyers, user_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT id, business_name, email, whatsapp, plan_type, flyers_generated FROM users WHERE id = ?",
        (user_id,),
    )
    updated = dict(cursor.fetchone())
    conn.close()
    return updated