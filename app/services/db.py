
from supabase import create_client
import os
from dotenv import load_dotenv
from app.config import Config
from app import constants

load_dotenv()

# supabaseのURLとKEYからDB接続
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# ユーザー情報
# ユーザー情報をユーザーIDから取得
def get_user_by_id(user_id):
    result = supabase.table(constants.USERS).select("*").eq("user_id", user_id).execute()
    return result.data[0] if result.data else []

# ユーザー情報をメールアドレスから取得
def get_user_by_email(mail_address):
    result = supabase.table(constants.USERS).select("*").eq("email", mail_address).execute()
    return result.data[0] if result.data else []

# ユーザー情報のパスワードを更新
def update_password(user_id, password_hash):
    supabase.table(constants.USERS).update({
        "password_hash": password_hash
    }).eq("user_id", user_id).execute()

# ユーザー情報のメールアドレス・ログインID・パスワードのいずれかを更新
# ログインID更新時、送信履歴情報のログインIDも更新(CASCADE)
def update_users(user_id, update_data):
    supabase.table(constants.USERS).update(update_data).eq("user_id", user_id).execute()


# 送信先情報(論理削除は除く)
# 送信先情報を全件取得
def get_recipients():
    result = supabase.table(constants.RECIPIENTS).select("*").eq("deleted", False).order("employee_no", desc=False).execute()
    return result.data or []

# 送信先情報をメールアドレスから取得
def get_recipient_id_by_email(email):
    result = supabase.table(constants.RECIPIENTS).select("recipient_id").eq("email", email).eq("deleted", False).execute()
    return result.data[0]["recipient_id"] if result.data else []

# 送信先情報に登録
def insert_recipients(employee_no, department, name, email):
    supabase.table(constants.RECIPIENTS).insert({
        "employee_no": employee_no,
        "department": department,
        "name": name,
        "email": email
    }).execute()

# メール送信先の"送信状態"を"success"にメールアドレスから更新
def update_email_delivered_by_email(mail_id, send_succeed):
    # 送信成功者のメールアドレスのrecipient_idを取得
    response = supabase.table(constants.RECIPIENTS).select("email, recipient_id").in_("email", send_succeed).eq("deleted", False).execute()
    # 辞書の作成
    recipient_map = {r["email"]: r["recipient_id"] for r in response.data}
    # 送信状態をsuccessに更新
    for email in send_succeed:
        recipient_id = recipient_map.get(email)
        if recipient_id:
            supabase.table(constants.EMAIL_DELIVERED).update({
                "state": "success"
            }).match({
                "mail_id": mail_id,
                "recipient_id": recipient_id
            }).execute()

# 送信先情報の部署・社員名・メールアドレスを社員番号から更新
def update_recipients_by_employee_no(employee_no, department, name, email):
    supabase.table(constants.RECIPIENTS).update({
        "department": department,
        "name": name,
        "email": email
    }).eq("employee_no", employee_no).eq("deleted", False).execute()

# 送信先情報を社員番号から論理削除
def delete_recipients_by_employee_no(employee_no):
    # supabase.table(constants.RECIPIENTS).delete().eq("employee_no", employee_no).execute()
    supabase.table(constants.RECIPIENTS).update({
        "deleted": True
    }).eq("employee_no", employee_no).execute()


# 送信履歴情報
# 送信履歴情報を全件取得
def get_mail_history():
    result = supabase.table(constants.SENT_EMAILS).select("*").order("sent_at", desc=True).execute()
    return result.data or []

# 送信履歴情報に登録
def insert_sent_emails(user_id, from_addr, subject, body, count):
    result = supabase.table(constants.SENT_EMAILS).insert({
        "user_id": user_id,
        "from_address": from_addr,
        "subject": subject,
        "body": body,
        "to_counts": count
    }).execute()
    return result.data[0]["mail_id"] if result.data else []

