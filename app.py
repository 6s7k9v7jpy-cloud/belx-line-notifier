import os
import requests
from bs4 import BeautifulSoup
from linebot import LineBotApi
from linebot.models import TextSendMessage


URL = "https://sunbelx.com/store/27"
LAST_FILE = "last_flyer.txt"


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


# 前回PDF確認
last_pdf = ""

if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r") as f:
        last_pdf = f.read().strip()


# 更新なし
if pdf == last_pdf:
    print("更新なし")


# 新しいチラシ発見
else:
    print("★★★★ 新しいチラシを検知しました！★★★★")


    send_line(
        "🛒 ベルクスの新しいチラシが公開されました！\n\n"
        + pdf
    )


    with open(LAST_FILE, "w") as f:
        f.write(pdf)
