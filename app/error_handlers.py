from flask import render_template

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", message="400 - 不正なリクエストです"), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return render_template("error.html", message="401 - 認証が必要です"), 401

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", message="404 - ページが見つかりません"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("error.html", message="500 - サーバーエラーです"), 500
