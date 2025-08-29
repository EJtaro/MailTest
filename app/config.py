import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    FLASK_DEBUG = os.getenv('FLASK_DEBUG')

    SECRET_KEY = os.getenv('SECRET_KEY')
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'

    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_FROM_NAME= os.getenv("MAIL_FROM_NAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_POP_SERVER = os.getenv("MAIL_POP_SERVER")
    MAIL_POP_PORT = int(os.getenv("MAIL_POP_PORT", 995))

    SENTRY_DSN = os.getenv("SENTRY_DSN")
    
    TINYURL_API = os.getenv("TINYURL_API")
