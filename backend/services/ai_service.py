import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib import request as url_request
from urllib.error import HTTPError, URLError

HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

SPANISH_SYSTEM_DIRECTIVE = (
    "IDIOMA OBLIGATORIO: ESPAÑOL. Está estrictamente prohibido escribir cualquier "
    "palabra, título, explicación, etiqueta o nombre en inglés. "
    "Todo el contenido debe redactarse en español claro, natural y comercial, "
    "analizando realmente el producto y obedeciendo al pie de la letra cualquier "
    "instrucción, corrección o enfoque solicitado por el usuario."
)


def _load_dotenv_value(key: str) -> str:
    env_val = os.getenv(key, "").strip()
    if env_val:
        return env_val

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate_paths = [
        os.path.join(base_dir, ".env"),
        os.path.abspath(os.path.join(base_dir, "..", ".env")),
        os.path.join(os.getcwd(), ".env"),
    ]
    seen = set()
    for env_path in candidate_paths:
        if env_path in seen or not os.path.isfile(env_path):
            continue
        seen.add(env_path)
        try:
            with open(env_path, "r", encoding="utf-8-sig") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        val = v.strip().strip('"').strip("'").strip()
                        if val:
                            return val
        except Exception:
            pass
    return ""


def _get_groq_config() -> Dict[str, str]:
    raw_url = (
        _load_dotenv_value("GROQ_API_URL")
        or "https://api.groq.com/openai/v1/responses"
    ).strip().rstrip("/")
    if raw_url.endswith("/chat/completions"):
        raw_url = raw_url[: -len("/chat/completions")] + "/responses"
    elif raw_url.endswith("/openai/v1") or raw_url.endswith("/v1"):
        raw_url = f"{raw_url}/responses"

    return {
        "api_key": _load_dotenv_value("GROQ_API_KEY"),
        "api_url": raw_url,
        "text_model": (
            _load_dotenv_value("GROQ_TEXT_MODEL") or "openai/gpt-oss-20b"
        ).strip(),
        "vision_model": (
            _load_dotenv_value("GROQ_VISION_MODEL") or "openai/gpt-oss-20b"
        ).strip(),
        "fallback_model": (
            _load_dotenv_value("GROQ_FALLBACK_MODEL") or "openai/gpt-oss-120b"
        ).strip(),
    }


def _clean_json_text(raw_text: str) -> str:
    cleaned = re.sub(
        r"^```(?:json)?\s*", "", (raw_text or "").strip(), flags=re.IGNORECASE
    )
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    return match.group(0) if match else cleaned


def _normalize_hex_color(value: Any, default_hex: str) -> str:
    text = str(value or "").strip()
    if not text:
        return default_hex
    if not text.startswith("#") and re.fullmatch(r"[0-9a-fA-F]{6}", text):
        text = f"#{text}"
    return text.upper() if HEX_COLOR_RE.match(text) else default_hex


def _clean_string_list(raw_val: Any, fallback_val: List[str], max_items: int = 4) -> List[str]:
    if not isinstance(raw_val, list):
        return fallback_val[:max_items]
    items = [str(x).strip() for x in raw_val if str(x).strip()]
    return items[:max_items] if items else fallback_val[:max_items]


def _extract_responses_output_text(body: Dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str) and body["output_text"].strip():
        return body["output_text"].strip()

    output = body.get("output")
    if isinstance(output, list):
        parts: List[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("text"), str) and item["text"].strip():
                parts.append(item["text"])
            content = item.get("content")
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict):
                        txt = c.get("text") or c.get("content")
                        if isinstance(txt, str) and txt.strip():
                            parts.append(txt)
        if parts:
            return "\n".join(parts).strip()

    choices = body.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        if isinstance(message.get("content"), str) and message["content"].strip():
            return message["content"].strip()

    return ""


def _messages_to_input(messages: List[Dict[str, Any]]) -> str:
    if len(messages) == 1 and isinstance(messages[0].get("content"), str):
        return messages[0]["content"]
    blocks: List[str] = []
    for m in messages:
        role = str(m.get("role") or "user").upper()
        content = m.get("content")
        if isinstance(content, str):
            blocks.append(f"{role}: {content}")
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    blocks.append(f"{role}: {part.get('text', '')}")
    return "\n\n".join(blocks)


