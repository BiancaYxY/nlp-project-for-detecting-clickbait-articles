import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from scraping.extractor import extract_article
from nlp.semantic_similarity import compute_similarity
from nlp.entailment import compute_entailment
from nlp.clickbait import compute_clickbait
from decision.verdict import compute_verdict

app = Flask(__name__)
CORS(app)  # => we can use React bc of this


# === some kind of helpers ===
def detect_language_from_text(title: str, text: str) -> str:
    combined = f"{title} {text}".lower()

    romanian_markers = [
        "ă", "â", "î", "ș", "ş", "ț", "ţ",
        "este", "sunt", "care", "pentru", "după", "intră",
        "românia", "vedetă", "articol", "declarație", "fanii"
    ]
    english_markers = [
        "the", "is", "are", "what", "after", "before",
        "celebrity", "article", "statement", "fans", "news"
    ]

    ro_score = sum(1 for m in romanian_markers if m in combined)
    en_score = sum(1 for m in english_markers if m in combined)

    return "ro" if ro_score >= en_score else "en"


def run_pipeline(url: str) -> dict:
    scraping_data = extract_article(url)

    cleaned = scraping_data.get("cleaned", {})
    language = detect_language_from_text(
        cleaned.get("title", ""),
        cleaned.get("text", "")
    )

    similarity_result = compute_similarity(scraping_data, language=language)
    entailment_result = compute_entailment(scraping_data, language=language)
    clickbait_result  = compute_clickbait(scraping_data,  language=language)
    verdict_result    = compute_verdict(similarity_result, entailment_result, clickbait_result)

    return {
        "url": url,
        "language": language,
        "scraping": scraping_data,
        "semantic_similarity": similarity_result,
        "entailment": entailment_result,
        "clickbait": clickbait_result,
        "verdict": verdict_result,
    }


# === rute ===
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Primeste un URL si returneaza rezultatul complet al pipeline-ului

    Body JSON asteptat:
        { "url": "https://example.com/article" }

    Raspuns:
        {
            "url": str,
            "language": "ro" | "en",
            "scraping": { ... },
            "semantic_similarity": { ... },
            "entailment": { ... },
            "clickbait": { ... },
            "verdict": {
                "verdict": "reliable" | "misleading" | "clickbait" | "unverifiable",
                "confidence": float,
                "signals": { ... },
                "flags": [ str ]
            }
        }
    """
    body = request.get_json(silent=True)

    if not body or not body.get("url"):
        return jsonify({"error": "Missing 'url' in request body."}), 400

    url = body["url"].strip()
    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "Invalid URL. Must start with http:// or https://."}), 400

    try:
        result = run_pipeline(url)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({
            "url": url,
            "status": "error",
            "message": str(exc)
        }), 500


if __name__ == "__main__":
    # debug=False in prod si tb sa schimbam portul daca e nevoie
    app.run(host="0.0.0.0", port=5000, debug=True)