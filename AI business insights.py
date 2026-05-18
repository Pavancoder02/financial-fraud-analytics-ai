"""
BizInsight AI — Flask Backend
Run: python app.py
"""
import os
import sys
import json
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import pandas as pd

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent))
from analyzer import clean_dataframe, run_analysis, build_ai_prompt
from pdf_generator import generate_pdf_report

app = Flask(
    __name__,
    static_folder="../frontend/static",
    template_folder="../frontend/templates",
)
CORS(app)

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")


@app.route("/api/sample-data", methods=["GET"])
def get_sample_data():
    """Return the sample dataset as JSON for the frontend."""
    csv_path = DATA_DIR / "ecommerce_sales.csv"
    if not csv_path.exists():
        return jsonify({"error": "Sample data not found. Run generate_sample.py first."}), 404
    df = pd.read_csv(csv_path)
    return jsonify({
        "rows": len(df),
        "columns": list(df.columns),
        "preview": df.head(8).to_dict(orient="records"),
    })


@app.route("/api/upload", methods=["POST"])
def upload_csv():
    """
    Accept a CSV upload, clean it, run analysis, return structured results.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({"error": f"Could not parse CSV: {str(e)}"}), 400

    return _process_dataframe(df, file.filename)


@app.route("/api/load-sample", methods=["POST"])
def load_sample():
    """Load and analyse the built-in sample dataset."""
    csv_path = DATA_DIR / "ecommerce_sales.csv"
    if not csv_path.exists():
        return jsonify({"error": "Sample data not found"}), 404
    df = pd.read_csv(csv_path)
    return _process_dataframe(df, "ecommerce_sales.csv")


def _process_dataframe(df: pd.DataFrame, filename: str):
    try:
        cleaned_df, cleaning_report = clean_dataframe(df)
        analysis = run_analysis(cleaned_df)
        return jsonify({
            "status": "ok",
            "filename": filename,
            "cleaning_report": cleaning_report,
            "analysis": analysis,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/insights", methods=["POST"])
def get_insights():
    """
    Proxy request to Claude API and return AI-generated insights.
    Expects: { analysis: {...}, question_type: "general"|"regional"|... }
    """
    body = request.get_json()
    if not body:
        return jsonify({"error": "No JSON body"}), 400

    analysis = body.get("analysis", {})
    question_type = body.get("question_type", "general")
    api_key = body.get("api_key") or ANTHROPIC_API_KEY

    if not api_key:
        return jsonify({"error": "No Anthropic API key provided. Set ANTHROPIC_API_KEY env var or pass in request."}), 400

    prompt = build_ai_prompt(analysis, question_type)

    import urllib.request
    import urllib.error

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        insight_text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        return jsonify({"insight": insight_text})
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        return jsonify({"error": f"Claude API error {e.code}: {err_body}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export-pdf", methods=["POST"])
def export_pdf():
    """Generate and return a PDF report."""
    body = request.get_json()
    if not body:
        return jsonify({"error": "No data"}), 400

    analysis = body.get("analysis", {})
    ai_insight = body.get("insight", "No AI insight available.")

    try:
        filepath = generate_pdf_report(analysis, ai_insight)
        return send_file(
            filepath,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=Path(filepath).name,
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "version": "1.0.0"})


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  BizInsight AI — Backend Server")
    print("  http://localhost:5000")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)