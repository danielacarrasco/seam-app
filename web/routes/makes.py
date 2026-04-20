import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("makes", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")


@bp.route("/")
def index():
    params = {k: v for k, v in request.args.items() if v}
    resp = requests.get(f"{API}/makes/", params=params)
    makes = resp.json() if resp.ok else []
    insights_resp = requests.get(f"{API}/makes/insights/summary")
    insights = insights_resp.json() if insights_resp.ok else {}
    return render_template(
        "makes/index.html", makes=makes, filters=params, insights=insights
    )


@bp.route("/new")
def new():
    projects_resp = requests.get(f"{API}/projects/", params={"status": "sewing"})
    projects = projects_resp.json() if projects_resp.ok else []
    return render_template("makes/new.html", projects=projects)


@bp.route("/", methods=["POST"])
def create():
    data = {
        "project_id": request.form.get("project_id"),
        "fabric_id": request.form.get("fabric_id"),
        "pattern_id": request.form.get("pattern_id"),
        "construction_notes": request.form.get("construction_notes"),
        "fit_outcome": request.form.get("fit_outcome"),
        "what_worked": request.form.get("what_worked"),
        "what_didnt": request.form.get("what_didnt"),
        "would_remake": request.form.get("would_remake") == "on",
        "wear_frequency": request.form.get("wear_frequency"),
        "care_outcome": request.form.get("care_outcome"),
        "lessons_learned": request.form.get("lessons_learned"),
    }
    resp = requests.post(f"{API}/makes/", json=data)
    if resp.ok:
        make = resp.json()
        for photo in request.files.getlist("photos"):
            if photo.filename:
                requests.post(
                    f"{API}/makes/{make.get('id')}/photos",
                    files={"file": (photo.filename, photo.stream, photo.content_type)},
                )
        flash("Make archived.", "success")
        return redirect(url_for("makes.detail", make_id=make.get("id")))
    flash("Something went wrong. Please try again.", "error")
    return redirect(url_for("makes.new"))


@bp.route("/<int:make_id>")
def detail(make_id):
    resp = requests.get(f"{API}/makes/{make_id}")
    if not resp.ok:
        flash("Make not found.", "error")
        return redirect(url_for("makes.index"))
    make = resp.json()
    photos_resp = requests.get(f"{API}/makes/{make_id}/photos")
    photos = photos_resp.json() if photos_resp.ok else []
    return render_template("makes/detail.html", make=make, photos=photos)


@bp.route("/<int:make_id>/edit")
def edit(make_id):
    resp = requests.get(f"{API}/makes/{make_id}")
    if not resp.ok:
        flash("Make not found.", "error")
        return redirect(url_for("makes.index"))
    return render_template("makes/edit.html", make=resp.json())


@bp.route("/<int:make_id>/edit", methods=["POST"])
def update(make_id):
    data = {k: v for k, v in request.form.items() if v and k != "csrf_token"}
    if "would_remake" in request.form:
        data["would_remake"] = request.form.get("would_remake") == "on"
    resp = requests.patch(f"{API}/makes/{make_id}", json=data)
    if resp.ok:
        flash("Make updated.", "success")
        return redirect(url_for("makes.detail", make_id=make_id))
    flash("Something went wrong.", "error")
    return redirect(url_for("makes.edit", make_id=make_id))


@bp.route("/<int:make_id>/delete", methods=["POST"])
def delete(make_id):
    requests.delete(f"{API}/makes/{make_id}")
    flash("Make deleted.", "success")
    return redirect(url_for("makes.index"))


@bp.route("/<int:make_id>/photos", methods=["POST"])
def upload_photo(make_id):
    uploaded = 0
    for photo in request.files.getlist("photos"):
        if photo.filename:
            requests.post(
                f"{API}/makes/{make_id}/photos",
                files={"file": (photo.filename, photo.stream, photo.content_type)},
            )
            uploaded += 1
    if uploaded:
        flash(f"{uploaded} photo(s) uploaded.", "success")
    else:
        flash("No files selected.", "error")
    return redirect(url_for("makes.detail", make_id=make_id))


@bp.route("/<int:make_id>/photos/<int:photo_id>/delete", methods=["POST"])
def delete_photo(make_id, photo_id):
    requests.delete(f"{API}/makes/{make_id}/photos/{photo_id}")
    return redirect(url_for("makes.detail", make_id=make_id))
