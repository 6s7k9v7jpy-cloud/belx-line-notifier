import os
import requests
from bs4 import BeautifulSoup
from pdf2image import convert_from_path
from linebot import LineBotApi
from linebot.models import TextSendMessage
import google.generativeai as genai


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


# Gemini設定
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

genai.configure(
    api_key=GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)


# ベルクスページ取得
response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


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


# 前回チェック
last_pdf = ""

if os.path.exists(LAST_FILE):

    with open(LAST_FILE, "r") as f:
        last_pdf = f.read().strip()


if pdf == last_pdf:

    print("更新なし")


else:

    print("★★★★ 新しいチラシを検知しました！★★★★")


    # PDF保存
    pdf_data = requests.get(pdf).content

    with open(PDF_FILE, "wb") as f:
        f.write(pdf_data)


    # PDF→画像
    images = convert_from_path(
        PDF_FILE,
        dpi=200
    )


    # Geminiへ送信
    prompt = """
あなたはスーパーのチラシ分析担当です。

このベルクス1週間チラシから、
本当にお得な商品TOP3を選んでください。

基準：
・価格が安い
・普段使いやすい
・特売感が強い

以下の形式で回答してください。

🛒 ベルクス今週のお買得TOP3

🥇 商品名
価格：
理由：

🥈 商品名
価格：
理由：

🥉 商品名
価格：
理由：

余計な説明はいりません。
"""


    contents = [prompt]

    for image in images:
        contents.append(image)


    result = model.generate_content(
        contents
    )


    analysis = result.text


    message = (
        analysis
        + "\n\n👇 チラシ全文\n"
        + pdf
    )


    send_line(message)


    with open(LAST_FILE, "w") as f:
        f.write(pdf)
