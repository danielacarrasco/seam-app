import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("stash", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")


@bp.route("/")
def index():
    params = {k: v for k, v in request.args.items() if v}
    resp = requests.get(f"{API}/fabrics/", params=params)
    fabrics = resp.json() if resp.ok else []
    return render_template("stash/index.html", fabrics=fabrics, filters=params)


@bp.route("/new")
def new():
    return render_template("stash/new.html")


@bp.route("/", methods=["POST"])
def create():
    data = {
        "nickname": request.form.get("nickname"),
        "fiber_content": request.form.get("fiber_content"),
        "color": request.form.get("color"),
        "print_pattern": request.form.get("print_pattern"),
        "length_meters": request.form.get("length_meters"),
        "width_cm": request.form.get("width_cm"),
        "weight_gsm": request.form.get("weight_gsm"),
        "stretch": request.form.get("stretch") == "on",
        "drape_structure": request.form.get("drape_structure"),
        "opacity": request.form.get("opacity"),
        "care_instructions": request.form.get("care_instructions"),
        "source_store": request.form.get("source_store"),
        "cost": request.form.get("cost"),
        "date_acquired": request.form.get("date_acquired"),
        "suitable_garment_types": request.form.getlist("suitable_garment_types"),
        "notes": request.form.get("notes"),
    }
    data = {k: (None if v == "" else v) for k, v in data.items()}
    resp = requests.post(f"{API}/fabrics/", json=data)
    if resp.ok:
        fabric = resp.json()
        if "photo" in request.files and request.files["photo"].filename:
            photo = request.files["photo"]
            requests.post(
                f"{API}/fabrics/{fabric.get('id')}/photo",
                files={"file": (photo.filename, photo.stream, photo.content_type)},
            )
        flash("Fabric added to stash.", "success")
        return redirect(url_for("stash.detail", fabric_id=fabric.get("id")))
    flash("Something went wrong. Please try again.", "error")
    return redirect(url_for("stash.new"))


@bp.route("/<int:fabric_id>")
def detail(fabric_id):
    resp = requests.get(f"{API}/fabrics/{fabric_id}")
    if not resp.ok:
        flash("Fabric not found.", "error")
        return redirect(url_for("stash.index"))
    fabric = resp.json()
    suitable = requests.get(f"{API}/fabrics/{fabric_id}/suitable-projects")
    suitable_projects = suitable.json() if suitable.ok else []
    used_resp = requests.get(f"{API}/projects/", params={"fabric_id": fabric_id})
    used_in = used_resp.json() if used_resp.ok else []
    used_ids = {p["id"] for p in used_in}
    all_resp = requests.get(f"{API}/projects/")
    available_projects = [
        p for p in (all_resp.json() if all_resp.ok else [])
        if p["id"] not in used_ids
    ]
    return render_template(
        "stash/detail.html",
        fabric=fabric,
        suitable_projects=suitable_projects,
        used_in=used_in,
        available_projects=available_projects,
    )


@bp.route("/<int:fabric_id>/edit")
def edit(fabric_id):
    resp = requests.get(f"{API}/fabrics/{fabric_id}")
    if not resp.ok:
        flash("Fabric not found.", "error")
        return redirect(url_for("stash.index"))
    return render_template("stash/edit.html", fabric=resp.json())


@bp.route("/<int:fabric_id>/edit", methods=["POST"])
def update(fabric_id):
    data = {k: v for k, v in request.form.items() if v and k != "csrf_token"}
    if "stretch" in request.form:
        data["stretch"] = request.form.get("stretch") == "on"
    resp = requests.patch(f"{API}/fabrics/{fabric_id}", json=data)
    if resp.ok:
        flash("Fabric updated.", "success")
        return redirect(url_for("stash.detail", fabric_id=fabric_id))
    flash("Something went wrong.", "error")
    return redirect(url_for("stash.edit", fabric_id=fabric_id))


@bp.route("/<int:fabric_id>/delete", methods=["POST"])
def delete(fabric_id):
    requests.delete(f"{API}/fabrics/{fabric_id}")
    flash("Fabric removed from stash.", "success")
    return redirect(url_for("stash.index"))


@bp.route("/<int:fabric_id>/photo", methods=["POST"])
def upload_photo(fabric_id):
    if "photo" not in request.files or not request.files["photo"].filename:
        flash("No file selected.", "error")
        return redirect(url_for("stash.detail", fabric_id=fabric_id))
    photo = request.files["photo"]
    requests.post(
        f"{API}/fabrics/{fabric_id}/photo",
        files={"file": (photo.filename, photo.stream, photo.content_type)},
    )
    flash("Photo updated.", "success")
    return redirect(url_for("stash.detail", fabric_id=fabric_id))


@bp.route("/<int:fabric_id>/use-in", methods=["POST"])
def use_in_project(fabric_id):
    project_id = request.form.get("project_id")
    if not project_id:
        flash("Pick a project first.", "error")
    else:
        requests.post(f"{API}/projects/{project_id}/fabrics/{fabric_id}")
        flash("Fabric linked to project.", "success")
    return redirect(url_for("stash.detail", fabric_id=fabric_id))


@bp.route("/<int:fabric_id>/unlink/<int:project_id>", methods=["POST"])
def unlink_from_project(fabric_id, project_id):
    requests.delete(f"{API}/projects/{project_id}/fabrics/{fabric_id}")
    flash("Unlinked from project.", "success")
    return redirect(url_for("stash.detail", fabric_id=fabric_id))


@bp.route("/<int:fabric_id>/reserve/<int:project_id>", methods=["POST"])
def reserve(fabric_id, project_id):
    requests.put(f"{API}/fabrics/{fabric_id}/reserve/{project_id}")
    flash("Fabric reserved.", "success")
    return redirect(url_for("stash.detail", fabric_id=fabric_id))


@bp.route("/<int:fabric_id>/release", methods=["POST"])
def release(fabric_id):
    requests.delete(f"{API}/fabrics/{fabric_id}/reserve")
    flash("Reservation released.", "success")
    return redirect(url_for("stash.detail", fabric_id=fabric_id))
