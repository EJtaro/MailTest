from flask import Blueprint, render_template, request, redirect, session, url_for, jsonify
from app.services.db import (
    get_recipients,
    get_mail_history,
    get_user_by_id,
    get_email_delivered_by_mail_id,
    get_click_alert,
    insert_recipients,
    insert_click_alert,
    update_recipients_by_employee_no,
    update_click_alert_by_employee_no,
    update_email_delivered,
    update_users,
    delete_recipients_by_employee_no,
    delete_click_alert_by_employee_no
)
from app.services.log import log_error
from app.services.utils import is_valid_login_id
from werkzeug.security import generate_password_hash

bp = Blueprint("master", __name__)


# 送信先管理画面
@bp.route("/recipient_master", methods=["GET", "POST"])
def recipient_master():
    message = session.pop("message", None)

    user_id = session["user_id"]

    try:
        recipients = get_recipients()       # 送信先一覧取得
    except Exception as e:
        session["message"] = f"初期値取得失敗: {str(e)}"
        log_error("送信先・送信履歴取得失敗", e)
        return redirect(url_for("master.recipient_master"))

    if request.method == "POST":
        mode = request.form.get("mode")

        # 値取得
        employee_no = request.form.get("employee_no", "")
        department = request.form.get("department", "")
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        print(employee_no)

        if mode == "insert":
            # 登録処理
            try:
                insert_recipients(employee_no, department, name, email)
            except Exception as e:
                session["message"] = f"登録に失敗しました。: {str(e)}"
                log_error("送信先の登録に失敗", e)
                return redirect(url_for("master.recipient_master"))

            session["message"] = f"{ employee_no }のデータを登録しました。"

        elif mode == "update":
            # 更新処理
            try:
                update_recipients_by_employee_no(employee_no, department, name, email)
            except Exception as e:
                session["message"] = f"更新に失敗しました。: {str(e)}"
                log_error("送信先の更新に失敗", e)
                return redirect(url_for("master.recipient_master"))

            session["message"] = f"{ employee_no }のデータを更新しました。"

        elif mode == "delete":
            # 削除処理
            # idがemail_deliveredと紐づいているのでも論理削除とする
            try:
                delete_recipients_by_employee_no(employee_no)
            except Exception as e:
                session["message"] = f"削除に失敗しました。: {str(e)}"
                log_error("送信先の削除に失敗", e)
                return redirect(url_for("master.recipient_master"))

            session["message"] = f"{ employee_no }のデータを削除しました。"

        return redirect(url_for("master.recipient_master"))

    return render_template("recipient_master.html", user=user_id, message=message, data=recipients)


# 送信履歴画面
@bp.route("/mail_master", methods=["GET"])
def mail_master():
    message = session.pop("message", None)

    user_id = session["user_id"]
    mail_id = request.args.get("mail_id")

    try:
        sent_emails = get_mail_history()    # 送信履歴取得
    except Exception as e:
        session["message"] = f"初期値取得失敗: {str(e)}"
        log_error("送信履歴・メール送信先取得失敗", e)
        return redirect(url_for("email.send_email"))

    # 初期表示では空の送信先リストを渡す
    delivered_list = []
    return render_template("mail_master.html", user=user_id, message=message, mail_history=sent_emails, delivered_list=delivered_list)

# メール送信先を返すAPI
# 取得なので[GET]
@bp.route("/mail_master/delivered_list", methods=["GET"])
def api_delivered_list():
    mail_id = request.args.get("mail_id")
    if not mail_id:
        return jsonify({"error": "mail_id is required"}), 400

    try:
        delivered_list = get_email_delivered_by_mail_id(mail_id)
        return jsonify(delivered_list)
    except Exception as e:
        log_error("メール送信先取得失敗", e)
        return jsonify({"error": str(e)}), 500

