import re
from functools import wraps
from flask import session, redirect, url_for
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import secrets
import string


# 大文字小文字の英数字か入力チェックを行う
# ログインフォームでのみ利用
def is_valid_login_id(login_id: str) -> bool:
    return re.match(r'^[a-zA-Z0-9_]+$', login_id) is not None

# パスワード自動生成
def generate_password(length=12):
    # string.ascii_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    # string.digits = '0123456789'
    allowed_chars = string.ascii_letters + string.digits + "_"

    return ''.join(secrets.choice(allowed_chars) for _ in range(length))


"""
現在のUTC時刻をISO 8601形式の文字列で返す。
Supabaseのtimestamptz型に渡す際に使用。
例: '2025-08-06T03:21:45.123456+00:00'
"""
def get_time_now():
    return datetime.now(timezone.utc).isoformat()

"""
UTC → JST に変換して日本語フォーマット（YYYY年M月D日H時M分S秒）で返す
Jinjaでの使用例:{{ mail.sent_at | jst_format }} または、{{ mail.sent_at | jst_format_jp }}
"""
# 通常フォーマット: YYYY-MM-DD HH:MM:SS
def jst_format(dt_utc) -> str:
    jst = _to_jst(dt_utc)
    if jst is None:
        return ""
    return jst.strftime("%Y-%m-%d %H:%M:%S")

# 日本語フォーマット: YYYY年M月D日H時M分S秒
def jst_format_jp(dt_utc) -> str:
    jst = _to_jst(dt_utc)
    if jst is None:
        return ""
    try:
        return jst.strftime("%Y年%-m月%-d日%-H時%-M分%-S秒")  # macOS/Linux
    except ValueError:
        return jst.strftime("%Y年%m月%d日%H時%M分%S秒")  # Windows

# UTCのdatetimeまたはISO文字列をJSTに変換
def _to_jst(dt_utc):
    if dt_utc is None:
        return None
    if not isinstance(dt_utc, datetime):
        dt_utc = datetime.fromisoformat(dt_utc)
    return dt_utc.astimezone(ZoneInfo("Asia/Tokyo"))




# middlewareで制御するので不要
#def login_required(f):
#    @wraps(f)  # fのメタ情報（関数名など）を保つためのデコレーター
#    def decorated_function(*args, **kwargs):   # セッションに'user_id'が無ければログインしていないと判断
#        if 'user_id' not in session:
#            return redirect(url_for('auth.login'))
#        return f(*args, **kwargs)  # ログイン済みなら元の関数を実行
#    return decorated_function