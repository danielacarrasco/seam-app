import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("measurements", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")


MEASUREMENT_FIELDS = (
    "bust",
    "waist",
    "hips",
    "high_bust",
    "back_length",
    "front_length",
    "shoulder_width",
    "sleeve_length",
    "inseam",
    "rise",
    "neck",
    "upper_arm",
    "wrist",
    "thigh",
    "calf",
    "height",
    "weight",
)


def _numeric(form, field):
    raw = form.get(field, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


@bp.route("/")
def index():
    profile_resp = requests.get(f"{API}/measurements/")
    profile = profile_resp.json() if profile_resp.ok else {}
    alts_resp = requests.get(f"{API}/measurements/alterations")
    alterations = alts_resp.json() if alts_resp.ok else []
    notes_resp = requests.get(f"{API}/measurements/fit-notes")
    fit_notes = notes_resp.json() if notes_resp.ok else []
    history_resp = requests.get(f"{API}/measurements/history")
    history = history_resp.json() if history_resp.ok else []
    return render_template(
        "measurements/index.html",
        profile=profile,
        alterations=alterations,
        fit_notes=fit_notes,
        history=history,
        fields=MEASUREMENT_FIELDS,
    )


@bp.route("/", methods=["POST"])
def save():
    data = {field: _numeric(request.form, field) for field in MEASUREMENT_FIELDS}
    data["preferred_ease"] = request.form.get("preferred_ease") or None
    data["fit_notes"] = request.form.get("fit_notes") or None
    resp = requests.patch(f"{API}/measurements/", json=data)
    if resp.ok:
        flash("Measurements saved.", "success")
    else:
        flash("Something went wrong.", "error")
    return redirect(url_for("measurements.index"))


@bp.route("/alterations", methods=["POST"])
def add_alteration():
    data = {
        "label": request.form.get("label"),
        "notes": request.form.get("notes") or None,
    }
    if not data["label"]:
        flash("Label is required.", "error")
    else:
        requests.post(f"{API}/measurements/alterations", json=data)
        flash("Alteration added.", "success")
    return redirect(url_for("measurements.index"))


@bp.route("/alterations/<int:alteration_id>/delete", methods=["POST"])
def delete_alteration(alteration_id):
    requests.delete(f"{API}/measurements/alterations/{alteration_id}")
    return redirect(url_for("measurements.index"))


@bp.route("/fit-notes", methods=["POST"])
def add_fit_note():
    data = {
        "garment_type": request.form.get("garment_type"),
        "note": request.form.get("note"),
    }
    if not (data["garment_type"] and data["note"]):
        flash("Garment type and note are required.", "error")
    else:
        requests.post(f"{API}/measurements/fit-notes", json=data)
        flash("Fit note added.", "success")
    return redirect(url_for("measurements.index"))


@bp.route("/fit-notes/<int:note_id>/delete", methods=["POST"])
def delete_fit_note(note_id):
    requests.delete(f"{API}/measurements/fit-notes/{note_id}")
    return redirect(url_for("measurements.index"))
