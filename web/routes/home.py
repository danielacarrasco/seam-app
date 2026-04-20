import os
import requests
from datetime import datetime
from flask import Blueprint, render_template

bp = Blueprint("home", __name__)
API = os.getenv("API_BASE_URL", "http://localhost:8000")


def time_of_day():
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    return "evening"


@bp.route("/")
def index():
    active = requests.get(f"{API}/projects/", params={"status": "sewing"})
    ideas = requests.get(f"{API}/projects/", params={"status": "idea"})
    fabrics = requests.get(f"{API}/fabrics/")
    patterns = requests.get(f"{API}/patterns/")

    all_fabrics = fabrics.json() if fabrics.ok else []
    stash_summary = {
        "total": len(all_fabrics),
        "reserved": sum(1 for f in all_fabrics if f.get("reserved")),
        "available": sum(1 for f in all_fabrics if not f.get("reserved")),
    }

    return render_template(
        "home/index.html",
        time_of_day=time_of_day(),
        active_projects=(active.json() if active.ok else [])[:3],
        ideas=(ideas.json() if ideas.ok else [])[:4],
        stash_summary=stash_summary,
        recent_fabrics=all_fabrics[-3:],
        recent_patterns=(patterns.json() if patterns.ok else [])[-2:],
    )
