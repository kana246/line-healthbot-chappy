pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# 環境変数からキーを取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ここが LINE に送る Webhook 用エンドポイント！
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージ受信処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_message = f"こんにちは！あなたのメッセージは「{user_message}」ですね！"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

# 動作確認用
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"
from google.oauth2 import service_account
from googleapiclient.discovery import build

# スプレッドシートID（URLの一部）
SPREADSHEET_ID = 'あなたのスプレッドシートID'

# 認証スコープ
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# サービスアカウント認証
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=SCOPES
)

service = build('sheets', 'v4', credentials=credentials)

sheet = service.spreadsheets()

# 例：体重データをシートに追加する関数
def append_weight_data(user_id, date, weight):
    values = [[user_id, date, weight]]
    body = {
        'values': values
    }
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A:C',  # 書き込み範囲
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
    print(f"{result.get('updates').get('updatedRows')} rows appended.")

