from app import create_app

# Flaskアプリ起動
app = create_app()

# gunicorn(本番)で起動する場合、スクリプトとして実行されず、
# モジュールとして読み込まれるので、以下は実行されない
if __name__ == '__main__':
    # 開発環境(コマンド > python run.py等)で動く
    app.run(debug=True)
