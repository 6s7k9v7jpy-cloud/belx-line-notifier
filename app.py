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



# 更新確認
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



    # PDF画像化
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



    lines = [
        x.strip()
        for x in all_text.split("\n")
        if x.strip()
    ]



    products = []


    # 商品候補抽出
    for i, line in enumerate(lines):


        price_match = re.search(
            r"(\d{2,4})円",
            line
        )


        if price_match:


            price = int(
                price_match.group(1)
            )


            # 安すぎる誤認識除外
            if price < 50:
                continue


            candidates = []


            # 前3行を見る
            for n in range(1,4):

                if i-n >= 0:

                    text = lines[i-n]


                    # ノイズ除外
                    if (
                        len(text) >= 3
                        and not re.search(
                            r"[|@_]",
                            text
                        )
                    ):
                        candidates.append(text)



            if candidates:

                name = max(
                    candidates,
                    key=len
                )


                # 長すぎるOCR崩れ除外
                if len(name) < 40:

                    products.append(
                        {
                            "name": name,
                            "price": price
                        }
                    )



    # 重複削除
    unique = []

    seen = set()


    for p in products:

        key = (
            p["name"],
            p["price"]
        )

        if key not in seen:

            seen.add(key)
            unique.append(p)



    # 安い順TOP3
    top3 = sorted(
        unique,
        key=lambda x:x["price"]
    )[:3]



    message = (
        "🛒 ベルクス今週のお買得候補\n\n"
    )


    if top3:

        for index, item in enumerate(top3):

            rank = [
                "🥇",
                "🥈",
                "🥉"
            ][index]


            message += (
                f"{rank} {item['name']}\n"
                f"💰 {item['price']}円\n\n"
            )


    else:

        message += (
            "商品を抽出できませんでした"
        )



    message += (
        "👇 チラシ全文\n"
        + pdf
    )


    send_line(message)



    # 保存
    with open(LAST_FILE, "w") as f:
        f.write(pdf)
