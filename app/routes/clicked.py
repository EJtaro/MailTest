from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from app.services.db import (
    get_email_delivered_by_mail_id_and_recipient_id,
    get_click_alert,
    update_email_delivered_clicked
)
from app.services.mail import MailClient
from app.services.log import log_error
from app.services.utils import is_valid_uuid,get_time_now, jst_format_jp

bp = Blueprint("clicked", __name__)

@bp.route("/url_clicked", methods=["GET"])
def url_clicked():
    mail_id = request.args.get("mail_id", "")
    recipient_id = request.args.get("recipient_id", "")
    now_time = get_time_now()
    formatted_time = jst_format_jp(now_time)

    print(f"メールID：{ mail_id }")
    print(f"送信先ID：{ recipient_id }")
    print(f"現在時刻：{ formatted_time }")

    if not mail_id or not recipient_id or not is_valid_uuid(mail_id) or not is_valid_uuid(recipient_id):
        print("パラメータ値が無効または未設定")
        return render_template("url_clicked.html")
    
    # mail_id、recipient_idを条件にemail_deliveredから探す
    try:
        result = get_email_delivered_by_mail_id_and_recipient_id(mail_id, recipient_id)
        print(f"取得結果：{ result }")
        print(f"recipientsの中身: {result.get('recipients')}")

        if not result or not result.get("recipients"):
            print("パラメータ値が未登録")
            return render_template("url_clicked.html")

        clicked = result.get("clicked")

        recipients = result.get("recipients")
        name = recipients.get("name")
        
        if clicked == True:
            # clickedがtrue(過去に同一URLクリック済み)なら何もしない
            print("URLクリック済み")
            return render_template("url_clicked.html")

        # clickedがfalseならtrueにし、時刻をclicked_atに登録する。
        update_email_delivered_clicked(result.get("delivered_id"), now_time)
        # さらにclick_alertに登録されたアドレスへ通知メール(時刻と名前)
        alert_list = get_click_alert()

        if not alert_list:
            # 通知先が未登録の場合、メールは送れないのでログにだけ残しておく。
            extra_info = {"mail_id": mail_id, "recipient_id": recipient_id}
            log_error("通知先が未登録です。", None, None, extra_info)
            print("通知先未登録")
            return render_template("url_clicked.html")

        # 辞書のリストからemailキーの値を取り出す
        mail_list = [data["email"] for data in alert_list]
        # 誤り - listから.getはNG
        #mail_list = alert_list.get("email")

        # URLクリック者の情報を通知
        for mail_address in mail_list:
            try:
                body_text = f"訓練メールのURLがクリックされました。 \n クリック者:{name} \n クリック時刻:{formatted_time}"
                mail_client = MailClient()
                mail_client.send_system_mail(
                    to_email=mail_address,
                    subject="訓練メールのURLがクリックされました。",
                    body_text=body_text
                )
            except Exception as e:
                # 送信に失敗した人のアドレスをログに保存し続行
                failed_address = {"mail_address": mail_address}
                log_error("URLクリック通知メールの送信に失敗", e, None, failed_address)
        
        print("正常終了")

    except Exception as e:
        extra_info = {"mail_id": mail_id, "recipient_id": recipient_id}
        log_error(f"email_deliveredの更新失敗", e, None, extra_info)
        return render_template("url_clicked.html")

    return render_template("url_clicked.html")