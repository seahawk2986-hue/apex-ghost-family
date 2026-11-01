import requests
from bs4 import BeautifulSoup

def scrape_website(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"scrape failed for {url}: {e}") from e
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

if __name__ == '__main__':
    url = 'https://example.com'
    data = scrape_website(url)
    print(data.prettify())