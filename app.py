import os

from flask import Flask, jsonify, request, send_from_directory

from sbblocks import catalog, generate
from sbblocks.examples import EXAMPLES
from sbblocks.lang import RESERVED

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE, "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1 MB per request

CATALOG = dict(catalog(), reserved=sorted(RESERVED))  # built once, read-only afterwards


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/blocks")
def api_blocks():
    return jsonify(CATALOG)


@app.post("/api/generate")
def api_generate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "workspace" not in data:
        return jsonify(error="Expected JSON like {\"workspace\": {...}}"), 400
    return jsonify(generate(data["workspace"]))


@app.get("/api/examples")
def api_examples():
    return jsonify([{"id": k, "title": v["title"]} for k, v in EXAMPLES.items()])


@app.get("/api/examples/<name>")
def api_example(name):
    ex = EXAMPLES.get(name)
    if ex is None:
        return jsonify(error="No such example"), 404
    return jsonify(ex["workspace"])


@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="Workspace is too large"), 413


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), threaded=True)
