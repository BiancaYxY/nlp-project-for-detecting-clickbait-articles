import json
import time
import requests
import trafilatura

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from scraping.cleaner import build_scraping_json


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def extract_trafilatura(url: str):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise Exception("Failed to download page with trafilatura")

    result = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        output_format="json"
    )

    if not result:
        raise Exception("Trafilatura extraction failed")

    data = json.loads(result)
    title = data.get("title", "") or ""
    text = data.get("text", "") or ""

    return title, text


def extract_with_bs4(url: str):
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    headline = ""
    h1 = soup.find("h1")
    if h1:
        headline = h1.get_text(strip=True)

    paragraphs = soup.find_all("p")
    content = " ".join([p.get_text(strip=True) for p in paragraphs])

    return headline, content


def extract_with_selenium(url: str):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(3)

        try:
            headline = driver.find_element(By.TAG_NAME, "h1").text
        except Exception:
            headline = ""

        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        content = " ".join([p.text for p in paragraphs])

        return headline, content
    finally:
        driver.quit()


def is_valid_text(text: str) -> bool:
    return bool(text and len(text.strip()) > 200)


def extract_article(url: str) -> dict:
    raw_title = ""
    raw_text = ""

    # Main extractor: Trafilatura
    try:
        raw_title, raw_text = extract_trafilatura(url)
        if is_valid_text(raw_text):
            return build_scraping_json(url, raw_title, raw_text)
    except Exception as e:
        print("Trafilatura failed:", e)

    # Fallback 1: BeautifulSoup
    try:
        raw_title, raw_text = extract_with_bs4(url)
        if is_valid_text(raw_text):
            return build_scraping_json(url, raw_title, raw_text)
    except Exception as e:
        print("BeautifulSoup failed:", e)

    # Fallback 2: Selenium
    try:
        raw_title, raw_text = extract_with_selenium(url)
        return build_scraping_json(url, raw_title, raw_text)
    except Exception as e:
        print("Selenium failed:", e)

    return build_scraping_json(url, "", "")