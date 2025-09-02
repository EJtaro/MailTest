
from flask import Blueprint, request, redirect, render_template, url_for

bp = Blueprint('main', __name__)  # 'main' は Blueprint の名前

@bp.route("/")
def root():
    return redirect(url_for("auth.login"))

# 稼働チェック(UptimeRobot)用エンドポイント
@bp.route("/ping", methods=["GET", "HEAD"])
def ping_check():
    return "", 200