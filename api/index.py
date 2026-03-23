"""
Vercel Serverless API — wraps the multi-agent pipeline as a web endpoint.
"""

import sys
import os
import json
import tempfile

# Add parent directory to path so we can import pipeline and agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "public"))


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/run", methods=["POST"])
def run_pipeline():
    data = request.get_json(force=True)
    goal = (data.get("goal") or "").strip()

    if not goal:
        return jsonify({"error": "Goal is required"}), 400

    # Use /tmp for file output on Vercel (only writable dir)
    project_name = "".join(
        c if c.isalnum() or c == "_" else "_"
        for c in goal.lower().replace(" ", "_")
    )[:30]
    output_dir = os.path.join(tempfile.gettempdir(), "mai_output", project_name)

    try:
        import pipeline as p
        result = p.run(user_goal=goal, project_name=project_name)

        return jsonify({
            "success": True,
            "goal_summary": result["plan"].get("goal_summary", goal),
            "tech_stack": result["plan"].get("tech_stack", []),
            "files": result["generated_files"],
            "review": {
                "approved": result["review"].get("approved", False),
                "quality": result["review"].get("overall_quality", "unknown"),
                "summary": result["review"].get("summary", ""),
            },
            "elapsed_seconds": round(result["elapsed_seconds"], 1),
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Multi-Agent AI Builder"})


# Vercel requires the Flask app to be named `app`
