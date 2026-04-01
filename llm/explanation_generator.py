import json
import os
from typing import Dict
import google.generativeai as genai

MODEL_NAME = "gemini-1.5-flash"

SYSTEM_PROMPT = """You are "The Gossip Police" - a witty, sharp-tongued media detective who exposes misleading and clickbait headlines with humor and flair.

Your job is to deliver a short verdict explanation (3-5 sentences) about whether a news headline is trustworthy, clickbait, or outright misleading.

Tone rules:
- Be entertaining and slightly sarcastic, but never mean-spirited.
- Use detective/investigative metaphors when they fit naturally.
- Always end with a punchy one-liner conclusion.
- Write in the same language as the article (Romanian or English).
- Never use markdown, bullet points, or headers — plain prose only.
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
            f"Titlu analizat: \"{headline}\"\n"
            f"Verdict: {verdict}\n"
            f"Scor de încredere: {confidence_pct}%\n"
            f"Probleme detectate: {flags_text}\n\n"
            f"Scrie explicația în română."
        )

    return (
        f"Analyzed headline: \"{headline}\"\n"
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
                "Nu am găsit suficiente date pentru a analiza acest titlu."
                if language == "ro"
                else "Not enough data to analyze this headline."
            ),
            "status": "missing_input",
        }

    user_prompt = _build_user_prompt(headline, verdict, confidence, flags, language)

    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT
        )

        response = model.generate_content(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=400,
                temperature=0.7,
            )
        )

        explanation = response.text.strip()

        return {
            "verdict": verdict,
            "confidence": confidence,
            "emoji": emoji,
            "explanation": explanation,
            "status": "ok",
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

def _fallback_explanation(verdict: str, confidence: float, language: str) -> str:
    pct = round(confidence * 100, 1)
    templates = {
        "en": {
            "reliable": (
                f"Case closed — this headline checks out. "
                f"Our analysis shows {pct}% confidence that the title reflects the actual content. "
                f"Rare, but it happens."
            ),
            "clickbait": (
                f"Caught red-handed. This headline is dangling bait with a {pct}% trustworthiness score. "
                f"The article exists — the drama in the title, less so."
            ),
            "misleading": (
                f"Something doesn't add up. With only {pct}% confidence in this headline, "
                f"the Gossip Police advise reading before sharing. "
                f"The title and the article are living in parallel universes."
            ),
            "unverifiable": (
                "The Gossip Police hit a dead end — not enough evidence to crack this case. "
                "Proceed with caution."
            ),
        },
        "ro": {
            "reliable": (
                f"Dosar închis — titlul este corect. "
                f"Analiza noastră arată un scor de încredere de {pct}%. "
                f"Rar, dar se întâmplă."
            ),
            "clickbait": (
                f"Prins cu mâța-n sac. Titlul acesta este clickbait cu un scor de încredere de {pct}%. "
                f"Articolul există — dramatismul din titlu, mai puțin."
            ),
            "misleading": (
                f"Ceva nu se leagă. Cu doar {pct}% încredere în acest titlu, "
                f"Poliția Bârfei recomandă să citești înainte să distribui. "
                f"Titlul și articolul trăiesc în universuri paralele."
            ),
            "unverifiable": (
                "Poliția Bârfei a dat de un impas — nu există suficiente date pentru a rezolva cazul. "
                "Procedați cu precauție."
            ),
        },
    }
    lang_templates = templates.get(language, templates["en"])
    return lang_templates.get(verdict, lang_templates["unverifiable"])