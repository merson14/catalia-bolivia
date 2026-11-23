import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "catalia_local.db")

demo_users = [
    ("Importadora Illimani", "illimani@demo.bo", "demo123", "pro_50bs", 6),
    ("Moda & Estilo La Paz", "estilo.lpz@demo.bo", "demo123", "free", 2),
    ("TecnoSur Cochabamba", "tecnosur@demo.bo", "demo123", "campana", 11),
    ("Hogar y Bazar Santa Cruz", "bazar.scz@demo.bo", "demo123", "pro_50bs", 4),
    ("Mundo Juguetes El Alto", "juguetes.ea@demo.bo", "demo123", "free", 1),
    ("Ferretería El Prado", "elprado@demo.bo", "demo123", "campana", 8),
]

sample_products = [
    (
        "illimani@demo.bo",
        "Carrito Plegable de Carga Reforzado",
        185.0,
        "Bs",
        "Logística y Comercio",
        "Estructura metálica resistente ideal para traslado de mercadería, cajas y compras pesadas en ciudad.",
        "¡Stock limitado esta semana! || Envío rápido en La Paz",
        "Resaltar capacidad de carga y ahorro de esfuerzo físico en entregas diarias.",
        "#09090b",
        "#10b981",
        None,
    ),
    (
        "illimani@demo.bo",
        "Lámpara Solar Portátil Recargable",
        75.0,
        "Bs",
        "Hogar e Iluminación",
        "Iluminación LED de alta duración con carga solar y USB, práctica para viajes, camping o emergencias.",
        "¡Últimas unidades en oferta! || Llévate la tuya hoy",
        "Destacar autonomía energética y utilidad en cortes de luz o salidas al campo.",
        "#09090b",
        "#a855f7",
        None,
    ),
    (
        "tecnosur@demo.bo",
        "Audífonos Inalámbricos ANC Pro",
        140.0,
        "Bs",
        "Tecnología y Audio",
        "Sonido nítido, estuche de carga rápida y conexión estable para llamadas, estudio y uso diario.",
        "¡Precio promocional de campaña! || Pídelos por WhatsApp",
        "Enfatizar batería de larga duración y comodidad para estudiantes y teletrabajo.",
        "#09090b",
        "#06b6d4",
        None,
    ),
]


def seed():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT,
                email TEXT UNIQUE,
                password TEXT,
                plan_type TEXT DEFAULT 'free',
                flyers_generated INTEGER DEFAULT 0,
                whatsapp TEXT DEFAULT ''
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                price REAL,
                currency TEXT DEFAULT 'Bs',
                category TEXT,
                commercial_description TEXT,
                urgency_phrase TEXT,
                estrategia_promocion TEXT,
                color_sugerido_fondo TEXT,
                color_sugerido_acento TEXT,
                image_data TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        inserted_users = {}

        for biz_name, email, pwd, plan, flyers in demo_users:
            cursor.execute(
                """
                INSERT INTO users (business_name, email, password, plan_type, flyers_generated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    business_name = excluded.business_name,
                    password = excluded.password,
                    plan_type = excluded.plan_type,
                    flyers_generated = excluded.flyers_generated
                """,
                (biz_name, email, pwd, plan, flyers),
            )
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                inserted_users[email] = row[0]

        for email, name, price, currency, cat, desc, urgency, strategy, bg, accent, img in sample_products:
            uid = inserted_users.get(email)
            if uid is not None:
                cursor.execute(
                    "SELECT id FROM products WHERE user_id = ? AND name = ?",
                    (uid, name),
                )
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute(
                        """
                        INSERT INTO products (
                            user_id, name, price, currency, category,
                            commercial_description, urgency_phrase, estrategia_promocion,
                            color_sugerido_fondo, color_sugerido_acento, image_data
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (uid, name, price, currency, cat, desc, urgency, strategy, bg, accent, img),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE products SET
                            price = ?,
                            currency = ?,
                            category = ?,
                            commercial_description = ?,
                            urgency_phrase = ?,
                            estrategia_promocion = ?,
                            color_sugerido_fondo = ?,
                            color_sugerido_acento = ?,
                            image_data = ?
                        WHERE id = ?
                        """,
                        (price, currency, cat, desc, urgency, strategy, bg, accent, img, existing[0]),
                    )

    print(f"Listo: datos insertados en {DB_PATH}")


if __name__ == "__main__":
    seed()