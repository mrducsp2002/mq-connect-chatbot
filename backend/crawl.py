from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from urllib.parse import urljoin, urlparse, urlunparse
import json
import random


def normalize_url(url):
    parsed = urlparse(url)
    # keep scheme + netloc + path only
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))


results = []

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=chrome_options)

base_url = "https://connect.mq.edu.au"
start_url = base_url + '/s/'

driver.get(base_url)
time.sleep(5)  # wait for JS

driver.add_cookie({
    'name': 'sid',
    'value': 'your_session_id_here',
    'domain': 'connect.mq.edu.au'
})

#BFS crawl 
max_depth = 3
visited = set()
to_visit = [(start_url, 0)]

while to_visit: 
    url, depth = to_visit.pop(0)
    if url in visited or depth > max_depth: 
        continue
    visited.add(url)
    
    print(f"\n--- Crawling: {url} (depth {depth}) ---")
    print(f"Visited {len(visited)} pages, {len(to_visit)} pages in queue")
    driver.get(url)
    time.sleep(50)  # wait for JS
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    footer = soup.find("div", class_="slds-p-vertical_x-large slds-grid slds-gutter slds-wrap")
    if footer:
        footer.decompose()  # delete from DOM

    if "/s/article/" in url:
        page_texts = [p.get_text(strip=True) for p in soup.find_all(
            ["p", "li", "summary"]) if not p.get_text(strip=True).startswith("https://")]
        print(page_texts[9:-15])

        results.append({
            "url": url,
            "text": "\n".join(page_texts[9:-15])
        })
    
    # Find links to other articles
    if depth < max_depth: 
        for a in soup.find_all("a", href=True):
            link = urljoin(base_url, a['href'])
            link = normalize_url(link)
            parsed = urlparse(link)
            if parsed.path.startswith("/s/") and base_url in link:
                if link not in visited:
                    to_visit.append((link, depth + 1))

with open("mq_connect_data_1.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)