# 全件送信成功 - 未使用
def update_success(mail_id):
    # 送信履歴の送信状態を"成功"に更新
    supabase.table(constants.SENT_EMAILS).update({
        "state": "success"
    }).eq("mail_id", mail_id).execute()
    # メール送信先の送信状態を"成功"に更新
    supabase.table(constants.EMAIL_DELIVERED).update({
        "state": "success"
    }).eq("mail_id", mail_id).execute()


# メール送信先
# メール送信先をメールIDから取得(論理削除も込み)
def get_email_delivered_by_mail_id(mail_id):
    result = supabase.table(constants.EMAIL_DELIVERED).select("""
        *,
        recipients!inner (
            name,
            email,
            department,
            employee_no
        )
    """).eq("mail_id", mail_id).execute()
    # 社員番号で昇順にソート
    sorted_data = sorted(result.data, key=lambda x: x["recipients"]["employee_no"])
    return sorted_data if sorted_data else []

# メール送信先をメールIDから取得(論理削除も込み)
def get_email_delivered_by_mail_id_and_recipient_id(mail_id, recipient_id):
    result = supabase.table(constants.EMAIL_DELIVERED).select("""
        *,
        recipients!inner (
            name
        )
    """).eq("mail_id", mail_id).eq("recipient_id", recipient_id).execute()
    return result.data[0] or []

# メール送信先に登録
def insert_email_delivered(recipient_id, mail_id):
    supabase.table(constants.EMAIL_DELIVERED).insert({
        "recipient_id": recipient_id,
        "mail_id": mail_id
    }).execute()

# メール送信先の"クリック済み"を更新
def update_email_delivered_clicked(delivered_id, now_time):
    supabase.table(constants.EMAIL_DELIVERED).update({
        "clicked": True,
        "clicked_at": now_time
    }).eq("delivered_id", delivered_id).execute()

# メール送信先の"報告済み"を更新
def update_email_delivered(recipient_id, mail_id, reported):
    supabase.table(constants.EMAIL_DELIVERED).update({
        "reported": reported
    }).eq("mail_id", mail_id).eq("recipient_id", recipient_id).execute()

    # report_rateの再計算（報告済みの割合）
    # ↑トリガー"trg_email_delivered_reported_update"で対応
    # 報告率を取得
    result = supabase.table(constants.SENT_EMAILS).select("report_rate").eq("mail_id", mail_id).execute()
    return result.data[0] if result.data else 0


# 通知先
# 通知先を全件取得
def get_click_alert():
    result = supabase.table(constants.CLICK_ALERT).select("*").order("employee_no", desc=False).execute()
    return result.data or []

# 通知先に登録
def insert_click_alert(employee_no, department, name, email):
    supabase.table(constants.CLICK_ALERT).insert({
        "employee_no": employee_no,
        "department": department,
        "name": name,
        "email": email
    }).execute()

# 通知先の部署・社員名・メールアドレスを社員番号から更新
def update_click_alert_by_employee_no(employee_no, department, name, email):
    supabase.table(constants.CLICK_ALERT).update({
        "department": department,
        "name": name,
        "email": email
    }).eq("employee_no", employee_no).execute()

# 通知先を社員番号から削除
def delete_click_alert_by_employee_no(employee_no):
    supabase.table(constants.CLICK_ALERT).delete().eq("employee_no", employee_no).execute()


# Function
# 送信履歴情報・メール送信先を登録
def send_email_transaction(user_id, from_address_display, subject, body_text, selected_emails):
    # 関数"send_email_transaction"を実行
    response = supabase.rpc("send_email_transaction", {
        "p_user_id": user_id,
        "p_from_address": from_address_display,
        "p_subject": subject,
        "p_body": body_text,
        "p_recipients": selected_emails
    }).execute()

    # mail_idを返す
    return response.data

# 送信履歴情報・メール送信先の"送信状態"を"success"に更新
def send_email_success(mail_id):
    # 関数"send_email_success"を実行
    supabase.rpc("send_email_success", {
        "p_mail_id": mail_id
    }).execute()
