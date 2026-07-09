import os
import re
import requests
from bs4 import BeautifulSoup
from pdf2image import convert_from_path
import pytesseract
from linebot import LineBotApi
from linebot.models import TextSendMessage


URL = "https://sunbelx.com/store/27"
LAST_FILE = "last_flyer.txt"
PDF_FILE = "flyer.pdf"


headers = {
    "User-Agent": "Mozilla/5.0"
}


# LINE設定
LINE_USER_ID = os.environ["LINE_USER_ID"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

line_bot_api = LineBotApi(
    LINE_CHANNEL_ACCESS_TOKEN
)


def send_line(message):
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=message)
    )


# ベルクスページ取得
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


# PDF取得
pdf = None

for a in soup.find_all("a", href=True):

    href = a["href"]

    if ".pdf" in href.lower():

        if href.startswith("/"):
            href = "https://sunbelx.com" + href

        pdf = href
        break


if pdf is None:
    raise Exception("PDFが見つかりません")


print("最新PDF:", pdf)


# 更新チェック
last_pdf = ""

if os.path.exists(LAST_FILE):

    with open(LAST_FILE, "r") as f:
        last_pdf = f.read().strip()


if pdf == last_pdf:

    print("更新なし")


else:

    print("★★★★ 新しいチラシを検知しました！★★★★")


    # PDF保存
    pdf_data = requests.get(
        pdf,
        headers=headers,
        timeout=60
    ).content


    with open(PDF_FILE, "wb") as f:
        f.write(pdf_data)



    # PDF→画像
    images = convert_from_path(
        PDF_FILE,
        dpi=250
    )


    all_text = ""


    # OCR
    for image in images:

        text = pytesseract.image_to_string(
            image,
            lang="jpn"
        )

        all_text += "\n" + text



    # 商品候補抽出
    lines = [
        line.strip()
        for line in all_text.split("\n")
        if line.strip()
    ]


    products = []


    for i, line in enumerate(lines):

        # 円がある行を探す
        if "円" in line or "￥" in line:

            price_match = re.search(
                r"(\d{2,4})円",
                line
            )


            if price_match:

                price = int(
                    price_match.group(1)
                )


                # 価格付近の商品名候補
                before = ""

                if i > 0:
                    before = lines[i-1]


                if len(before) > 1:

                    products.append(
                        {
                            "name": before,
                            "price": price
                        }
                    )



    # 安い順でTOP3
    products = sorted(
        products,
        key=lambda x: x["price"]
    )


    top3 = products[:3]


    message = "🛒 ベルクス今週のお買得候補\n\n"


    if top3:

        rank = 1

        for item in top3:

            message += (
                f"🥇 商品候補{rank}\n"
                f"{item['name']}\n"
                f"{item['price']}円\n\n"
            )

            rank += 1

    else:

        message += "商品情報を抽出できませんでした"



    message += (
        "\n👇 チラシ全文\n"
        + pdf
    )


    send_line(message)



    with open(LAST_FILE, "w") as f:
        f.write(pdf)
