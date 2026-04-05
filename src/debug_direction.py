import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GitLabChatbot/1.0)"}

url = "https://about.gitlab.com/direction/"
response = requests.get(url, headers=HEADERS, timeout=15)
soup = BeautifulSoup(response.text, "html.parser")

for tag in soup(["nav", "footer", "script", "style", "header", "aside"]):
    tag.decompose()

main = soup.find("main") or soup.body
tags = main.find_all(["h1","h2","h3","p","li"])
print(f"Total tags found: {len(tags)}")
print("\nFirst 5 tags:")
for t in tags[:5]:
    print(f"  [{t.name}] {t.get_text(strip=True)[:100]}")

print("\nPage length:", len(response.text))
print("\nFirst 500 chars of raw HTML:")
print(response.text[:500])