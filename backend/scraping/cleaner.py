import re
from typing import Dict, List


MIN_PARAGRAPH_WORDS = 5

NOISE_PATTERNS = [
    # English
    r"cookie[s]?",
    r"accept( all)? cookies?",
    r"subscribe",
    r"sign up",
    r"log in",
    r"advertisement",
    r"\bad\b",
    r"read more",
    r"related article[s]?",
    r"related stor(y|ies)",
    r"follow us",
    r"share (this )?article",
    r"all rights reserved",
    r"newsletter",
    r"click here",
    r"privacy policy",
    r"terms of service",

    # Romanian
    r"cookie-uri",
    r"accept(ă|a)? cookie(-uri)?",
    r"abon(ează|are|eaza-te)",
    r"autentificare",
    r"publicitate",
    r"citește mai mult",
    r"citeste mai mult",
    r"articole similare",
    r"articole recomandate",
    r"urmărește-ne",
    r"urmareste-ne",
    r"distribuie",
    r"toate drepturile rezervate",
    r"politica de confidențialitate",
    r"politica de confidentialitate",
    r"termeni și condiții",
    r"termeni si conditii",
    r"vezi mai mult",
    r"trimite",
    r"continuă",
    r"continua",
]


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_urls(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"https?://\S+|www\.\S+", "", text)


def clean_punctuation(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\!{2,}", "!", text)
    text = re.sub(r"\?{2,}", "?", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])([^\s])", r"\1 \2", text)

    return text.strip()


def split_into_paragraphs(text: str) -> List[str]:
    if not text:
        return []

    paragraphs = re.split(r"\n{2,}|\n", text)
    return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]


def is_noise_line(line: str) -> bool:
    if not line:
        return True

    normalized_line = line.strip().lower()

    if not normalized_line:
        return True

    if any(re.search(pattern, normalized_line) for pattern in NOISE_PATTERNS):
        return True

    short_noise_candidates = {
        "share", "follow", "login", "subscribe",
        "distribuie", "urmărește", "urmareste",
        "citește", "citeste", "trimite", "video", "live"
    }

    if len(normalized_line.split()) <= 2 and normalized_line in short_noise_candidates:
        return True

    return False


def remove_noise_lines(text: str) -> str:
    if not text:
        return ""

    cleaned_lines = []

    for line in text.splitlines():
        stripped = line.strip()
        if is_noise_line(stripped):
            continue
        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines)


def deduplicate_paragraphs(paragraphs: List[str]) -> List[str]:
    unique_paragraphs = []
    seen = set()

    for paragraph in paragraphs:
        normalized = re.sub(r"\s+", " ", paragraph.lower()).strip()
        if normalized not in seen:
            seen.add(normalized)
            unique_paragraphs.append(paragraph)

    return unique_paragraphs


def filter_short_paragraphs(paragraphs: List[str], min_words: int = MIN_PARAGRAPH_WORDS) -> List[str]:
    return [
        paragraph
        for paragraph in paragraphs
        if len(paragraph.split()) >= min_words
    ]


def clean_title(title: str) -> str:
    if not title:
        return ""

    title = remove_urls(title)
    title = normalize_whitespace(title)

    title = re.sub(r"\s+\|\s+.*$", "", title)
    title = re.sub(r"\s+-\s+.*$", "", title)

    title = clean_punctuation(title)
    return title.strip()


def clean_article_text(text: str, min_paragraph_words: int = MIN_PARAGRAPH_WORDS) -> str:
    if not text:
        return ""

    text = remove_urls(text)
    text = normalize_whitespace(text)
    text = remove_noise_lines(text)

    paragraphs = split_into_paragraphs(text)
    paragraphs = deduplicate_paragraphs(paragraphs)
    paragraphs = filter_short_paragraphs(paragraphs, min_words=min_paragraph_words)

    cleaned_text = "\n\n".join(paragraphs)
    cleaned_text = normalize_whitespace(cleaned_text)
    cleaned_text = clean_punctuation(cleaned_text)

    return cleaned_text


def build_scraping_json(url: str, raw_title: str, raw_text: str) -> Dict:
    cleaned_title = clean_title(raw_title)
    cleaned_text = clean_article_text(raw_text)

    return {
        "url": url,
        "raw": {
            "title": raw_title or "",
            "text": raw_text or ""
        },
        "cleaned": {
            "title": cleaned_title,
            "text": cleaned_text
        }
    }