from typing import Any, Dict, List, Optional
from database.connection import get_connection


def list_products_by_user(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection(row_factory=True)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM products WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def create_product_record(
    user_id: int,
    name: str,
    price: float,
    currency: str,
    ai_data: Dict[str, str],
    image_data: Optional[str],
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO products (
            user_id, name, price, currency, category,
            commercial_description, urgency_phrase, estrategia_promocion,
            color_sugerido_fondo, color_sugerido_acento, image_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            price,
            currency,
            ai_data["category"],
            ai_data["commercial_description"],
            ai_data["urgency_phrase"],
            ai_data["estrategia_promocion"],
            ai_data["color_sugerido_fondo"],
            ai_data["color_sugerido_acento"],
            image_data,
        ),
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()

    return {
        "id": product_id,
        "user_id": user_id,
        "name": name,
        "price": price,
        "currency": currency,
        **ai_data,
        "image_data": image_data,
    }


def delete_product_record(product_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_flyers_count(user_id: int) -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT flyers_generated FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return (row[0] or 0) if row else None


def increment_flyers_count(user_id: int) -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET flyers_generated = COALESCE(flyers_generated, 0) + 1 WHERE id = ?",
        (user_id,),
    )
    conn.commit()
    cursor.execute("SELECT flyers_generated FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return (row[0] or 0) if row else None


def get_product_order_info(product_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(row_factory=True)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.id, p.name, p.price, p.currency, u.business_name, u.whatsapp
        FROM products p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
        """,
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None