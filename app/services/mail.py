import smtplib
import poplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr,parsedate_to_datetime
from email.parser import Parser
import os
import re
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.services.utils import get_time_now
from app.config import Config
from app import constants

class MailClient:
    # URL短縮API
    tynyurl_api = Config.TINYURL_API
    # クラス内のメソッドは 必ず第一引数に self を書く
    # インスタンス
    def __init__(self):
        # SMTP設定
        self.smtp_host = Config.MAIL_SERVER
        self.smtp_port = Config.MAIL_PORT
        self.smtp_user = Config.MAIL_USERNAME
        self.smtp_pass = Config.MAIL_PASSWORD
        self.envelope_from = self.smtp_user
        self.from_name = Config.MAIL_FROM_NAME
        self.use_tls = Config.MAIL_USE_TLS
        # POP3設定
        self.pop_host = Config.MAIL_POP_SERVER
        self.pop_port = Config.MAIL_POP_PORT

    # SMTPサーバー接続
    def connect(self):
        server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
        if self.use_tls:
            server.starttls()
        server.login(self.smtp_user, self.smtp_pass)
        return server
    
    # POP3サーバー接続
    def connect_pop3(self):
        server = poplib.POP3_SSL(self.pop_host, self.pop_port, timeout=10)
        server.user(self.smtp_user)  # 同じユーザーを使う
        server.pass_(self.smtp_pass)
        return server


    # URL変換処理
    def convert_links_to_html(self, body_text, target_url):
        # 局所的な利用のためネストされたローカル関数
        # URL短縮処理（TinyURL）
        def shorten_url(original_url):
            try:
                response = requests.get(self.tynyurl_api, params={'url': original_url})
                if response.status_code == 200:
                    return response.text
                else:
                    return original_url
            except Exception as e:
                print("URL短縮エラー:", e)
                return original_url

        # match: 正規表現にマッチしたオブジェクト（置換対象の部分）
        def _replace_link(match):
            display_text = match.group(1).strip()

            # 開発モード時はAPIを使わない
            if Config.FLASK_DEBUG == "1":
                short_url = target_url
            else:
                # URLを短縮する
                short_url = shorten_url(target_url)

            if display_text:
                return f'<a href="{short_url}">{display_text}</a>'     # 表示テキストにある
            else:
                return f'<a href="{short_url}">{short_url}</a>'       # 表示テキストが空
        
        return re.sub(r"\[\[LINK:(.*?)\]\]", _replace_link, body_text)


    # 訓練メール送信処理
    def send_training_mail(self, from_name, from_email, to_email, subject, body_text, recipient_id, mail_id):
        # 訓練通知画面のURL
        if Config.FLASK_DEBUG == "1":
            url = constants.URL_DEV
        else:
            url = constants.URL
        
        target_url = f"{ url }?mail_id={ mail_id }&recipient_id={ recipient_id }"

        # [[LINK:*〇〇〇]]の部分を<a>リンクに置換
        html_body = self.convert_links_to_html(body_text, target_url)
    
        # 改行を <br> にして HTML にラップ
        html_body = "<html><body>" + html_body.replace("\n", "<br>") + "</body></html>"

        # メール作成
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((str(Header(from_name, 'utf-8')), from_email))
        msg["To"] = to_email

        msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with self.connect() as server:
            server.sendmail(self.envelope_from, [to_email], msg.as_string())
    
    # パスワード再発行・URLクリック通知メール送信処理
    # To・件名・メッセージを受け取る
    def send_system_mail(self, to_email, subject, body_text):
        # メール作成
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr((str(Header(self.from_name, 'utf-8')), self.envelope_from))
        msg["To"] = to_email

        msg.attach(MIMEText(body_text, 'plain'))

        with self.connect() as server:
            server.sendmail(self.envelope_from, [to_email], msg.as_string())


    # バウンスメールをチェックし、届かなかったアドレスを返す
    def check_recent_bounces(self, recent_recipients: list[str], window_minutes: int = 10, max_messages: int = 20):
        bounced_emails = []
        # POP3接続
        server = self.connect_pop3()

        num_messages = len(server.list()[1])    
        # get_time_now() は ISO8601 文字列を返すので、datetimeに変換してUTCのaware(タイムゾーン情報持ち)にする
        now = datetime.fromisoformat(get_time_now())
        window = timedelta(minutes=window_minutes)

        # 直近のメールを取得
        for i in range(num_messages, max(0, num_messages - max_messages), -1):    # 最新20件まで
            raw_email = b"\n".join(server.retr(i)[1])
            parsed_email = email.message_from_bytes(raw_email)

            # メールの日付確認
            date_str = parsed_email.get("Date", "")
            try:
                msg_date = parsedate_to_datetime(date_str)
            except Exception:
                continue
        
            # msg_dateがnaive(タイムゾーン情報無し)の場合はJSTとして扱い、UTCに変換する
            if msg_date.tzinfo is None:
                msg_date = msg_date.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
                msg_date = msg_date.astimezone(timezone.utc)
            else:
                # すでにタイムゾーン付きならUTCに変換
                msg_date = msg_date.astimezone(timezone.utc)

            print(f"[DEBUG] now: {now} (tz: {now.tzinfo}), msg_date: {msg_date} (tz: {msg_date.tzinfo})")

            # 「タイムゾーン情報がない日時」と「タイムゾーン情報がある日時」は計算不可
            if abs(now - msg_date).total_seconds() > window.total_seconds():
                continue

            # メールの件名・送信者確認
            subject = parsed_email.get("Subject", "")
            from_email = parsed_email.get("From", "")

            # バウンスメール判定（件名・送信者）
            if "Mail Delivery Subsystem" in from_email or "Undelivered Mail Returned to Sender" in subject:
                # メール本文を抽出
                for part in parsed_email.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")

                        # メールアドレスの抽出
                        failed_addresses = re.findall(r'[\w\.-]+@[\w\.-]+', body)
                        for addr in failed_addresses:
                            if addr in recent_recipients:
                                bounced_emails.append(addr)

        # SMTPはwith構文で自動的にquit()されるが、
        # POP3_SSLはcontext manager非対応のため、明示的にquit()が必要
        server.quit()

        # 重複排除(set)して返す
        return list(set(bounced_emails))