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


# 環境変数
LINE_USER_ID = os.environ["LINE_USER_ID"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]


# LINE
line_bot_api = LineBotApi(
    LINE_CHANNEL_ACCESS_TOKEN
)


# Gemini
client = genai.Client(
    api_key=GEMINI_API_KEY
)


def send_line(text):

    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=text)
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


for a in soup.find_all("a", href=True):

    href = a["href"]

    if ".pdf" in href.lower():

        if href.startswith("/"):

            href = "https://sunbelx.com" + href

        pdf = href
        break



if not pdf:

    raise Exception(
        "PDFが見つかりません"
    )


print("最新PDF:", pdf)



# 更新確認

old = ""

if os.path.exists(LAST_FILE):

    with open(
        LAST_FILE,
        "r"
    ) as f:

        old = f.read().strip()



if pdf == old:

    print("更新なし")

    exit()



print(
    "★★★★ 新しいチラシを検知しました！★★★★"
)



# PDF保存

data = requests.get(
    pdf,
    timeout=60
).content


with open(
    PDF_FILE,
    "wb"
) as f:

    f.write(data)



# PDF → 画像

images = convert_from_path(
    PDF_FILE,
    dpi=150
)



prompt = """

あなたはスーパーの節約アドバイザーです。

このベルクスのチラシから、
今週買う価値が高い商品を分析してください。


条件：

・単純な安さだけで判断しない
・普段の家庭料理で使いやすい商品を優先
・特売感が強い商品を選ぶ
・肉、魚、野菜、日用品など幅広く見る


出力形式：

🛒 ベルクス今週のお買得情報


🥩 肉類
商品名：
価格：
おすすめ理由：


🐟 魚類
商品名：
価格：
おすすめ理由：


🥬 野菜・果物
商品名：
価格：
おすすめ理由：


🥚 食品・その他
商品名：
価格：
おすすめ理由：


🔥 今週特におすすめTOP5

1.
2.
3.
4.
5.


読み取れない商品は無理に推測しないでください。
"""


contents = [prompt]


for image in images:

    contents.append(image)



result = client.models.generate_content(

    model="gemini-2.0-flash",

    contents=contents

)



message = result.text


message += (

    "\n\n👇 チラシ全文\n"

    + pdf

)



send_line(message)



# 保存

with open(
    LAST_FILE,
    "w"
) as f:

    f.write(pdf)



print("LINE送信完了")
