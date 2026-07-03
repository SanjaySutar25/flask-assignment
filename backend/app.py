from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # allow requests from the Express frontend (different host/port)

# ---- in-memory "database" (simple, no external DB needed for this assignment) ----
todos = [
    {"id": 1, "task": "Deploy Flask backend", "done": False},
    {"id": 2, "task": "Deploy Express frontend", "done": False},
]
next_id = 3


@app.route("/api/health", methods=["GET"])
def health():
    """Used to verify the backend is up and reachable."""
    return jsonify({
        "status": "ok",
        "service": "flask-backend",
        "hostname": os.uname().nodename
    })


@app.route("/api/todos", methods=["GET"])
def get_todos():
    return jsonify(todos)


@app.route("/api/todos", methods=["POST"])
def add_todo():
    global next_id
    data = request.get_json(force=True)
    task = data.get("task", "").strip()
    if not task:
        return jsonify({"error": "task is required"}), 400
    todo = {"id": next_id, "task": task, "done": False}
    todos.append(todo)
    next_id += 1
    return jsonify(todo), 201


@app.route("/api/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json(force=True)
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = data.get("done", t["done"])
            return jsonify(t)
    return jsonify({"error": "not found"}), 404


@app.route("/api/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    global todos
    todos = [t for t in todos if t["id"] != todo_id]
    return jsonify({"result": "deleted"})


if __name__ == "__main__":
    # 0.0.0.0 so it's reachable from outside the container / EC2 instance
    app.run(host="0.0.0.0", port=5000, debug=True)