# 報告チェックボックスクリックにあわせてDB反映
# 更新なので[POST]
@bp.route("/mail_master/report", methods=["POST"])
def update_report():
    data = request.get_json()
    recipient_id = data.get("recipient_id")
    mail_id = data.get("mail_id")
    reported = data.get("checked")

    try:
        result = update_email_delivered(recipient_id, mail_id, reported)
        report_rate = result.get("report_rate", 0)
        # HTML側のパーセント化は機能しないのでここで処理する
        report_rate_percent = round(report_rate * 100, 1)

        return jsonify({"success": True, "report_rate": report_rate_percent})
    except Exception as e:
        print(f"エラー：{e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ユーザー管理画面
@bp.route("/user_master", methods=["GET", "POST"])
def user_master():
    message = session.pop("message", None)
    user_id = session["user_id"]

    try:
        user_data = get_user_by_id(user_id)  # ユーザー情報取得
        alert_list = get_click_alert()       # 通知先一覧取得
    except Exception as e:
        session["message"] = f"初期値取得失敗: {str(e)}"
        log_error("ユーザー情報・通知先取得失敗", e)
        return redirect(url_for("master.user_master"))
    
    if request.method == "POST":
        print("post処理")
        mode = request.form.get("mode")

        if not mode:
            # 管理者更新処理
            try:
                print("ユーザー更新")
                user_email = request.form.get("user_email", "")
                new_user_id = request.form.get("user_id", "")
                password = request.form.get("password", "")

                # 登録データ作成
                update_data = {}
                if new_user_id:
                    if not is_valid_login_id(new_user_id):
                        session["message"] = "ログインIDには大文字小文字の英数字とアンダースコア(_)のみ入力可能です。" 
                        return redirect(url_for("master.user_master"))
                    update_data["user_id"] = new_user_id
                if user_email:
                    update_data["email"] = user_email
                if password:
                    password_hash = generate_password_hash(password)
                    # ハッシュ化
                    print(f"ハッシュ化：{password_hash}")
                    update_data["password_hash"] = password_hash
                
                if not update_data:
                    session["message"] = "登録データ取得失敗"
                    return redirect(url_for("master.user_master"))

                update_users(user_id, update_data)
                # セッション値も更新
                session["user_id"] = new_user_id
                session["message"] = "管理者情報を更新しました。"
            except Exception as e:
                session["message"] = f"管理者情報の更新に失敗しました: {str(e)}"
                log_error("管理者情報の更新に失敗", e)
            
            return redirect(url_for("master.user_master"))

        # 値取得
        employee_no = request.form.get("employee_no", "")
        department = request.form.get("department", "")
        name = request.form.get("name", "")
        email = request.form.get("email", "")

        if mode == "insert":
            # 登録処理
            try:
                print("登録")
                insert_click_alert(employee_no, department, name, email)
            except Exception as e:
                session["message"] = f"登録に失敗しました。: {str(e)}"
                log_error("通知先の登録に失敗", e)
                return redirect(url_for("master.user_master"))

            session["message"] = f"{ employee_no }のデータを登録しました。"

        elif mode == "update":
            # 更新処理
            try:
                print("更新")
                update_click_alert_by_employee_no(employee_no, department, name, email)
            except Exception as e:
                session["message"] = f"更新に失敗しました。: {str(e)}"
                log_error("通知先の更新に失敗", e)
                return redirect(url_for("master.user_master"))

            session["message"] = f"{ employee_no }のデータを更新しました。"

        elif mode == "delete":
            # 削除処理
            try:
                print("削除")
                delete_click_alert_by_employee_no(employee_no)
            except Exception as e:
                session["message"] = f"削除に失敗しました。: {str(e)}"
                log_error("通知先の削除に失敗", e)
                return redirect(url_for("master.user_master"))

            session["message"] = f"{ employee_no }のデータを削除しました。"

        return redirect(url_for("master.user_master"))

    return render_template("user_master.html", user=user_id, message=message, user_data=user_data, alert_list=alert_list)
