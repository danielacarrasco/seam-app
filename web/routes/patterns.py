import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("patterns", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")


@bp.route("/")
def index():
    params = {k: v for k, v in request.args.items() if v}
    resp = requests.get(f"{API}/patterns/", params=params)
    patterns = resp.json() if resp.ok else []
    return render_template("patterns/index.html", patterns=patterns, filters=params)


@bp.route("/new")
def new():
    return render_template("patterns/new.html")


@bp.route("/", methods=["POST"])
def create():
    data = {
        "brand": request.form.get("brand"),
        "designer": request.form.get("designer"),
        "pattern_name": request.form.get("pattern_name"),
        "pattern_number": request.form.get("pattern_number"),
        "garment_type": request.form.get("garment_type"),
        "size_chosen": request.form.get("size_chosen"),
        "size_range": request.form.get("size_range"),
        "view_version": request.form.get("view_version"),
        "recommended_fabrics": request.form.get("recommended_fabrics"),
        "instructions_rating": request.form.get("instructions_rating"),
        "notes": request.form.get("notes"),
    }
    data = {k: (None if v == "" else v) for k, v in data.items()}
    resp = requests.post(f"{API}/patterns/", json=data)
    if resp.ok:
        pattern = resp.json()
        if "image" in request.files and request.files["image"].filename:
            img = request.files["image"]
            requests.post(
                f"{API}/patterns/{pattern.get('id')}/image",
                files={"file": (img.filename, img.stream, img.content_type)},
            )
        flash("Pattern added to library.", "success")
        return redirect(url_for("patterns.detail", pattern_id=pattern.get("id")))
    flash("Something went wrong. Please try again.", "error")
    return redirect(url_for("patterns.new"))


@bp.route("/<int:pattern_id>")
def detail(pattern_id):
    resp = requests.get(f"{API}/patterns/{pattern_id}")
    if not resp.ok:
        flash("Pattern not found.", "error")
        return redirect(url_for("patterns.index"))
    pattern = resp.json()
    history_resp = requests.get(f"{API}/patterns/{pattern_id}/fit-history")
    fit_history = history_resp.json() if history_resp.ok else []
    return render_template(
        "patterns/detail.html", pattern=pattern, fit_history=fit_history
    )


@bp.route("/<int:pattern_id>/edit")
def edit(pattern_id):
    resp = requests.get(f"{API}/patterns/{pattern_id}")
    if not resp.ok:
        flash("Pattern not found.", "error")
        return redirect(url_for("patterns.index"))
    return render_template("patterns/edit.html", pattern=resp.json())


@bp.route("/<int:pattern_id>/edit", methods=["POST"])
def update(pattern_id):
    data = {k: v for k, v in request.form.items() if v and k != "csrf_token"}
    resp = requests.patch(f"{API}/patterns/{pattern_id}", json=data)
    if resp.ok:
        flash("Pattern updated.", "success")
        return redirect(url_for("patterns.detail", pattern_id=pattern_id))
    flash("Something went wrong.", "error")
    return redirect(url_for("patterns.edit", pattern_id=pattern_id))


@bp.route("/<int:pattern_id>/delete", methods=["POST"])
def delete(pattern_id):
    requests.delete(f"{API}/patterns/{pattern_id}")
    flash("Pattern removed from library.", "success")
    return redirect(url_for("patterns.index"))


@bp.route("/<int:pattern_id>/image", methods=["POST"])
def upload_image(pattern_id):
    if "image" not in request.files or not request.files["image"].filename:
        flash("No file selected.", "error")
        return redirect(url_for("patterns.detail", pattern_id=pattern_id))
    img = request.files["image"]
    requests.post(
        f"{API}/patterns/{pattern_id}/image",
        files={"file": (img.filename, img.stream, img.content_type)},
    )
    flash("Image updated.", "success")
    return redirect(url_for("patterns.detail", pattern_id=pattern_id))


@bp.route("/<int:pattern_id>/fit-history", methods=["POST"])
def add_fit_history(pattern_id):
    data = {
        "alterations_made": request.form.get("alterations_made"),
        "fit_notes": request.form.get("fit_notes"),
        "size_used": request.form.get("size_used"),
        "linked_make_id": request.form.get("linked_make_id"),
    }
    requests.post(f"{API}/patterns/{pattern_id}/fit-history", json=data)
    flash("Fit history entry added.", "success")
    return redirect(url_for("patterns.detail", pattern_id=pattern_id))


@bp.route("/<int:pattern_id>/fit-history/<int:entry_id>/delete", methods=["POST"])
def delete_fit_history(pattern_id, entry_id):
    requests.delete(f"{API}/patterns/{pattern_id}/fit-history/{entry_id}")
    return redirect(url_for("patterns.detail", pattern_id=pattern_id))
