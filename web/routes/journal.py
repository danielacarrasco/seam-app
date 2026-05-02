import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("journal", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")

ENTRY_TYPES = ("dream", "thought", "memory", "inspiration", "mood")


def _ai_configured():
    try:
        resp = requests.get(f"{API}/journal/ai-status", timeout=5)
        return bool(resp.ok and resp.json().get("configured"))
    except requests.RequestException:
        return False


def _split_tags(raw):
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


@bp.route("/")
def index():
    resp = requests.get(f"{API}/journal/")
    entries = resp.json() if resp.ok else []
    return render_template("journal/index.html", entries=entries)


@bp.route("/new")
def new():
    return render_template(
        "journal/new.html",
        entry_types=ENTRY_TYPES,
        ai_configured=_ai_configured(),
    )


@bp.route("/", methods=["POST"])
def create():
    body = (request.form.get("body") or "").strip()
    if not body:
        flash("Write something in the entry first.", "error")
        return redirect(url_for("journal.new"))
    payload = {
        "title": (request.form.get("title") or "").strip() or None,
        "entry_type": request.form.get("entry_type") or "thought",
        "body": body,
        "tags": _split_tags(request.form.get("tags")),
    }
    resp = requests.post(f"{API}/journal/", json=payload)
    if not resp.ok:
        flash("Could not save entry.", "error")
        return redirect(url_for("journal.new"))
    entry = resp.json()
    image = request.files.get("image")
    if image and image.filename:
        requests.post(
            f"{API}/journal/{entry['id']}/image",
            files={"file": (image.filename, image.stream, image.content_type)},
        )
    flash("Entry saved.", "success")
    return redirect(url_for("journal.detail", entry_id=entry["id"]))


@bp.route("/<int:entry_id>")
def detail(entry_id):
    resp = requests.get(f"{API}/journal/{entry_id}")
    if not resp.ok:
        flash("Entry not found.", "error")
        return redirect(url_for("journal.index"))
    return render_template(
        "journal/detail.html",
        entry=resp.json(),
        ai_configured=_ai_configured(),
    )


@bp.route("/<int:entry_id>/edit")
def edit(entry_id):
    resp = requests.get(f"{API}/journal/{entry_id}")
    if not resp.ok:
        flash("Entry not found.", "error")
        return redirect(url_for("journal.index"))
    return render_template(
        "journal/edit.html",
        entry=resp.json(),
        entry_types=ENTRY_TYPES,
    )


@bp.route("/<int:entry_id>/edit", methods=["POST"])
def update(entry_id):
    payload = {
        "title": (request.form.get("title") or "").strip() or None,
        "entry_type": request.form.get("entry_type") or "thought",
        "body": (request.form.get("body") or "").strip(),
        "tags": _split_tags(request.form.get("tags")),
    }
    resp = requests.put(f"{API}/journal/{entry_id}", json=payload)
    if not resp.ok:
        flash("Could not save changes.", "error")
        return redirect(url_for("journal.edit", entry_id=entry_id))
    flash("Entry updated.", "success")
    return redirect(url_for("journal.detail", entry_id=entry_id))


@bp.route("/<int:entry_id>/delete", methods=["POST"])
def delete(entry_id):
    requests.delete(f"{API}/journal/{entry_id}")
    flash("Entry deleted.", "success")
    return redirect(url_for("journal.index"))


@bp.route("/<int:entry_id>/generate-suggestions", methods=["POST"])
def generate_suggestions(entry_id):
    resp = requests.post(
        f"{API}/journal/{entry_id}/generate-suggestions", timeout=120
    )
    if not resp.ok:
        try:
            detail = resp.json().get("detail", "Could not generate suggestions.")
        except ValueError:
            detail = "Could not generate suggestions."
        flash(detail, "error")
    else:
        flash("New suggestions ready.", "success")
    return redirect(url_for("journal.detail", entry_id=entry_id))


@bp.route("/suggestions/<int:suggestion_id>/create-project", methods=["POST"])
def create_project_from_suggestion(suggestion_id):
    save_only = request.form.get("save_only") == "1"
    entry_id = request.form.get("entry_id", type=int)
    resp = requests.post(
        f"{API}/journal-suggestions/{suggestion_id}/create-project",
        timeout=30,
    )
    if not resp.ok:
        flash("Could not create project.", "error")
        if entry_id:
            return redirect(url_for("journal.detail", entry_id=entry_id))
        return redirect(url_for("journal.index"))
    project_id = resp.json().get("project_id")
    if save_only:
        flash("Saved as idea in Projects.", "success")
        if entry_id:
            return redirect(url_for("journal.detail", entry_id=entry_id))
        return redirect(url_for("journal.index"))
    flash("Project created.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/suggestions/<int:suggestion_id>/generate-sketch", methods=["POST"])
def generate_sketch_from_suggestion(suggestion_id):
    entry_id = request.form.get("entry_id", type=int)
    project_id = request.form.get("project_id")
    data = {"project_id": project_id} if project_id else {}
    resp = requests.post(
        f"{API}/journal-suggestions/{suggestion_id}/generate-sketch",
        data=data,
        timeout=120,
    )
    if not resp.ok:
        try:
            detail = resp.json().get("detail", "Could not generate sketch.")
        except ValueError:
            detail = "Could not generate sketch."
        flash(detail, "error")
        if entry_id:
            return redirect(url_for("journal.detail", entry_id=entry_id))
        return redirect(url_for("journal.index"))
    sketch_id = resp.json().get("sketch_id")
    flash("Sketch generated.", "success")
    return redirect(url_for("sketches.detail", sketch_id=sketch_id))
