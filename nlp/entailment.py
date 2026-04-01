from typing import Dict

from transformers import pipeline


EN_MODEL_NAME = "cross-encoder/nli-deberta-v3-small"
RO_MODEL_NAME = "joeddav/xlm-roberta-large-xnli"

LABEL_ENTAILMENT = "entailment"
LABEL_NEUTRAL = "neutral"
LABEL_CONTRADICTION = "contradiction"


class EntailmentService:
    def __init__(
        self,
        en_model_name: str = EN_MODEL_NAME,
        ro_model_name: str = RO_MODEL_NAME,
    ):
        self.en_model_name = en_model_name
        self.ro_model_name = ro_model_name

        self._en_pipeline = None
        self._ro_pipeline = None

    def _load_en_pipeline(self):
        if self._en_pipeline is None:
            self._en_pipeline = pipeline(
                "zero-shot-classification",
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

    def _select_pipeline(self, language: str):
        language = (language or "en").lower()
        if language == "ro":
            return self._load_ro_pipeline(), self.ro_model_name
        return self._load_en_pipeline(), self.en_model_name

    @staticmethod
    def _truncate(text: str, max_chars: int = 1500) -> str:
        if not text:
            return ""
        return text.strip()[:max_chars]

    def compute(self, headline: str, article_text: str, language: str = "en") -> Dict:
        headline = (headline or "").strip()
        article_text = self._truncate(article_text)

        if not headline or not article_text:
            return {
                "language": language,
                "model_used": None,
                "label": None,
                "scores": {},
                "status": "missing_input",
            }

        nli_pipeline, model_name = self._select_pipeline(language)

        # 0-shot-classification:
        # the premise is the article text,
        # the hypothesis (candidate label) is derived from the headline.
        # The three NLI labels are used as candidate labels directly.
        result = nli_pipeline(
            sequences=article_text,
            candidate_labels=[LABEL_ENTAILMENT, LABEL_NEUTRAL, LABEL_CONTRADICTION],
            hypothesis_template="The article headline states: " + headline + ". This is {}.",
        )

        labels = result["labels"]
        scores = result["scores"]

        scores_dict = {label: round(float(score), 4) for label, score in zip(labels, scores)}
        top_label = labels[0]

        return {
            "language": language,
            "model_used": model_name,
            "label": top_label,
            "scores": scores_dict,
            "status": "ok",
        }


_entailment_service = EntailmentService()


def compute_entailment(scraping_data: Dict, language: str = "en") -> Dict:
    cleaned = scraping_data.get("cleaned", {})
    headline = cleaned.get("title", "")
    article_text = cleaned.get("text", "")

    return _entailment_service.compute(
        headline=headline,
        article_text=article_text,
        language=language,
    )