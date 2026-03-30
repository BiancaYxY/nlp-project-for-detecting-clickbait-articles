from scraping.extractor import extract_article

url = "https://www.euronews.com/2026/03/30/trump-threatens-to-obliterate-irans-kharg-island-oil-hub-if-no-deal-reached-shortly"

article_data = extract_article(url)

print(article_data["cleaned"]["title"])
print(article_data["cleaned"]["text"])