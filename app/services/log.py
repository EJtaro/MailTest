import logging
import sentry_sdk

# ローカルログの設定（console出力 or ファイルにも出せるよう拡張可能）
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

# ログ出力先のハンドラー設定
if not logger.hasHandlers():
    # コンソールにログを出すStreamHandlerを設定
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# エラー発生時に一括でロギング & Sentry送信
# 呼び出し例:log_error("エラーメッセージ", 例外[省略可], ログインID[省略可], 辞書型のその他情報[省略可])
def log_error(message: str, exception: Exception = None, user_id=None, extra: dict = None):
    # ローカルにエラーログ出力
    error_msg = f"{message}: {str(exception)}" if exception else message
    logger.error(error_msg)

    # Sentryにログの内容を送信
    with sentry_sdk.push_scope() as scope:
        # 追加情報のセット
        if user_id: # ログインID
            scope.set_user({"id": user_id})
        if extra: # その他
            for k, v in extra.items():
                scope.set_extra(k, v)
        # Sentryへの送信
        if exception:
            # 例外ログ
            sentry_sdk.capture_exception(exception)
        else:
            # Errorレベルとして扱われる例外なしのログ
            sentry_sdk.capture_message(message, level="error")