from flask import request, session, render_template, abort
from app import constants

# ログイン必須なパス
authorized_path = constants.AUTHORIZED_PATH

# それぞれ全リクエストを対象に行う

# ログイン認証確認
def require_login(app):
    @app.before_request
    def _require_login():
        if request.path in authorized_path and 'user_id' not in session:
            abort(401)

# キャッシュを無効化
def no_cache_headers(app):
    @app.after_request
    def _add_headers(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
