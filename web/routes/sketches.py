import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("sketches", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")


def _projects():
    resp = requests.get(f"{API}/projects/")
    return resp.json() if resp.ok else []


@bp.route("/")
def index():
    project_id = request.args.get("project_id", type=int)
    params = {"project_id": project_id} if project_id else {}
    resp = requests.get(f"{API}/sketches/", params=params)
    sketches = resp.json() if resp.ok else []
    return render_template(
        "sketches/index.html",
        sketches=sketches,
        filter_project_id=project_id,
        projects=_projects(),
    )


@bp.route("/new")
def new():
    project_id = request.args.get("project_id", type=int)
    return render_template(
        "sketches/new.html",
        projects=_projects(),
        prefill_project_id=project_id,
    )


@bp.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files or not request.files["image"].filename:
        flash("Pick an image to upload.", "error")
        return redirect(url_for("sketches.new"))
    image = request.files["image"]
    data = {}
    if request.form.get("project_id"):
        data["project_id"] = request.form.get("project_id")
    resp = requests.post(
        f"{API}/sketches/upload",
        files={"file": (image.filename, image.stream, image.content_type)},
        data=data,
    )
    if not resp.ok:
        flash("Upload failed.", "error")
        return redirect(url_for("sketches.new"))
    flash("Sketch uploaded.", "success")
    return redirect(url_for("sketches.detail", sketch_id=resp.json()["id"]))


@bp.route("/generate", methods=["POST"])
def generate():
    prompt = (request.form.get("prompt") or "").strip()
    if not prompt:
        flash("Write a prompt to generate a sketch.", "error")
        return redirect(url_for("sketches.new"))
    return _post_generate(prompt, request.form.get("project_id"))


@bp.route("/ai-generate", methods=["POST"])
def ai_generate():
    parts = []
    garment = (request.form.get("garment_type") or "").strip()
    silhouette = (request.form.get("silhouette") or "").strip()
    color = (request.form.get("color") or "").strip()
    fabric = (request.form.get("fabric") or "").strip()
    length = (request.form.get("length") or "").strip()
    sleeves = (request.form.get("sleeves") or "").strip()
    extras = (request.form.get("extras") or "").strip()

    descriptor_parts = [p for p in [silhouette, color, fabric] if p]
    descriptor = " ".join(descriptor_parts)
    if garment:
        parts.append(f"{descriptor + ' ' if descriptor else ''}{garment}".strip())
    elif descriptor:
        parts.append(descriptor)

    if length:
        parts.append(f"{length} length")
    if sleeves:
        parts.append(f"{sleeves} sleeves")
    if extras:
        parts.append(extras)

    if not parts:
        flash("Pick at least one option or add notes.", "error")
        return redirect(url_for("sketches.new"))
    prompt = ". ".join(parts) + "."
    return _post_generate(prompt, request.form.get("project_id"))


def _post_generate(prompt, project_id):
    payload = {"prompt": prompt}
    if project_id:
        payload["project_id"] = int(project_id)
    resp = requests.post(f"{API}/sketches/generate", json=payload, timeout=120)
    if not resp.ok:
        try:
            detail = resp.json().get("detail", "Generation failed.")
        except ValueError:
            detail = "Generation failed."
        flash(detail, "error")
        return redirect(url_for("sketches.new"))
    flash("Sketch generated.", "success")
    return redirect(url_for("sketches.detail", sketch_id=resp.json()["id"]))


@bp.route("/<int:sketch_id>")
def detail(sketch_id):
    resp = requests.get(f"{API}/sketches/{sketch_id}")
    if not resp.ok:
        flash("Sketch not found.", "error")
        return redirect(url_for("sketches.index"))
    return render_template(
        "sketches/detail.html",
        sketch=resp.json(),
        projects=_projects(),
    )


@bp.route("/<int:sketch_id>/link", methods=["POST"])
def link(sketch_id):
    project_id = request.form.get("project_id") or None
    payload = {"project_id": int(project_id) if project_id else None}
    requests.patch(f"{API}/sketches/{sketch_id}", json=payload)
    return redirect(url_for("sketches.detail", sketch_id=sketch_id))


@bp.route("/<int:sketch_id>/delete", methods=["POST"])
def delete(sketch_id):
    requests.delete(f"{API}/sketches/{sketch_id}")
    flash("Sketch deleted.", "success")
    return redirect(url_for("sketches.index"))
