import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("inspiration", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")

ENTRY_TYPES = (
    "dream",
    "thought",
    "memory",
    "mood",
    "image",
    "fabric",
    "silhouette",
    "note",
)


def _ai_configured():
    try:
        resp = requests.get(f"{API}/inspiration/ai-status", timeout=5)
        return bool(resp.ok and resp.json().get("configured"))
    except requests.RequestException:
        return False


def _split_tags(raw):
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


@bp.route("/")
def index():
    resp = requests.get(f"{API}/inspiration/")
    entries = resp.json() if resp.ok else []
    return render_template(
        "inspiration/index.html",
        entries=entries,
        ai_configured=_ai_configured(),
    )


@bp.route("/new")
def new():
    return render_template(
        "inspiration/new.html",
        entry_types=ENTRY_TYPES,
    )


@bp.route("/", methods=["POST"])
def create():
    body = (request.form.get("body") or "").strip() or None
    image = request.files.get("image")
    has_image = image is not None and image.filename
    if not body and not has_image:
        flash("Add some text, an image, or both.", "error")
        return redirect(url_for("inspiration.new"))

    payload = {
        "title": (request.form.get("title") or "").strip() or None,
        "entry_type": request.form.get("entry_type") or "note",
        "body": body,
        "tags": _split_tags(request.form.get("tags")),
    }
    resp = requests.post(f"{API}/inspiration/", json=payload)
    if not resp.ok:
        flash("Could not save entry.", "error")
        return redirect(url_for("inspiration.new"))
    entry = resp.json()
    if has_image:
        requests.post(
            f"{API}/inspiration/{entry['id']}/image",
            files={"file": (image.filename, image.stream, image.content_type)},
        )
    flash("Saved.", "success")
    return redirect(url_for("inspiration.index"))


@bp.route("/<int:entry_id>/edit")
def edit(entry_id):
    resp = requests.get(f"{API}/inspiration/{entry_id}")
    if not resp.ok:
        flash("Entry not found.", "error")
        return redirect(url_for("inspiration.index"))
    return render_template(
        "inspiration/edit.html",
        entry=resp.json(),
        entry_types=ENTRY_TYPES,
    )


@bp.route("/<int:entry_id>/edit", methods=["POST"])
def update(entry_id):
    body = (request.form.get("body") or "").strip() or None
    image = request.files.get("image")
    has_new_image = image is not None and image.filename

    payload = {
        "title": (request.form.get("title") or "").strip() or None,
        "entry_type": request.form.get("entry_type") or "note",
        "body": body,
        "tags": _split_tags(request.form.get("tags")),
    }
    resp = requests.put(f"{API}/inspiration/{entry_id}", json=payload)
    if not resp.ok:
        try:
            detail = resp.json().get("detail", "Could not save.")
        except ValueError:
            detail = "Could not save."
        flash(detail, "error")
        return redirect(url_for("inspiration.edit", entry_id=entry_id))
    if has_new_image:
        requests.post(
            f"{API}/inspiration/{entry_id}/image",
            files={"file": (image.filename, image.stream, image.content_type)},
        )
    flash("Updated.", "success")
    return redirect(url_for("inspiration.index"))


@bp.route("/<int:entry_id>/delete", methods=["POST"])
def delete(entry_id):
    requests.delete(f"{API}/inspiration/{entry_id}")
    flash("Entry deleted.", "success")
    return redirect(url_for("inspiration.index"))


@bp.route("/generate", methods=["POST"])
def generate():
    entry_ids = request.form.getlist("entry_ids", type=int)
    if not entry_ids:
        flash("Select at least one inspiration entry.", "error")
        return redirect(url_for("inspiration.index"))
    resp = requests.post(
        f"{API}/inspiration/generate-project-suggestion",
        json={"entry_ids": entry_ids},
        timeout=120,
    )
    if not resp.ok:
        try:
            detail = resp.json().get("detail", "Could not generate suggestion.")
        except ValueError:
            detail = "Could not generate suggestion."
        flash(detail, "error")
        return redirect(url_for("inspiration.index"))
    sugg = resp.json()
    return redirect(url_for("inspiration.suggestion", suggestion_id=sugg["id"]))


@bp.route("/suggestions/<int:suggestion_id>")
def suggestion(suggestion_id):
    resp = requests.get(f"{API}/inspiration-suggestions/{suggestion_id}")
    if not resp.ok:
        flash("Suggestion not found.", "error")
        return redirect(url_for("inspiration.index"))
    sugg = resp.json()
    # Re-fetch the source entries for context.
    sources = []
    for eid in sugg.get("source_entry_ids") or []:
        e = requests.get(f"{API}/inspiration/{eid}")
        if e.ok:
            sources.append(e.json())
    return render_template(
        "inspiration/suggestion.html",
        suggestion=sugg,
        sources=sources,
    )


@bp.route("/suggestions/<int:suggestion_id>/create-project", methods=["POST"])
def create_project_from_suggestion(suggestion_id):
    resp = requests.post(
        f"{API}/inspiration-suggestions/{suggestion_id}/create-project",
        timeout=30,
    )
    if not resp.ok:
        flash("Could not create project.", "error")
        return redirect(url_for("inspiration.suggestion", suggestion_id=suggestion_id))
    project_id = resp.json().get("project_id")
    flash("Project created.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/suggestions/<int:suggestion_id>/generate-sketch", methods=["POST"])
def generate_sketch_from_suggestion(suggestion_id):
    project_id = request.form.get("project_id")
    data = {"project_id": project_id} if project_id else {}
    resp = requests.post(
        f"{API}/inspiration-suggestions/{suggestion_id}/generate-sketch",
        data=data,
        timeout=120,
    )
    if not resp.ok:
        try:
            detail = resp.json().get("detail", "Could not generate sketch.")
        except ValueError:
            detail = "Could not generate sketch."
        flash(detail, "error")
        return redirect(url_for("inspiration.suggestion", suggestion_id=suggestion_id))
    sketch_id = resp.json().get("sketch_id")
    flash("Sketch generated.", "success")
    return redirect(url_for("sketches.detail", sketch_id=sketch_id))
