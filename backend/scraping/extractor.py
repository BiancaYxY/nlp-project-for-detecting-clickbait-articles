import time

import cloudscraper
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from scraping.cleaner import build_scraping_json


def _fetch_html(url: str) -> str:
    """Fetch raw HTML using cloudscraper (handles Cloudflare & 403s)."""
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    response = scraper.get(url, timeout=15)
    response.raise_for_status()
    return response.text


def extract_title_from_soup(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        return og_title.get("content").strip()

    twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
    if twitter_title and twitter_title.get("content"):
        return twitter_title.get("content").strip()

    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)

    return ""


def extract_with_newspaper(url: str, html: str):
    article = Article(url)
    article.download(input_html=html)
    article.parse()
    title = (article.title or "").strip()
    text = (article.text or "").strip()

    # fallback title from soup if newspaper missed it
    if not title:
        soup = BeautifulSoup(html, "html.parser")
        title = extract_title_from_soup(soup)

    return title, text


def extract_with_bs4(html: str, url: str):
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title_from_soup(soup)
    paragraphs = soup.find_all("p")
    content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    return title, content


def extract_with_selenium(url: str):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(3)

        headline = ""
        try:
            headline = driver.find_element(By.TAG_NAME, "h1").text
        except Exception:
            pass

        if not headline:
            try:
                headline = driver.execute_script("""
                    const og = document.querySelector('meta[property="og:title"]');
                    if (og && og.content) return og.content;
                    const tw = document.querySelector('meta[name="twitter:title"]');
                    if (tw && tw.content) return tw.content;
                    return document.title || "";
                """)
            except Exception:
                headline = ""

        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        content = " ".join(p.text for p in paragraphs if p.text.strip())

        return headline, content
    finally:
        driver.quit()


def is_valid_text(text: str) -> bool:
    return bool(text and len(text.strip()) > 200)


def extract_article(url: str) -> dict:
    html = None

    # Step 1: fetch HTML (cloudscraper handles 403/Cloudflare)
    try:
        html = _fetch_html(url)
    except Exception as e:
        print(f"cloudscraper fetch failed: {e}")

    if html:
        # Step 2a: newspaper4k parser (best for news articles)
        try:
            title, text = extract_with_newspaper(url, html)
            if is_valid_text(text):
                return build_scraping_json(url, title, text)
        except Exception as e:
            print(f"newspaper4k failed: {e}")

        # Step 2b: BeautifulSoup fallback on same fetched HTML
        try:
            title, text = extract_with_bs4(html, url)
            if is_valid_text(text):
                return build_scraping_json(url, title, text)
        except Exception as e:
            print(f"BeautifulSoup failed: {e}")

    # Step 3: Selenium (last resort — renders JS, real browser)
    try:
        title, text = extract_with_selenium(url)
        return build_scraping_json(url, title, text)
    except Exception as e:
        print(f"Selenium failed: {e}")

    return build_scraping_json(url, "", "")
