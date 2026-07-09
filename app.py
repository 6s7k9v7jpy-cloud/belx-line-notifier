import os
import requests
from bs4 import BeautifulSoup
from pdf2image import convert_from_path

from google import genai

from linebot import LineBotApi
from linebot.models import TextSendMessage


URL = "https://sunbelx.com/store/27"
LAST_FILE = "last_flyer.txt"
PDF_FILE = "flyer.pdf"


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9"
}


LINE_USER_ID = os.environ["LINE_USER_ID"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


line_bot_api = LineBotApi(
    LINE_CHANNEL_ACCESS_TOKEN
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def send_line(message):

    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(
            text=message
        )
    )


# ベルクスページ取得

try:

    response = requests.get(
        URL,
        headers=headers,
        timeout=(10,120)
    )

    response.raise_for_status()

except Exception as e:

    raise Exception(
        f"ベルクスページ取得失敗: {e}"
    )


soup = BeautifulSoup(
    response.text,
    "html.parser"
)


pdf = None


for a in soup.find_all(
    "a",
    href=True
):

    href = a["href"]

    if ".pdf" in href.lower():

        if href.startswith("/"):

            href = "https://sunbelx.com" + href

        pdf = href
        break


if pdf is None:

    raise Exception(
        "PDFが見つかりませんでした"
    )


print(
    "最新PDF:",
    pdf
)


# 更新確認

old_pdf = ""


if os.path.exists(LAST_FILE):

    with open(
        LAST_FILE,
        "r"
    ) as f:

        old_pdf = f.read().strip()



if pdf == old_pdf:

    print(
        "更新なし"
    )

    exit()



print(
    "★★★★ 新しいチラシを検知しました！★★★★"
)


# PDFダウンロード

pdf_response = requests.get(
    pdf,
    headers=headers,
    timeout=(10,120)
)

pdf_response.raise_for_status()


with open(
    PDF_FILE,
    "wb"
) as f:

    f.write(
        pdf_response.content
    )


# PDFを画像化

images = convert_from_path(
    PDF_FILE,
    dpi=120
)


# 1ページ目のみ解析（無料枠対策）

image = images[0]

prompt = """

あなたはスーパーの節約アドバイザーです。

ベルクスのチラシ画像を分析してください。

目的：
今週スーパーで買う価値が高い商品を紹介する。

選ぶ基準：
・価格が安い
・普段使いやすい
・特売感が強い
・家計節約になる

出力：

🛒 ベルクス今週のお買得情報


🥇 商品名
💰 価格
⭐ おすすめ理由


🥈 商品名
💰 価格
⭐ おすすめ理由


🥉 商品名
💰 価格
⭐ おすすめ理由


🔥 今週買うならおすすめ

・商品名
・商品名
・商品名


※読み取れない商品は推測しない
※文字化けした場合は無理に出力しない
"""


# Gemini解析

result = client.models.generate_content(

    model="gemini-2.0-flash-lite",

    contents=[
        prompt,
        image
    ]

)


message = result.text



message += (

    "\n\n👇 チラシ全文\n"

    + pdf

)



# LINE送信

send_line(
    message
)



# 最新PDF保存

with open(
    LAST_FILE,
    "w"
) as f:

    f.write(pdf)



print(
    "LINE送信完了"
)
