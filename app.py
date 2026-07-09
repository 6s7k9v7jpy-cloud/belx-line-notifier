import os
import requests
from bs4 import BeautifulSoup

from linebot import LineBotApi
from linebot.models import TextSendMessage


URL = "https://sunbelx.com/store/27"
LAST_FILE = "last_flyer.txt"


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9"
}


LINE_USER_ID = os.environ["LINE_USER_ID"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]


line_bot_api = LineBotApi(
    LINE_CHANNEL_ACCESS_TOKEN
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
        timeout=(10, 120)
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


# 前回PDF確認

old_pdf = ""


if os.path.exists(LAST_FILE):

    with open(
        LAST_FILE,
        "r",
        encoding="utf-8"
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


# LINE通知

message = f"""
★★★★ 新しいベルクスチラシを検知しました！★★★★

ベルクスのチラシが更新されました。

👇 最新チラシはこちら

{pdf}

買い物前にチェックしてください🛒
"""


send_line(
    message
)


# 最新PDF保存

with open(
    LAST_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(pdf)



print(
    "LINE送信完了"
)
