from flask import Blueprint, render_template, request, session, redirect, url_for
from app.services.db import (
    get_mail_history,
    get_recipients,
    get_recipient_id_by_email,
    insert_sent_emails,
    insert_email_delivered,
    update_success,
    update_email_delivered_by_email,
    send_email_transaction,
    send_email_success
)
from app.services.mail import MailClient
from app.services.log import log_error
from app import constants
import os
import re

bp = Blueprint("email", __name__)

# メール送信画面
@bp.route("/send_email", methods=["GET", "POST"])
def send_email():
    user_id = session["user_id"]
    # .popで取り出すと同時にsession情報を削除している
    message = session.pop("message", None)

    try:
        recipients = get_recipients()       # 送信先一覧取得
        sent_emails = get_mail_history()    # 送信履歴取得
    except Exception as e:
        session["message"] = f"初期値取得失敗: {str(e)}"
        log_error("送信先・送信履歴取得失敗", e)
        return redirect(url_for("email.send_email"))

    if request.method == "POST":
        print("POST処理開始")

        from_name = request.form["header_from_name"]
        from_email = request.form["header_from_email"]
        from_address_display = f"{from_name} <{from_email}>"
        print(from_address_display)
        subject = request.form["subject"]
        body_text = request.form["body_text"] or ""
        selected_emails = request.form.getlist("selected_rows")
        print("今回の送信先メール:" + ",".join(selected_emails))

        # プロシージャ利用
        try:
            mail_id = send_email_transaction(user_id, from_address_display, subject, body_text, selected_emails)

        except Exception as e:
            session["message"] = f"訓練メールの送信に失敗しました。" + constants.UTIL_MESSAGE
            return redirect(url_for("email.send_email"))

        send_succeed = []
        send_failed = []

        # ここから実際にメール送信
        for to_email in selected_emails:
            try:
                recipient_id = get_recipient_id_by_email(to_email)

                mail_client = MailClient()
                mail_client.send_training_mail(
                    from_name=from_name,
                    from_email=from_email,
                    to_email=to_email,
                    subject=subject,
                    body_text=body_text,
                    recipient_id = recipient_id,
                    mail_id = mail_id
                )
                send_succeed.append(to_email)
            except Exception as e:
                # 失敗した人はリストに入れて続行
                log_error("訓練メール送信失敗", e)
                send_failed.append(to_email)

        try:
            # メール送信後、バウンスメールを確認
            mail_client = MailClient()
            bounced = mail_client.check_recent_bounces(
                recent_recipients=send_succeed,
                window_minutes=10,
                max_messages=len(selected_emails)
            )

            # バウンスされたアドレスを failed に移す
            for email_addr in bounced:
                if email_addr in send_succeed:
                    send_succeed.remove(email_addr)
                    send_failed.append(email_addr)
        except Exception as e:
            session["message"] = f"送信結果の取得に失敗しました。hetemailにログインし、送信結果を確認してください。"
            log_error("送信結果の取得に失敗", e)
            return redirect(url_for("email.send_email"))

        print(f"送信成功 : {send_succeed}")
        print(f"送信失敗 : {send_failed}")

        # 更新処理(一部送信失敗)
        # 失敗したメンバーはそのまま
        # 一部成功したメンバーだけ成功に更新
        if send_failed:
            try:
                print(f"エラーあり:{send_failed}")
                print(f"成功欄を更新:{send_succeed}")
                update_email_delivered_by_email(mail_id,send_succeed)

            except Exception as e:
                session["message"] = f"送信結果の更新に失敗しました。hetemailにログインし、送信結果を確認してください。"
                log_error("送信結果のDB更新に失敗", e)
                return redirect(url_for("email.send_email"))

            session["message"] = f"{len(send_failed)}名の送信に失敗しました。履歴画面より確認してください。"
            return redirect(url_for("email.send_email"))

        else:
            # 更新処理(全員分のメール送信成功)
            try:
                #response = update_success(mail_id)
                send_email_success(mail_id)
                print("全員成功")
            
            except Exception as e:
                session["message"] = f"メールの送信に成功しましたが、データベースの更新に失敗しました。システム管理者に問い合わせください。"
                log_error("送信に成功したがDB更新に失敗", e)
                return redirect(url_for("email.send_email"))

            session["message"] = f"{len(selected_emails)}件のメールを送信しました。"
            return redirect(url_for("email.send_email"))

    last_input = get_last_sent_email(sent_emails)
    return render_template("send_email.html", user=user_id, message=message, data=recipients, mail_history=sent_emails, initial_value=last_input)

# 最後に送信したメールの内容を抽出
def get_last_sent_email(sent_emails):
    if not sent_emails:
        return {
            "from_name": "",
            "from_email": "",
            "subject": "",
            "body_text": ""
        }

    email = sent_emails[0]  # 最新の1件

    from_address = email["from_address"]
    subject = email["subject"]
    body_text = email["body"]

    # 差出人を分割
    match = re.match(r"^(.*)?\s*<([^>]+)>$", from_address)
    if match:
        from_name = match[1].strip() if match[1] else ""
        from_email = match[2]
    else:
        from_name = ""
        from_email = from_address.strip()

    return {
        "from_name": from_name,
        "from_email": from_email,
        "subject": subject,
        "body_text": body_text
    }
