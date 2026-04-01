import re
from typing import Dict

from transformers import pipeline


EN_MODEL_NAME = "elozano/bert-base-cased-clickbait-news"
RO_MODEL_NAME = "joeddav/xlm-roberta-large-xnli"

LABEL_CLICKBAIT = "clickbait"
LABEL_NOT_CLICKBAIT = "not_clickbait"


CLICKBAIT_PATTERNS_EN = [
    r"\byou won't believe\b",
    r"\bthis is why\b",
    r"\bwhat happens (when|next|if)\b",
    r"\b\d+ (things|reasons|ways|secrets|facts|tips)\b",
    r"\bthe truth about\b",
    r"\beveryone is (talking about|saying)\b",
    r"\bshocking\b",
    r"\bblew (our|my|their) mind[s]?\b",
    r"\bmust[- ]see\b",
    r"\bwent viral\b",
    r"\bbreaking[:\s]",
    r"\bexclusive[:\s]",
]

CLICKBAIT_PATTERNS_RO = [
    r"\bnu o să (crezi|îți vină să crezi)\b",
    r"\btoată lumea vorbește\b",
    r"\bsocant\b",
    r"\bsocat\b",
    r"\bai nostri\b",
    r"\bfotografia care a înnebunit\b",
    r"\b\d+ (lucruri|motive|secrete|sfaturi)\b",
    r"\bexclusiv[:\s]",
    r"\bruptă din povești\b",
    r"\biată (ce|cum|de ce)\b",
    r"\baflă (acum|imediat|totul)\b",
    r"\bîți va tăia respirația\b",
    r"\bte va lăsa fără cuvinte\b",
]


def _count_pattern_hits(text: str, patterns: list) -> int:
    normalized = text.lower()
    return sum(1 for pattern in patterns if re.search(pattern, normalized))


def _lexical_clickbait_score(headline: str, language: str) -> float:
    """
    Returns a heuristic score in [0.0, 1.0] based on pattern hits.
    Capped at 1.0, each pattern hit adds 0.25.
    """
    patterns = CLICKBAIT_PATTERNS_RO if language == "ro" else CLICKBAIT_PATTERNS_EN
    hits = _count_pattern_hits(headline, patterns)
    return min(hits * 0.25, 1.0)


# ── Model layer ───────────────────────────────────────────────────────────────
class ClickbaitService:
    def __init__(
        self,
        en_model_name: str = EN_MODEL_NAME,
        ro_model_name: str = RO_MODEL_NAME,
    ):
        self.en_model_name = en_model_name
        self.ro_model_name = ro_model_name

        self._en_pipeline = None
        self._ro_pipeline = None

    # ── Lazy model loading ────────────────────────────────────────────────────
    def _load_en_pipeline(self):
        if self._en_pipeline is None:
            self._en_pipeline = pipeline(
                "text-classification",
                model=self.en_model_name,
            )
        return self._en_pipeline

    def _load_ro_pipeline(self):
        if self._ro_pipeline is None:
            self._ro_pipeline = pipeline(
                "zero-shot-classification",
                model=self.ro_model_name,
            )
        return self._ro_pipeline

    def _predict_en(self, headline: str) -> Dict:
        clf = self._load_en_pipeline()
        raw = clf(headline, truncation=True, max_length=128)[0]

        label_raw = raw["label"].lower()
        model_score = round(float(raw["score"]), 4)

        is_clickbait = "clickbait" in label_raw and "not" not in label_raw

        return {
            "label": LABEL_CLICKBAIT if is_clickbait else LABEL_NOT_CLICKBAIT,
            "model_score": model_score if is_clickbait else round(1 - model_score, 4),
            "model_used": self.en_model_name,
        }

    def _predict_ro(self, headline: str) -> Dict:
        clf = self._load_ro_pipeline()
        result = clf(
            sequences=headline,
            candidate_labels=[LABEL_CLICKBAIT, LABEL_NOT_CLICKBAIT],
        )

        top_label = result["labels"][0]
        scores_dict = {
            label: round(float(score), 4)
            for label, score in zip(result["labels"], result["scores"])
        }

        return {
            "label": top_label,
            "model_score": scores_dict.get(LABEL_CLICKBAIT, 0.0),
            "model_used": self.ro_model_name,
        }

    def compute(self, headline: str, language: str = "en") -> Dict:
        headline = (headline or "").strip()
        language = (language or "en").lower()

        if not headline:
            return {
                "language": language,
                "model_used": None,
                "label": None,
                "model_score": 0.0,
                "lexical_score": 0.0,
                "final_score": 0.0,
                "status": "missing_input",
            }
        try:
            if language == "ro":
                prediction = self._predict_ro(headline)
            else:
                prediction = self._predict_en(headline)
            model_ok = True
        except Exception as exc:
            print(f"[clickbait] Model inference failed: {exc}")
            prediction = {
                "label": None,
                "model_score": 0.0,
                "model_used": None,
            }
            model_ok = False

        lexical_score = _lexical_clickbait_score(headline, language)

        # 70 % model, 30 % lexical (falls back to 100 % lexical if model failed)
        model_score = prediction["model_score"]
        if model_ok:
            final_score = round(0.7 * model_score + 0.3 * lexical_score, 4)
        else:
            final_score = lexical_score

        final_label = prediction["label"]
        if final_label is None:
            final_label = LABEL_CLICKBAIT if final_score >= 0.5 else LABEL_NOT_CLICKBAIT

        return {
            "language": language,
            "model_used": prediction["model_used"],
            "label": final_label,
            "model_score": model_score,
            "lexical_score": lexical_score,
            "final_score": final_score,
            "status": "ok",
        }


_clickbait_service = ClickbaitService()


def compute_clickbait(scraping_data: Dict, language: str = "en") -> Dict:
    cleaned = scraping_data.get("cleaned", {})
    headline = cleaned.get("title", "")

    return _clickbait_service.compute(headline=headline, language=language)