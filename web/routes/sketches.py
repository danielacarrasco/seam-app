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
    def field(name):
        val = (request.form.get(name) or "").strip()
        if val.lower() == "other":
            return (request.form.get(name + "_other") or "").strip()
        return val

    garment = field("garment_type")
    silhouette = field("silhouette")
    length = field("length")
    neckline = field("neckline")
    armholes = field("sleeves")
    waist = field("waist_shaping")
    back = field("back_design")
    fabric = field("fabric")
    color = field("color")
    extras = (request.form.get("extras") or "").strip()

    if not garment:
        flash("Pick a garment type (or use Other to describe one).", "error")
        return redirect(url_for("sketches.new"))

    fabric_line = f"{color} {fabric}".strip() if color or fabric else ""

    lines = [
        f"Create a clean editorial fashion sketch of a {garment} designed for a female body.",
        "The garment should have:",
    ]
    if silhouette:
        lines.append(f"Silhouette: {silhouette}")
    if length:
        lines.append(f"Length: {length}")
    if neckline:
        lines.append(f"Neckline: {neckline}")
    if armholes:
        lines.append(f"Armholes/sleeves: {armholes}")
    if waist:
        lines.append(f"Waist shaping: {waist}")
    if back:
        lines.append(f"Back design: {back}")
    if fabric_line:
        lines.append(f"Fabric: {fabric_line}")
    if extras:
        lines.append(extras)

    lines.extend([
        "Show how the fabric behaves (drape, stiffness, folds, transparency).",
        "Style: minimal, modern, slightly architectural, similar to high-end "
        "ready-to-wear (e.g. Akris / Scanlan Theodore aesthetic).",
        "Output: front and back views; clean fashion illustration (no face "
        "detail, focus on garment); light shading to indicate structure and "
        "fabric movement; neutral background.",
    ])

    prompt = "\n".join(lines)
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