def _call_groq_responses(
    api_key: str,
    api_url: str,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.85,
) -> str:
    payload: Dict[str, Any] = {
        "model": model,
        "input": _messages_to_input(messages),
        "temperature": temperature,
    }
    data = json.dumps(payload).encode("utf-8")
    req = url_request.Request(
        api_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0 CataliA-Bolivia/1.0",
        },
        method="POST",
    )
    try:
        with url_request.urlopen(req, timeout=35) as resp:
            raw_body = resp.read().decode("utf-8", errors="replace").strip()
            if not raw_body:
                raise RuntimeError("Respuesta vacía de la API")
            body = json.loads(raw_body)
            text = _extract_responses_output_text(body)
            if not text:
                raise RuntimeError(f"Sin texto en respuesta: {raw_body[:300]}")
            return text
    except HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace").strip()
        except Exception:
            pass
        raise HTTPError(e.url, e.code, f"{e.reason} - {detail}", e.headers, None)


def _build_models_list(cfg: Dict[str, str], image_data: Optional[str]) -> List[str]:
    has_image = bool(
        image_data and image_data.startswith("data:image/") and "," in image_data
    )
    models_to_try: List[str] = []
    for candidate in [
        cfg["vision_model"] if has_image else "",
        cfg["text_model"],
        cfg["fallback_model"],
    ]:
        if candidate and candidate not in models_to_try:
            models_to_try.append(candidate)
    return models_to_try


