import os
import requests
from bs4 import BeautifulSoup
from linebot import LineBotApi
from linebot.models import TextSendMessage
from pdf2image import convert_from_path
import pytesseract


URL = "https://sunbelx.com/store/27"
LAST_FILE = "last_flyer.txt"
PDF_FILE = "flyer.pdf"


headers = {
    "User-Agent": "Mozilla/5.0"
}


# LINE設定
LINE_USER_ID = os.environ["LINE_USER_ID"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)


def send_line(message):
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=message)
    )


# ベルクスページ取得
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


    # PDFダウンロード
    pdf_data = requests.get(pdf).content

    with open(PDF_FILE, "wb") as f:
        f.write(pdf_data)


    # PDFを画像化
    images = convert_from_path(
        PDF_FILE,
        dpi=200
    )


    flyer_text = ""

    # OCR
    for image in images:

        text = pytesseract.image_to_string(
            image,
            lang="jpn"
        )

        flyer_text += text


    # 長すぎ防止
    flyer_text = flyer_text[:1500]


    message = (
        "🛒 ベルクス新着チラシ\n\n"
        "📌 チラシ内容\n\n"
        + flyer_text
        + "\n\n👇 PDF\n"
        + pdf
    )


    send_line(message)


    with open(LAST_FILE, "w") as f:
        f.write(pdf)
