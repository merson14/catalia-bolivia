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

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

inserted_users = {}

for biz_name, email, pwd, plan, flyers in demo_users:
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            """
            INSERT INTO users (business_name, email, password, plan_type, flyers_generated)
            VALUES (?, ?, ?, ?, ?)
            """,
            (biz_name, email, pwd, plan, flyers),
        )
        inserted_users[email] = cursor.lastrowid
    else:
        inserted_users[email] = row[0]

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

for email, name, price, currency, cat, desc, urgency, strategy, bg, accent, img in sample_products:
    uid = inserted_users.get(email)
    if uid:
        cursor.execute(
            "SELECT id FROM products WHERE user_id = ? AND name = ?",
            (uid, name),
        )
        if not cursor.fetchone():
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

conn.commit()
conn.close()
print(f"Listo: datos insertados en {DB_PATH}")