import os
from typing import Dict

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are "The Gossip Police" — a street-smart, wisecracking media detective straight outta the newsroom. You talk like a classic noir detective but keep it fun and informal. Never refuse a case. Always deliver the goods.

Your job: in 3-4 sentences, spill the tea on WHY the NLP system flagged this headline. Use the confidence score and signals as your evidence. Don't retell the story — crack the case on the headline itself. Use detective slang and informal expressions in the language you are writing in.

Keep it loose, informal, fun. End with one killer closing line. Write only in the language specified. No bullet points, no markdown. Max 100 words."""


def _call_llm(api_key: str, user_prompt: str, max_tokens: int = 400) -> str:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.9,
    )
    return (response.choices[0].message.content or "").strip()


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
            f'Titlu: "{headline}"\n'
            f"Verdict NLP: {verdict} (incredere {confidence_pct}%)\n"
            f"Semnale detectate: {flags_text}\n\n"
            f"Explica DE CE sistemul NLP a dat acest verdict acestui titlu. Nu rezuma articolul. "
            f"Vorbeste despre titlu si semnalele de mai sus. "
            f"Raspunde DOAR in romana, informal si amuzant, cu argou de detectiv romanesc — "
            f'expresii ca "nasul meu nu minte", "am mirosit-o de la distanta", "clasica manevra", '
            f'"cifrele vorbesc de la sine", "am mai vazut filmul asta". Incheie cu o concluzie scurta si acida.'
        )

    return (
        f'Headline: "{headline}"\n'
        f"NLP verdict: {verdict} (confidence {confidence_pct}%)\n"
        f"Signals detected: {flags_text}\n\n"
        f"Explain WHY the NLP system gave this verdict to this headline. Do NOT summarize the article. "
        f"Talk about the headline and the signals above. "
        f"Reply in ENGLISH ONLY, informal and fun, with noir detective slang — "
        f'phrases like "my nose started twitchin\'", "the numbers don\'t lie", "classic rookie move", '
        f'"smells fishy from a mile away", "we\'ve seen this trick before". End with a punchy one-liner.'
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

    api_key = os.getenv("GROQ_API_KEY")
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
        explanation = _call_llm(api_key, user_prompt, max_tokens=400)

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


def summarize_article(article_text: str, headline: str = "", language: str = "en") -> dict:
    if not article_text:
        return {
            "summary": (
                "Nu am gasit continut de rezumat." if language == "ro"
                else "No article content to summarize."
            ),
            "status": "missing_input",
        }

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "summary": (
                "Rezumatul nu este disponibil." if language == "ro"
                else "Summary unavailable."
            ),
            "status": "missing_api_key",
        }

    if language == "ro":
        user_prompt = (
            f'Titlu: "{headline}"\n\nArticol:\n{article_text[:4000]}\n\n'
            f"Rezuma acest articol in romana."
        )
    else:
        user_prompt = (
            f'Headline: "{headline}"\n\nArticle:\n{article_text[:4000]}\n\n'
            f"Summarize this article in English."
        )

    try:
        summary = _call_llm(api_key, user_prompt, max_tokens=300)
        if not summary:
            return {"summary": "No summary generated.", "status": "fallback"}
        return {"summary": summary, "status": "ok"}

    except Exception as exc:
        import traceback
        print(f"[explanation_generator] Gemini summarize error: {exc}")
        traceback.print_exc()
        return {
            "summary": (
                "Rezumatul nu este disponibil." if language == "ro"
                else "Summary unavailable."
            ),
            "status": "fallback",
        }
