from flask import render_template
from app import constants

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", message=constants.MESSAGE_400), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return render_template("error.html", message=constants.MESSAGE_401), 401

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", message=constants.MESSAGE_404), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("error.html", message=constants.MESSAGE_500), 500

    @app.errorhandler(503)
    def internal_error(e):
        return render_template("error.html", message=constants.MESSAGE_503), 503
