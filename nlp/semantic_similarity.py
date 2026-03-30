from typing import Dict

from sentence_transformers import SentenceTransformer, util


EN_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RO_MODEL_NAME = "BlackKakapo/stsb-xlm-r-multilingual-ro"


class SemanticSimilarityService:
    def __init__(self, en_model_name: str = EN_MODEL_NAME, ro_model_name: str = RO_MODEL_NAME):
        self.en_model_name = en_model_name
        self.ro_model_name = ro_model_name

        self._en_model = None
        self._ro_model = None

    def _load_en_model(self) -> SentenceTransformer:
        if self._en_model is None:
            self._en_model = SentenceTransformer(self.en_model_name)
        return self._en_model

    def _load_ro_model(self) -> SentenceTransformer:
        if self._ro_model is None:
            self._ro_model = SentenceTransformer(self.ro_model_name)
        return self._ro_model

    def _select_model(self, language: str) -> SentenceTransformer:
        language = (language or "en").lower()

        if language == "ro":
            return self._load_ro_model()

        return self._load_en_model()

    @staticmethod
    def _prepare_article_text(article_text: str, max_chars: int = 1500) -> str:
        if not article_text:
            return ""
        return article_text.strip()[:max_chars]

    def compute(self, headline: str, article_text: str, language: str = "en") -> Dict:
        headline = (headline or "").strip()
        article_text = self._prepare_article_text(article_text)

        if not headline or not article_text:
            return {
                "language": language,
                "model_used": None,
                "similarity_score": 0.0,
                "status": "missing_input"
            }

        model = self._select_model(language)

        headline_embedding = model.encode(headline, convert_to_tensor=True)
        article_embedding = model.encode(article_text, convert_to_tensor=True)

        similarity_score = util.cos_sim(headline_embedding, article_embedding).item()

        return {
            "language": language,
            "model_used": self.ro_model_name if language == "ro" else self.en_model_name,
            "similarity_score": round(float(similarity_score), 4),
            "status": "ok"
        }


_similarity_service = SemanticSimilarityService()


def compute_similarity(scraping_data: Dict, language: str = "en") -> Dict:
    cleaned = scraping_data.get("cleaned", {})
    headline = cleaned.get("title", "")
    article_text = cleaned.get("text", "")

    return _similarity_service.compute(
        headline=headline,
        article_text=article_text,
        language=language
    )