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
    "User-Agent": "Mozilla/5.0"
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

response = requests.get(
    URL,
    headers=headers,
    timeout=60
)

response.raise_for_status()


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
        "PDFが見つかりません"
    )



print(
    "最新PDF:",
    pdf
)



# 更新チェック

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



# PDF保存

pdf_data = requests.get(
    pdf,
    timeout=60
).content


with open(
    PDF_FILE,
    "wb"
) as f:

    f.write(pdf_data)



# PDFを画像化

images = convert_from_path(
    PDF_FILE,
    dpi=120
)



# まず1ページだけ解析

image = images[0]



prompt = """

あなたはスーパーの節約アドバイザーです。

このベルクスのチラシ画像から、
おすすめの商品を選んでください。

条件：
・安いだけではなくお得感を見る
・家庭で使いやすい商品を優先
・肉、魚、野菜、食品を中心に選ぶ

出力形式：

🛒 ベルクス今週のお買得

🥇 商品名
価格：
おすすめ理由：

🥈 商品名
価格：
おすすめ理由：

🥉 商品名
価格：
おすすめ理由：

最後に
「今週買うなら」
を3〜5個まとめてください。
"""



result = client.models.generate_content(

    model="gemini-2.0-flash",

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



send_line(
    message
)



with open(
    LAST_FILE,
    "w"
) as f:

    f.write(pdf)



print(
    "LINE送信完了"
)
