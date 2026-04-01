import os
from typing import Dict

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-1.5-flash"

SYSTEM_PROMPT = """You are "The Gossip Police" - a witty, sharp-tongued media detective who exposes misleading and clickbait headlines with humor and flair.

Your job is to deliver a short verdict explanation (3-5 sentences) about whether a news headline is trustworthy, clickbait, or outright misleading.

Tone rules:
- Be entertaining and slightly sarcastic, but never mean-spirited.
- Use detective/investigative metaphors when they fit naturally.
- Always end with a punchy one-liner conclusion.
- Write in the same language as the article (Romanian or English).
- Never use markdown, bullet points, or headers - plain prose only.
- Keep it under 100 words."""


def _build_user_prompt(
    headline: str,
    verdict: str,
    confidence: float,
    flags: list,
    language: str,
) -> str:
    flags_text = " | ".join(flags) if flags else "No specific issues detected."
    confidence_pct = round(confidence * 100, 1)

    if language == "ro":
        return (
            f'Titlu analizat: "{headline}"\n'
            f"Verdict: {verdict}\n"
            f"Scor de incredere: {confidence_pct}%\n"
            f"Probleme detectate: {flags_text}\n\n"
            f"Scrie explicatia in romana."
        )

    return (
        f'Analyzed headline: "{headline}"\n'
        f"Verdict: {verdict}\n"
        f"Confidence score: {confidence_pct}%\n"
        f"Issues detected: {flags_text}\n\n"
        f"Write the explanation in English."
    )


def _verdict_to_emoji(verdict: str) -> str:
    mapping = {
        "reliable": "✅",
        "clickbait": "🎣",
        "misleading": "🚨",
        "unverifiable": "🔍",
    }
    return mapping.get(verdict, "❓")


def _fallback_explanation(verdict: str, confidence: float, language: str) -> str:
    pct = round(confidence * 100, 1)
    templates = {
        "en": {
            "reliable": (
                f"Case closed - this headline checks out. "
                f"Our analysis shows {pct}% confidence that the title reflects the actual content. "
                f"Rare, but it happens."
            ),
            "clickbait": (
                f"Caught red-handed. This headline is dangling bait with a {pct}% trustworthiness score. "
                f"The article exists - the drama in the title, less so."
            ),
            "misleading": (
                f"Something doesn't add up. With only {pct}% confidence in this headline, "
                f"the Gossip Police advise reading before sharing. "
                f"The title and the article are living in parallel universes."
            ),
            "unverifiable": (
                "The Gossip Police hit a dead end - not enough evidence to crack this case. "
                "Proceed with caution."
            ),
        },
        "ro": {
            "reliable": (
                f"Dosar inchis - titlul este corect. "
                f"Analiza noastra arata un scor de incredere de {pct}%. "
                f"Rar, dar se intampla."
            ),
            "clickbait": (
                f"Prins cu mata-n sac. Titlul acesta este clickbait cu un scor de incredere de {pct}%. "
                f"Articolul exista - dramatismul din titlu, mai putin."
            ),
            "misleading": (
                f"Ceva nu se leaga. Cu doar {pct}% incredere in acest titlu, "
                f"Politia Barfei recomanda sa citesti inainte sa distribui. "
                f"Titlul si articolul traiesc in universuri paralele."
            ),
            "unverifiable": (
                "Politia Barfei a dat de un impas - nu exista suficiente date pentru a rezolva cazul. "
                "Procedati cu precautie."
            ),
        },
    }
    lang_templates = templates.get(language, templates["en"])
    return lang_templates.get(verdict, lang_templates["unverifiable"])


def generate_explanation(
    headline: str,
    verdict_result: Dict,
    language: str = "en",
) -> Dict:
    verdict = verdict_result.get("verdict", "unverifiable")
    confidence = float(verdict_result.get("confidence", 0.0))
    flags = verdict_result.get("flags", [])
    emoji = _verdict_to_emoji(verdict)

    if not headline:
        return {
            "verdict": verdict,
            "confidence": confidence,
            "emoji": emoji,
            "explanation": (
                "Nu am gasit suficiente date pentru a analiza acest titlu."
                if language == "ro"
                else "Not enough data to analyze this headline."
            ),
            "status": "missing_input",
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        fallback = _fallback_explanation(verdict, confidence, language)
        return {
            "verdict": verdict,
            "confidence": confidence,
            "emoji": emoji,
            "explanation": fallback,
            "status": "missing_api_key",
        }

    user_prompt = _build_user_prompt(headline, verdict, confidence, flags, language)

    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
        )

        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=400,
                temperature=0.7,
            ),
        )

        explanation = getattr(response, "text", "") or ""
        explanation = explanation.strip()

        if not explanation:
            explanation = _fallback_explanation(verdict, confidence, language)
            status = "fallback"
        else:
            status = "ok"

        return {
            "verdict": verdict,
            "confidence": confidence,
            "emoji": emoji,
            "explanation": explanation,
            "status": status,
        }

    except Exception as exc:
        print(f"[explanation_generator] Gemini API error: {exc}")
        fallback = _fallback_explanation(verdict, confidence, language)
        return {
            "verdict": verdict,
            "confidence": confidence,
            "emoji": emoji,
            "explanation": fallback,
            "status": "fallback",
        }