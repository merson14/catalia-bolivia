import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database.connection import init_db
from routers import admin, auth, products

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

app = FastAPI(title="CataliA Bolivia - SaaS & CRM Comercial")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(products.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def _serve_html(filename: str):
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return JSONResponse({"message": f"Vista {filename} no encontrada en {FRONTEND_DIR}"}, status_code=404)


@app.get("/")
def serve_root():
    return _serve_html("index.html")


@app.get("/{page_name}.html")
def serve_html_page(page_name: str):
    safe_name = os.path.basename(f"{page_name}.html")
    return _serve_html(safe_name)