import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("projects", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")


@bp.route("/")
def index():
    params = {k: v for k, v in request.args.items() if v}
    resp = requests.get(f"{API}/projects/", params=params)
    projects = resp.json() if resp.ok else []
    return render_template("projects/index.html", projects=projects, filters=params)


@bp.route("/new")
def new():
    return render_template("projects/new.html")


@bp.route("/", methods=["POST"])
def create():
    data = {
        "title": request.form.get("title"),
        "garment_type": request.form.get("garment_type"),
        "status": request.form.get("status", "idea"),
        "season": request.form.get("season"),
        "occasion": request.form.get("occasion"),
        "priority": request.form.get("priority"),
        "difficulty": request.form.get("difficulty"),
        "estimated_meterage": request.form.get("estimated_meterage"),
        "notes": request.form.get("notes"),
        "category_tags": request.form.getlist("category_tags"),
    }
    data = {k: (None if v == "" else v) for k, v in data.items()}
    resp = requests.post(f"{API}/projects/", json=data)
    if resp.ok:
        project = resp.json()
        flash("Project created.", "success")
        return redirect(url_for("projects.detail", project_id=project.get("id")))
    flash("Something went wrong. Please try again.", "error")
    return redirect(url_for("projects.new"))


@bp.route("/<int:project_id>")
def detail(project_id):
    resp = requests.get(f"{API}/projects/{project_id}")
    if not resp.ok:
        flash("Project not found.", "error")
        return redirect(url_for("projects.index"))
    project = resp.json()
    log_resp = requests.get(f"{API}/projects/{project_id}/log")
    log = log_resp.json() if log_resp.ok else []
    sketches_resp = requests.get(f"{API}/sketches/", params={"project_id": project_id})
    sketches = sketches_resp.json() if sketches_resp.ok else []
    linked_fabric_ids = {f["id"] for f in project.get("fabrics") or []}
    fabrics_resp = requests.get(f"{API}/fabrics/")
    available_fabrics = [
        f for f in (fabrics_resp.json() if fabrics_resp.ok else [])
        if f["id"] not in linked_fabric_ids
    ]
    patterns_resp = requests.get(f"{API}/patterns/")
    available_patterns = patterns_resp.json() if patterns_resp.ok else []
    return render_template(
        "projects/detail.html",
        project=project,
        log=log,
        sketches=sketches,
        available_fabrics=available_fabrics,
        available_patterns=available_patterns,
    )


@bp.route("/<int:project_id>/edit")
def edit(project_id):
    resp = requests.get(f"{API}/projects/{project_id}")
    if not resp.ok:
        flash("Project not found.", "error")
        return redirect(url_for("projects.index"))
    return render_template("projects/edit.html", project=resp.json())


@bp.route("/<int:project_id>/edit", methods=["POST"])
def update(project_id):
    data = {k: v for k, v in request.form.items() if v and k != "csrf_token"}
    resp = requests.patch(f"{API}/projects/{project_id}", json=data)
    if resp.ok:
        flash("Project updated.", "success")
        return redirect(url_for("projects.detail", project_id=project_id))
    flash("Something went wrong.", "error")
    return redirect(url_for("projects.edit", project_id=project_id))


@bp.route("/<int:project_id>/delete", methods=["POST"])
def delete(project_id):
    requests.delete(f"{API}/projects/{project_id}")
    flash("Project deleted.", "success")
    return redirect(url_for("projects.index"))


@bp.route("/<int:project_id>/log", methods=["POST"])
def add_log(project_id):
    data = {"note": request.form.get("note")}
    requests.post(f"{API}/projects/{project_id}/log", json=data)
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/<int:project_id>/log/<int:entry_id>/delete", methods=["POST"])
def delete_log(project_id, entry_id):
    requests.delete(f"{API}/projects/{project_id}/log/{entry_id}")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/<int:project_id>/fabrics/<int:fabric_id>/link", methods=["POST"])
def link_fabric(project_id, fabric_id):
    requests.post(f"{API}/projects/{project_id}/fabrics/{fabric_id}")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/<int:project_id>/fabrics/link", methods=["POST"])
def link_fabric_picker(project_id):
    fabric_id = request.form.get("fabric_id")
    if not fabric_id:
        flash("Pick a fabric first.", "error")
    else:
        requests.post(f"{API}/projects/{project_id}/fabrics/{fabric_id}")
        flash("Fabric linked.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/<int:project_id>/fabrics/<int:fabric_id>/unlink", methods=["POST"])
def unlink_fabric(project_id, fabric_id):
    requests.delete(f"{API}/projects/{project_id}/fabrics/{fabric_id}")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/<int:project_id>/pattern/<int:pattern_id>/set", methods=["POST"])
def set_pattern(project_id, pattern_id):
    requests.put(f"{API}/projects/{project_id}/pattern/{pattern_id}")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/<int:project_id>/pattern/set", methods=["POST"])
def set_pattern_picker(project_id):
    pattern_id = request.form.get("pattern_id")
    if not pattern_id:
        flash("Pick a pattern first.", "error")
    else:
        requests.put(f"{API}/projects/{project_id}/pattern/{pattern_id}")
        flash("Pattern linked.", "success")
    return redirect(url_for("projects.detail", project_id=project_id))


@bp.route("/<int:project_id>/pattern/remove", methods=["POST"])
def remove_pattern(project_id):
    requests.delete(f"{API}/projects/{project_id}/pattern")
    return redirect(url_for("projects.detail", project_id=project_id))
