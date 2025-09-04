
# DB
USERS = "users"                     # ユーザー情報
RECIPIENTS = "recipients"           # 送信先情報
SENT_EMAILS = "sent_emails"         # 送信履歴情報
EMAIL_DELIVERED = "email_delivered" # メール送信先
CLICK_ALERT = "click_alert"         # 通知先

# URL
URL_DEV = "http://127.0.0.1:5000/url_clicked"               # 訓練通知画面URL-開発環境用
URL = "https://my-flask-app-ixgu.onrender.com/url_clicked"  # 訓練通知画面URL

# 認証が必要なパス
AUTHORIZED_PATH = {'/send_email', '/recipient_master', '/mail_master', '/user_master'}

# エラーメッセージ
UTIL_MESSAGE = "\n しばらく時間をおいてから、お試しください。"
MESSAGE_400 = "400 - 入力に誤りがあります。もう一度確認してください。"
MESSAGE_401 = "401 - ログインセッションが期限切れです。ログインしてください。"
MESSAGE_404 = "404 - ページが見つかりません。URLをご確認ください。"
MESSAGE_500 = "500 - サーバーで問題が発生しました。しばらくしてから再度お試しください。"
MESSAGE_503 = "503 - メンテナンス中またはサーバーが混み合っています。"