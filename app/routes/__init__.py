from .auth import bp as auth_bp
from .email import bp as email_bp
from .main import bp as main_bp
from .master import bp as master_bp
from .clicked import bp as clicked_bp

# Blueprint登録
def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(clicked_bp)