def analyze_product_with_ai(
    name: str,
    price: float,
    currency: str = "Bs",
    image_data: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = _get_groq_config()

    fallback: Dict[str, Any] = {
        "source": "fallback",
        "category": "Comercio General",
        "commercial_description": (
            f"{name} a {price:.2f} {currency}, pensado para resolver una necesidad real "
            "con buena relación calidad-precio y atención directa."
        ),
        "description_options": [
            f"{name} por {price:.2f} {currency}: directo, útil y listo para entregar.",
            f"Si buscas {name}, esta opción a {price:.2f} {currency} combina practicidad y buen valor.",
        ],
        "urgency_options": [
            f"¡Hoy {name} a {price:.2f} {currency}! Escríbenos y aparta el tuyo",
            f"Unidades limitadas de {name}: no lo dejes pasar",
            f"Dale un giro a tu día con {name} a {price:.2f} {currency}",
        ],
        "urgency_phrase": (
            f"¡Hoy {name} a {price:.2f} {currency}! Escríbenos y aparta el tuyo || "
            f"Unidades limitadas de {name}: no lo dejes pasar || "
            f"Dale un giro a tu día con {name} a {price:.2f} {currency}"
        ),
        "creative_ideas": [
            "Muestra el producto en contexto real y haz una pregunta directa en WhatsApp en vez de solo mandar el precio.",
            "Prueba un enfoque de contraste: qué cambia para el cliente al tenerlo vs. seguir buscando.",
            "Lanza una dinámica corta ('¿Para quién lo llevarías hoy?') en Estados o historias.",
        ],
        "estrategia_promocion": (
            "Muestra el producto en contexto real y haz una pregunta directa en WhatsApp "
            "en vez de solo mandar el precio."
        ),
        "palette_options": [
            {"name": "Propuesta IA 1", "bg": "#1E1B4B", "accent": "#22C55E"},
            {"name": "Propuesta IA 2", "bg": "#18181B", "accent": "#F59E0B"},
            {"name": "Propuesta IA 3", "bg": "#0F172A", "accent": "#38BDF8"},
        ],
        "color_sugerido_fondo": "#1E1B4B",
        "color_sugerido_acento": "#22C55E",
        "whatsapp_pitch": (
            f"¡Hola! Qué tal, tenemos {name} a {price:.2f} {currency}. "
            "Si quieres te cuento detalles o te reservo uno hoy."
        ),
        "tags": ["Idea fresca", "Atención directa", "Disponible"],
    }

    prompt_text = f"""
{SPANISH_SYSTEM_DIRECTIVE}

Analiza en profundidad el producto "{name}" (precio: {price} {currency}):
1. Identifica qué es exactamente "{name}", qué función o emoción cumple, quién lo busca y qué lo hace atractivo.
2. Adapta cada campo de la respuesta a la naturaleza real de "{name}" y a su precio de {price} {currency}, sin usar frases genéricas ni palabras en inglés.

Responde ÚNICAMENTE con un objeto JSON válido (sin markdown ni texto extra) y 100% en ESPAÑOL:
- "category": categoría precisa y natural en español para "{name}".
- "commercial_description": análisis y descripción comercial de "{name}" en 2 a 3 oraciones en español, destacando su uso o valor real.
- "description_options": lista de 3 descripciones cortas en español con distintos ángulos comerciales para "{name}".
- "urgency_options": lista de 4 titulares o llamados llamativos en español pensados para "{name}".
- "urgency_phrase": las frases de "urgency_options" unidas con " || ".
- "creative_ideas": lista de 3 ideas concretas y bien pensadas para promocionar o vender "{name}".
- "estrategia_promocion": la idea más práctica y efectiva de "creative_ideas" en español.
- "palette_options": lista de 3 combinaciones de color con nombres en español que encajen con la identidad de "{name}", cada una como {{"name": "...", "bg": "#HEX", "accent": "#HEX"}}.
- "color_sugerido_fondo": bg de la primera paleta en formato #RRGGBB.
- "color_sugerido_acento": accent de la primera paleta en formato #RRGGBB.
- "whatsapp_pitch": mensaje natural y directo en español para ofrecer "{name}" por WhatsApp.
- "tags": lista de 3 etiquetas cortas en español que describan bien "{name}".
"""

    if not cfg["api_key"]:
        print("[AI] GROQ_API_KEY no encontrada en analyze_product_with_ai.")
        print(f"[AI] Usando fallback para producto '{name}'.")
        return fallback

    for model in _build_models_list(cfg, image_data):
        messages = [
            {
                "role": "user",
                "content": (
                    f"{SPANISH_SYSTEM_DIRECTIVE}\n"
                    "Analiza el producto indicado y responde ÚNICAMENTE con JSON válido en español.\n\n"
                    + prompt_text
                ),
            }
        ]
        try:
            raw_response = _call_groq_responses(
                cfg["api_key"],
                cfg["api_url"],
                model,
                messages,
                temperature=0.85,
            )
            parsed = json.loads(_clean_json_text(raw_response))
            if not isinstance(parsed, dict):
                continue

            desc_options = _clean_string_list(
                parsed.get("description_options"), fallback["description_options"], 3
            )
            urgency_options = _clean_string_list(
                parsed.get("urgency_options"), fallback["urgency_options"], 4
            )
            creative_ideas = _clean_string_list(
                parsed.get("creative_ideas"), fallback["creative_ideas"], 3
            )

            raw_palettes = parsed.get("palette_options")
            palette_options: List[Dict[str, str]] = []
            if isinstance(raw_palettes, list):
                for idx, item in enumerate(raw_palettes[:3]):
                    if isinstance(item, dict):
                        fb = fallback["palette_options"][idx % 3]
                        palette_options.append(
                            {
                                "name": str(item.get("name") or fb["name"]).strip(),
                                "bg": _normalize_hex_color(item.get("bg"), fb["bg"]),
                                "accent": _normalize_hex_color(
                                    item.get("accent"), fb["accent"]
                                ),
                            }
                        )
            if not palette_options:
                palette_options = fallback["palette_options"]

            bg_default = palette_options[0]["bg"]
            accent_default = palette_options[0]["accent"]
            raw_urgency = str(parsed.get("urgency_phrase") or "").strip()

            print(f"[AI] Respuesta real desde Grok ({model}) para producto '{name}'.")
            return {
                "source": "grok",
                "category": str(parsed.get("category") or fallback["category"]).strip(),
                "commercial_description": str(
                    parsed.get("commercial_description") or desc_options[0]
                ).strip(),
                "description_options": desc_options,
                "urgency_options": urgency_options,
                "urgency_phrase": raw_urgency if raw_urgency else " || ".join(urgency_options),
                "creative_ideas": creative_ideas,
                "estrategia_promocion": str(
                    parsed.get("estrategia_promocion") or creative_ideas[0]
                ).strip(),
                "palette_options": palette_options,
                "color_sugerido_fondo": _normalize_hex_color(
                    parsed.get("color_sugerido_fondo"), bg_default
                ),
                "color_sugerido_acento": _normalize_hex_color(
                    parsed.get("color_sugerido_acento"), accent_default
                ),
                "whatsapp_pitch": str(
                    parsed.get("whatsapp_pitch") or fallback["whatsapp_pitch"]
                ).strip(),
                "tags": _clean_string_list(parsed.get("tags"), fallback["tags"], 3),
            }
        except HTTPError as e:
            print(f"[AI] Error HTTP {e.code} con modelo '{model}': {e.reason}")
            continue
        except (URLError, json.JSONDecodeError, Exception) as e:
            print(f"[AI] Error con modelo '{model}': {e}")
            continue

    print(f"[AI] Usando fallback para producto '{name}'.")
    return fallback


def generate_creative_studio_ideas(
    name: str,
    price: float,
    currency: str = "Bs",
    business_name: str = "Mi Negocio",
    instruction: str = "",
    current_headline: str = "",
    image_data: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = _get_groq_config()
    clean_instr = (instruction or "").strip()
    tag_note = f" ({clean_instr[:32]})" if clean_instr else ""

    fallback: Dict[str, Any] = {
        "source": "fallback",
        "headlines": [
            f"{name} a {price:.2f} {currency}: ¡llévalo hoy y resuélvelo ya!{tag_note}",
            f"¿Te imaginas tener {name}? Hoy está a {price:.2f} {currency}",
            f"Oportunidad real en {name}: pídelo antes que se acabe",
            f"{name} con estilo y buen precio: {price:.2f} {currency}",
        ],
        "channels": {
            "whatsapp": {
                "flyer_cta": "Escríbenos y aparta el tuyo hoy",
                "badge": "WhatsApp Directo",
                "options": [
                    f"¡Hola! Qué tal, tenemos {name} a {price:.2f} {currency}. ¿Te gustaría ver más detalles o reservar uno?",
                    f"Estado / Difusión: ¡Nuevo ingreso o promo en {name} a {price:.2f} {currency}! Responde este mensaje y te asesoramos.",
                    f"Si te interesa {name} ({price:.2f} {currency}), escríbenos hoy y coordinamos entrega rápida.",
                ],
            },
            "instagram": {
                "flyer_cta": "Guarda esto y escríbenos al DM",
                "badge": "IG / Reels",
                "options": [
                    f"Visual y directo: muestra {name} en buena luz, pon '{price:.2f} {currency}' y cierra con '¿Lo llevarías en este estilo?'",
                    f"Carrusel corto: slide 1 gancho visual, slide 2 detalle real de {name}, slide 3 precio ({price:.2f} {currency}) y contacto.",
                    f"Historia interactiva: '¿Te gusta {name} a {price:.2f} {currency}? Escríbenos y te contamos más.'",
                ],
            },
            "facebook": {
                "flyer_cta": "Comenta o escríbenos para pedir",
                "badge": "Facebook",
                "options": [
                    f"Publicación clara para comunidad/grupos: explica qué resuelve {name}, su precio de {price:.2f} {currency} y cómo pedirlo fácil.",
                    f"Enfoque de confianza: {business_name} presenta {name} a {price:.2f} {currency}, ideal para quienes buscan buen trato y respuesta rápida.",
                    f"Pregunta abierta en el post: '¿Quién estaba buscando {name}? Disponible a {price:.2f} {currency}, consultas por mensaje.'",
                ],
            },
            "otras_relaciones": {
                "flyer_cta": "Pide el tuyo o compártelo",
                "badge": "TikTok / Clientes",
                "options": [
                    f"TikTok / Video corto (5-8 seg): toma rápida de {name} + giro o dato útil + precio {price:.2f} {currency}.",
                    f"Clientes frecuentes / VIP: 'Hola! Pensamos en ti porque tenemos {name} a {price:.2f} {currency}. ¿Te apartamos uno?'",
                    f"Objeción de precio/duda: destaca lo que incluye {name} y ofrece atención rápida o combinación útil en vez de rebajar sin sentido.",
                ],
            },
        },
        "palettes": [
            {"name": "Vibrante IA", "bg": "#1E1B4B", "accent": "#22C55E"},
            {"name": "Contraste Pro", "bg": "#18181B", "accent": "#F59E0B"},
            {"name": "Fresco Moderno", "bg": "#0F172A", "accent": "#38BDF8"},
        ],
    }

    user_order_block = (
        f"INSTRUCCIÓN DEL USUARIO (CUMPLIR ESTRICTAMENTE): {clean_instr}\n"
        "Aplica esta instrucción de forma directa en los titulares, mensajes por canal, "
        "llamados a la acción y paletas."
        if clean_instr
        else "No hay instrucción adicional; crea propuestas variadas, coherentes con el producto y pensadas para vender en español."
    )

    prompt_text = f"""
{SPANISH_SYSTEM_DIRECTIVE}

Analiza el producto "{name}" del negocio "{business_name}" (precio: {price} {currency}, titular actual: "{current_headline or "No definido"}") y genera respuestas que correspondan tanto a las características reales del producto como a lo que se indica en la instrucción.

{user_order_block}

Responde ÚNICAMENTE con un objeto JSON válido (sin markdown ni texto extra) y 100% en ESPAÑOL con esta estructura exacta:
{{
  "headlines": [
    "4 titulares cortos en español coherentes con {name} y con lo pedido por el usuario"
  ],
  "channels": {{
    "whatsapp": {{
      "flyer_cta": "llamado a la acción corto en español",
      "badge": "etiqueta corta en español de 1-2 palabras",
      "options": ["3 opciones en español para WhatsApp adaptadas a {name} y a lo solicitado"]
    }},
    "instagram": {{
      "flyer_cta": "llamado a la acción corto en español",
      "badge": "etiqueta corta en español de 1-2 palabras",
      "options": ["3 ideas en español para Instagram/Reels/Historias adaptadas a {name} y a lo solicitado"]
    }},
    "facebook": {{
      "flyer_cta": "llamado a la acción corto en español",
      "badge": "etiqueta corta en español de 1-2 palabras",
      "options": ["3 ideas en español para Facebook adaptadas a {name} y a lo solicitado"]
    }},
    "otras_relaciones": {{
      "flyer_cta": "llamado a la acción corto en español",
      "badge": "etiqueta corta en español de 1-2 palabras",
      "options": ["3 ideas en español para video corto/clientes/dudas adaptadas a {name} y a lo solicitado"]
    }}
  }},
  "palettes": [
    {{"name": "Nombre en español 1", "bg": "#HEX_OSCURO", "accent": "#HEX_VIBRANTE"}},
    {{"name": "Nombre en español 2", "bg": "#HEX_OSCURO", "accent": "#HEX_VIBRANTE"}},
    {{"name": "Nombre en español 3", "bg": "#HEX_OSCURO", "accent": "#HEX_VIBRANTE"}}
  ]
}}
"""

    if not cfg["api_key"]:
        print("[AI] GROQ_API_KEY no encontrada en generate_creative_studio_ideas.")
        print(f"[AI] Usando fallback para estudio creativo '{name}'.")
        return fallback

    for model in _build_models_list(cfg, image_data):
        messages = [
            {
                "role": "user",
                "content": (
                    f"{SPANISH_SYSTEM_DIRECTIVE}\n"
                    "Analiza el producto, sigue la instrucción indicada y responde ÚNICAMENTE con JSON válido en español.\n\n"
                    + prompt_text
                ),
            }
        ]
        try:
            raw_response = _call_groq_responses(
                cfg["api_key"],
                cfg["api_url"],
                model,
                messages,
                temperature=0.85 if clean_instr else 0.9,
            )
            parsed = json.loads(_clean_json_text(raw_response))
            if not isinstance(parsed, dict):
                continue

            headlines = _clean_string_list(
                parsed.get("headlines"), fallback["headlines"], 4
            )
            raw_ch = parsed.get("channels") if isinstance(parsed.get("channels"), dict) else {}

            channels_out: Dict[str, Any] = {}
            for key in ["whatsapp", "instagram", "facebook", "otras_relaciones"]:
                fb_ch = fallback["channels"][key]
                src_ch = raw_ch.get(key) if isinstance(raw_ch.get(key), dict) else {}
                channels_out[key] = {
                    "flyer_cta": str(src_ch.get("flyer_cta") or fb_ch["flyer_cta"]).strip(),
                    "badge": str(src_ch.get("badge") or fb_ch["badge"]).strip(),
                    "options": _clean_string_list(src_ch.get("options"), fb_ch["options"], 3),
                }

            raw_pals = parsed.get("palettes")
            palettes_out: List[Dict[str, str]] = []
            if isinstance(raw_pals, list):
                for idx, item in enumerate(raw_pals[:3]):
                    if isinstance(item, dict):
                        fb_p = fallback["palettes"][idx % 3]
                        palettes_out.append(
                            {
                                "name": str(item.get("name") or fb_p["name"]).strip(),
                                "bg": _normalize_hex_color(item.get("bg"), fb_p["bg"]),
                                "accent": _normalize_hex_color(
                                    item.get("accent"), fb_p["accent"]
                                ),
                            }
                        )
            if not palettes_out:
                palettes_out = fallback["palettes"]

            print(f"[AI] Respuesta real desde Grok ({model}) para estudio creativo '{name}'.")
            return {
                "source": "grok",
                "headlines": headlines,
                "channels": channels_out,
                "palettes": palettes_out,
            }
        except HTTPError as e:
            print(f"[AI] Error HTTP {e.code} con modelo '{model}': {e.reason}")
            continue
        except (URLError, json.JSONDecodeError, Exception) as e:
            print(f"[AI] Error con modelo '{model}': {e}")
            continue

    print(f"[AI] Usando fallback para estudio creativo '{name}'.")
    return fallback


# Alias retrocompatible para routers existentes
analyze_product_with_gemini = analyze_product_with_ai