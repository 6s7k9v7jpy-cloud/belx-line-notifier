import os
import requests
from bs4 import BeautifulSoup

URL = "https://sunbelx.com/store/27"
LAST_FILE = "last_flyer.txt"

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

if pdf is None:
    raise Exception("PDFが見つかりませんでした")

print("最新PDF:", pdf)

last_pdf = ""

if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r") as f:
        last_pdf = f.read().strip()

if pdf == last_pdf:
    print("更新なし")
else:
    print("★★★★ 新しいチラシを検知しました！★★★★")

    with open(LAST_FILE, "w") as f:
        f.write(pdf)
