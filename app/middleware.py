from flask import request, session, render_template

# ログイン不要なパス
EXEMPT_PATHS = {'/login', '/logout', '/error', '/'}

# ログイン必須なパス（例：管理画面など）
AUTHORIZED_PATH = {'/send_email', '/recipient_master', '/mail_master', '/user_master'}

# それぞれ全リクエストを対象に行う

def require_login(app):
    @app.before_request
    def _require_login():
        #print("パス:", request.path)
        #print("セッション:", dict(session))

        if request.path in AUTHORIZED_PATH and 'user_id' not in session:
            return render_template('error.html', message='401 - 認証が必要です。'), 401

def no_cache_headers(app):
    @app.after_request
    def _add_headers(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
