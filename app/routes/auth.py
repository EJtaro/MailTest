from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from app.services.db import get_user_by_id, get_user_by_email, update_password
from app.services.mail import MailClient
from app.services.utils import is_valid_login_id, generate_password
from app.services.log import log_error

bp = Blueprint('auth', __name__)

@bp.route("/login", methods=["GET","POST"])
def login():
    username = ""
    error_message = ""
    
    try:
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if request.method == "GET" and "user_id" in session:
            # ログイン済みの場合、メール送信画面へリダイレクト
            return redirect(url_for("email.send_email"))

        if request.method == "POST":

            # ログインssessionが切れているときのみ動く
            if request.form.get("restart") == "error":
                # 再び再発行画面を開いたときにエラーメッセージが出ないようにするため
                session.pop("error", None)
                return redirect(url_for("auth.login"))
            
            if is_valid_login_id(username) and password:
                user = get_user_by_id(username)

                if user and check_password_hash(user.get("password_hash"),password):
                    session.permanent = True # ブラウザが閉じられるまでセッションを維持
                    session["user_id"] = user["user_id"] # Session値を保持
                    return redirect(url_for("email.send_email"))
                error_message = "登録済みのログインID・パスワードを入力してください。"
            else:
                error_message = ( 
                    "ユーザー名が未入力です。" if username == "" else 
                    "ログインIDには英数字とアンダースコア(_)のみ入力可能です。" if not is_valid_login_id(username) else
                    "パスワードが未入力です。"
                )
                #return jsonify(success=False, error="ユーザー名またはパスワードが未入力です。")

    except Exception as e:
        log_error("ログイン処理に失敗に失敗", e)
        error_message = "システムエラーが発生しました。管理者に連絡してください。"
        return render_template("login.html", error=error_message)
    return  render_template("login.html", error = error_message, username=username, password=password)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    error = session.pop("error", None)
    if request.method == "POST":
        # 受け取ったアドレスが登録済みか確認
        mail_address = request.form.get("mail_address")
        user_id = ""
        try:
            result = get_user_by_email(mail_address)

            if result:
                user_id = result.get("user_id")
                # パスワードを再生成
                password = generate_password()
                print(password)

                password = "mail0406"
                # ハッシュ化
                password_hash = generate_password_hash(password)
                print(password_hash)
                # パスワードを登録
                error = "OK"
                session["error"] = error
                update_password(user_id, password_hash)
            else:
                session["error"] = "未登録のアドレスです。"
                return redirect(url_for("auth.forgot_password"))

        except Exception as e:
            log_error("パスワード再発行に失敗", e)
            session["error"] = "パスワードの再発行中にエラーが発生しました。\n しばらく時間をおいてから、お試しください。"
            return redirect(url_for("auth.forgot_password"))

        # メール送信
        try:
            body_text = f"パスワードを再発行いたしました。 \n ログインID:{user_id} \n パスワード:{password}"
            mail_client = MailClient()
            mail_client.send_system_mail(
                to_email=mail_address,
                subject="パスワードを再発行",
                body_text=body_text
            )
        except Exception as e:
            log_error("パスワード通知メールの送信に失敗", e)
            session["error"] = f"{mail_address} への送信に失敗しました。"
            return redirect(url_for("auth.forgot_password"))
        
        session["error"] = f"{mail_address} へログインIDと再発行したパスワードを送信しました。"
        return redirect(url_for("auth.forgot_password"))
    return render_template("forgot_password.html", error=error)

