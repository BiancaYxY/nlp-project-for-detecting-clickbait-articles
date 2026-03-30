import json
import sys
from typing import Dict

from scraping.extractor import extract_article
from nlp.semantic_similarity import compute_similarity


def detect_language_from_text(title: str, text: str) -> str:
    """
    Heuristic simplu pentru RO vs EN.
    Poți înlocui mai târziu cu langdetect/fasttext.
    """
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

    ro_score = sum(1 for marker in romanian_markers if marker in combined)
    en_score = sum(1 for marker in english_markers if marker in combined)

    if ro_score >= en_score:
        return "ro"
    return "en"


def build_pipeline_result(url: str) -> Dict:
    scraping_data = extract_article(url)

    cleaned = scraping_data.get("cleaned", {})
    cleaned_title = cleaned.get("title", "")
    cleaned_text = cleaned.get("text", "")

    language = detect_language_from_text(cleaned_title, cleaned_text)

    similarity_result = compute_similarity(scraping_data, language=language)

    return {
        "url": url,
        "language": language,
        "scraping": scraping_data,
        "semantic_similarity": similarity_result
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.main <article_url>")
        sys.exit(1)

    url = sys.argv[1]

    try:
        result = build_pipeline_result(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        error_result = {
            "url": url,
            "status": "error",
            "message": str(exc)
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()