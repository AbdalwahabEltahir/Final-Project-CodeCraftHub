import json
import os
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = "courses.json"
VALID_STATUSES = ["Not Started", "In Progress", "Completed"]


def load_courses():
    """Read all courses from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_courses(courses):
    """Write all courses to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(courses, f, indent=2)


def get_next_id(courses):
    """Generate a new course ID."""
    return max([c["id"] for c in courses], default=0) + 1


def validate(data, require_all=True):
    if not isinstance(data, dict):
        return "Request body must be JSON"
    required = ["name", "description", "target_date", "status"]
    if require_all:
        missing = [k for k in required if not data.get(k)]
        if missing:
            return f"Missing required fields: {', '.join(missing)}"
    if "status" in data and data["status"] not in VALID_STATUSES:
        return f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
    if "target_date" in data:
        try:
            datetime.strptime(data["target_date"], "%Y-%m-%d")
        except (ValueError, TypeError):
            return "target_date must be in YYYY-MM-DD format"
    return None


# ---- Bonus endpoints ----
@app.route("/api/courses/stats", methods=["GET"])
def get_stats():
    courses = load_courses()
    stats = {"total": len(courses)}
    for status in VALID_STATUSES:
        stats[status] = sum(1 for c in courses if c["status"] == status)
    return jsonify(stats), 200


@app.route("/api/courses/search", methods=["GET"])
def search_courses():
    term = request.args.get("q", "").strip().lower()
    if not term:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    results = [
        c for c in load_courses()
        if term in c["name"].lower() or term in c["description"].lower()
    ]
    return jsonify(results), 200


# ---- Core CRUD endpoints ----
@app.route("/api/courses", methods=["POST"])
def create_course():
    data = request.get_json(silent=True)
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400
    courses = load_courses()
    course = {
        "id": get_next_id(courses),
        "name": data["name"],
        "description": data["description"],
        "target_date": data["target_date"],
        "status": data["status"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    courses.append(course)
    save_courses(courses)
    return jsonify(course), 201


@app.route("/api/courses", methods=["GET"])
def get_courses():
    return jsonify(load_courses()), 200


@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    for course in load_courses():
        if course["id"] == course_id:
            return jsonify(course), 200
    return jsonify({"error": "Course not found"}), 404


@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def update_course(course_id):
    data = request.get_json(silent=True)
    error = validate(data, require_all=False)
    if error:
        return jsonify({"error": error}), 400
    courses = load_courses()
    for course in courses:
        if course["id"] == course_id:
            for key in ["name", "description", "target_date", "status"]:
                if key in data:
                    course[key] = data[key]
            save_courses(courses)
            return jsonify(course), 200
    return jsonify({"error": "Course not found"}), 404


@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def delete_course(course_id):
    courses = load_courses()
    remaining = [c for c in courses if c["id"] != course_id]
    if len(remaining) == len(courses):
        return jsonify({"error": "Course not found"}), 404
    save_courses(remaining)
    return jsonify({"message": "Course deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)