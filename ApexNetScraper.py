# FILE: ApexNetScraper.py
import os
import time
import json
import requests
from bs4 import BeautifulSoup
import logging

ROOT = r"C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
LOGS = os.path.join(ROOT, "Logs")

class ApexNetScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; x64) AppleWebKit/537.36"}
        self.setup_logging()

    def setup_logging(self):
        os.makedirs(LOGS, exist_ok=True)
        self.logger = logging.getLogger("ApexNetScraper")
        handler = logging.FileHandler(os.path.join(LOGS, "system.log"))
        formatter = logging.Formatter('[%(asctime)s] [NET_SCRAPER] %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, msg, level="info"):
        if level == "info":
            self.logger.info(msg)
        elif level == "warning":
            self.logger.warning(msg)
        elif level == "error":
            self.logger.error(msg)

    def search_and_extract(self, query, retries=3, delay=5):
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        self.log(f"Searching raw HTML endpoint for: {query}")
        for attempt in range(retries):
            try:
                r = requests.get(url, headers=self.headers, timeout=15)
                r.raise_for_status()
                soup = self.parse_html(r.text)
                results = self.extract_links(soup)
                return results
            except requests.RequestException as e:
                self.log(f"Error fetching data, retrying in {delay} seconds: {e}", level="warning")
                time.sleep(delay)
        self.log(f"Failed to fetch data after {retries} attempts", level="error")
        return None

    def parse_html(self, html):
        return BeautifulSoup(html, 'html.parser')

    def extract_links(self, soup):
        return [a['href'] for a in soup.find_all('a', href=True)]

