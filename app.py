import requests
from bs4 import BeautifulSoup

URL = "https://sunbelx.com/store/27"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

pdf = None

for a in soup.find_all("a", href=True):
    href = a["href"]
    if ".pdf" in href.lower():
        if href.startswith("/"):
            href = "https://sunbelx.com" + href
        pdf = href
        break

if pdf:
    print("最新PDF:", pdf)
else:
    print("PDFが見つかりません")
