from flask import Flask
from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.flask import FlaskIntegration
from app.config import Config
from app.middleware import require_login, no_cache_headers
from app.services.utils import jst_format, jst_format_jp
from dotenv import load_dotenv
from .routes import register_blueprints
from .error_handlers import register_error_handlers
from datetime import timedelta
import os
import logging

# 環境変数の読込
load_dotenv() 

sentry_init(
    dsn=Config.SENTRY_DSN,
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)

# Flaskアプリを生成
def create_app():
    app = Flask(__name__)

    # Configファイル読み込み
    app.config.from_object(Config)

    # 共通ミドルウェアの登録
    require_login(app)
    no_cache_headers(app)

    # Blueprints登録
    register_blueprints(app)
    # Errorhandlers登録
    register_error_handlers(app)

    # jinjaフィルターに時刻フォーマットを登録
    app.jinja_env.filters["jst_format"] = jst_format
    app.jinja_env.filters["jst_format_jp"] = jst_format_jp

    return app
