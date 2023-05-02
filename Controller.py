"""Controller.py
    外部設定ファイルの読み込み、ログ出力クラスのインスタンス化
    Mastodonサービスの起動を行う
"""
import Initialize
import os
import MastodonService

class Controller:
    """コントローラ
        各処理を呼び出す。
    """
    def __init__(self):
        """コンストラクタ
            外部設定ファイルの値取得、ログ出力クラスのインスタンス化
        """
        # インスタンス化
        init = Initialize.InitRead()

        # 外部設定ファイル_値取得
        self.initValues = init.__initValues__()

        # ログファイルパス設定　.pyと同ディレクトリ + 設定ファイルのファイル名 + yyyyMMdd + 設定ファイルの拡張子
        logFilePath = os.path.dirname(os.path.abspath(__file__)) + '/' + self.initValues.log_file_name + "_" + self.initValues.now_date + self.initValues.log_file_name_extension

        # インスタンス化
        self.logging = Initialize.Loggings(logFilePath)

    def run(self):
        """Mastodonサービスの起動
        """
        MastodonService.MastodonService(self.initValues,
                                        self.logging)

# インスタンス化
ctrl = Controller()

# 処理開始
ctrl.logging.info("bot起動")
ctrl.run()