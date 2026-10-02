"""Serve the compiled Vue application and explicit local asset directories."""

from pathlib import Path

from flask import Blueprint, abort, current_app, send_from_directory

main_bp = Blueprint("main", __name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_ASSETS = {
    "background.png", "fondoDePagina.png", "kia carens .png", "logo dorado.jpg",
    "logo plomo.png", "logo de WhatsApp .png", "logo.png", "logo1.png",
}


@main_bp.get("/api/health")
def health():
    return {"status": "ok"}


@main_bp.get("/img/<path:filename>")
def image(filename):
    if filename not in ALLOWED_ASSETS:
        abort(404)
    return send_from_directory(PROJECT_ROOT / "img", filename, max_age=86400)


@main_bp.get("/assets/<path:filename>")
def asset(filename):
    # Vite emits hashed JS/CSS filenames; send_from_directory prevents traversal.
    return send_from_directory(Path(current_app.config["DIST_DIR"]) / "assets", filename, max_age=31536000)


@main_bp.get("/favicon.svg")
def favicon():
    return send_from_directory(current_app.config["DIST_DIR"], "favicon.svg", max_age=86400)


@main_bp.get("/")
@main_bp.get("/<path:page>")
def spa(page=""):
    if page == "api" or page.startswith("api/") or "." in page:
        abort(404)
    dist = Path(current_app.config["DIST_DIR"])
    if not (dist / "index.html").is_file():
        return {"error": "Falta compilar el frontend. Ejecuta npm install y npm run build antes de iniciar JAGE."}, 503
    return send_from_directory(dist, "index.html", max_age=0)
