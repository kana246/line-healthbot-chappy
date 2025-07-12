# 必要なパッケージを事前にインストールしてください
# pip install flask line-bot-sdk google-api-python-client google-auth-httplib2 google-auth-oauthlib

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# 環境変数からLINEキーを取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Googleスプレッドシート設定
SPREADSHEET_ID = '1mmdxzloT6rOmx7SiVT4X2PtmtcsBxivcHSoMUvjDCqc'  # ここにあなたのスプレッドシートID
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# サービスアカウント認証ファイルはプロジェクト直下などに配置してパスを指定
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',  # 認証JSONファイルパス
    scopes=SCOPES
)

service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

# 体重データをスプレッドシートに追加する関数
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

# LINEのWebhookエンドポイント
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

# メッセージイベントハンドラー
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id

    # 体重登録コマンド例：「体重 2025-07-12 65.5」
    if text.startswith("体重"):
        try:
            parts = text.split()
            if len(parts) != 3:
                raise ValueError("フォーマットエラー")
            _, date, weight_str = parts
            weight = float(weight_str)
            append_weight_data(user_id, date, weight)
            reply = f"{date} の体重 {weight}kg を記録しました！"
        except Exception:
            reply = "記録に失敗しました。正しいフォーマットは「体重 YYYY-MM-DD 数字」です。"
    else:
        reply = "こんにちは！体重を記録するには「体重 YYYY-MM-DD 数字」の形式で送信してください。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# 動作確認用ルート
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

if __name__ == "__main__":
    # Renderなどクラウド環境でPORT環境変数使う場合もある
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
