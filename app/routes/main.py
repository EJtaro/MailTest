
from flask import Blueprint, request, redirect, render_template, url_for

bp = Blueprint('main', __name__)  # 'main' は Blueprint の名前

@bp.route("/")
def root():
    return redirect(url_for("auth.login"))

# @bp.route("/index", methods=["GET", "POST"])
# def index():
#     keyword = request.args.get("keyword")  # GETの値（例：検索）
#     name = request.form.get("username") if request.method == "POST" else None  # POSTの値（例：フォーム入力）
#     return render_template("index.html", keyword=keyword, name=name) # テンプレート名と変数

# 訓練通知画面
# @bp.route("/training",methods=["GET"])

