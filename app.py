# 必要なパッケージは事前にインストールしてください
# pip install flask line-bot-sdk google-api-python-client google-auth-httplib2 google-auth-oauthlib

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# 環境変数からLINEキーを取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Googleスプレッドシート設定
SPREADSHEET_ID = '1mmdxzloT6rOmx7SiVT4X2PtmtcsBxivcHSoMUvjDCqc'  # ご自身のスプレッドシートIDに置き換えてください
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# 認証JSONファイルパス（プロジェクト直下に置くのがおすすめ）
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=SCOPES
)

service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

def append_weight_data(user_id, date, weight):
    values = [[user_id, date, weight]]
    body = {'values': values}
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A:C',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
    print(f"{result.get('updates').get('updatedRows')} rows appended.")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id

    if text.startswith("体重"):
        # 例: 体重 2025-07-12 65.5
        parts = text.split()
        if len(parts) == 3:
            _, date_str, weight_str = parts
            try:
                weight = float(weight_str)
                # 日付形式チェック
                datetime.strptime(date_str, "%Y-%m-%d")
                append_weight_data(user_id, date_str, weight)
                reply = f"{date_str} の体重 {weight}kg を記録しました！"
            except Exception:
                reply = "日付か体重の形式が正しくありません。正しい形式：体重 YYYY-MM-DD 数字"
        else:
            reply = "フォーマットが違います。正しい形式：体重 YYYY-MM-DD 数字"
    elif text.replace('.', '', 1).isdigit():
        # 数字のみなら現在日時で登録
        weight = float(text)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        append_weight_data(user_id, date_str, weight)
        reply = f"体重 {weight}kg を記録しました！（日時：{date_str}）"
    else:
        reply = "こんにちは！体重を記録するには「体重 YYYY-MM-DD 数字」か「数字」だけを送ってください。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
