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


# ベルクスページ取得（リトライ付き）
for i in range(3):
    try:
        response = requests.get(
            URL,
            headers=headers,
            timeout=60
        )
        break

    except requests.exceptions.RequestException:
        if i == 2:
            raise


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


    # PDF取得
    pdf_data = requests.get(
        pdf,
        headers=headers,
        timeout=60
    ).content


    with open(PDF_FILE, "wb") as f:
        f.write(pdf_data)


    # PDFを画像化（2ページ対応）
    images = convert_from_path(
        PDF_FILE,
        dpi=200
    )


    prompt = """
あなたはスーパーのチラシ分析担当です。

ベルクスの1週間チラシ画像を分析してください。

目的：
買い物する人が「これは買うべき」と思える
お買得商品TOP3を選ぶ。

判断基準：
・価格が安い
・普段使いやすい
・特売感が強い
・コスパが良い

出力形式：

🛒 ベルクス今週のお買得TOP3

🥇 商品名
価格：
おすすめ理由：

🥈 商品名
価格：
おすすめ理由：

🥉 商品名
価格：
おすすめ理由：

余計な説明は不要です。
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
