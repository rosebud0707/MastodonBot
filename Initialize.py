"""Initialize.py
    初期設定処理を記載
"""
import configparser
import dataclasses
import datetime
import logging
import os

@dataclasses.dataclass
class InitializeSetting:
    """データエンティティ
        iniファイルの内容保持用エンティティクラス
    """
    log_file_name: str
    log_file_name_extension: str
    mastodon_bot_client_id: str
    mastodon_bot_client_secret: str
    mastodon_bot_access_token: str
    mastodon_bot_api_base_url: str
    mastodon_bot_visibility_unlisted: str
    now_date: str
    #mastodon_bot_datasource_path: str
    chatgpt_api_key: str

class Init_read:
    """初期設定
        外部設定ファイルを読み込む
    """
    def __initValues__(self):
        """初期設定
            外部設定ファイルの値をデータエンティティにセット
            Returns:データエンティティ(外部設定ファイル)
        """
        try:
            # 外部設定ファイル読み込み
            ini = configparser.ConfigParser()
            ini.read(os.path.dirname(os.path.abspath(__file__)) + r'/Config.ini', 'UTF-8') #.pyと同じディレクトリに配置してる前提

            # 日付設定
            t_delta = datetime.timedelta(hours=9)
            JST = datetime.timezone(t_delta, 'JST')
            now = datetime.datetime.now(JST)

            # 内容設定
            return InitializeSetting(
                                    log_file_name = str(ini['LogWriter']['fileNmBase']),
                                    log_file_name_extension = str(ini['LogWriter']['extension']),
                                    mastodon_bot_client_id = str(ini['botSetting']['client_id']),
                                    mastodon_bot_client_secret = str(ini['botSetting']['client_secret']),
                                    mastodon_bot_access_token = str(ini['botSetting']['access_token']),
                                    mastodon_bot_api_base_url = str(ini['botSetting']['api_base_url']),
                                    mastodon_bot_visibility_unlisted = str(ini['botSetting']['visibilityUnlisted']),
                                    now_date = now.strftime('%Y%m%d'),
                                    # self.mastodon_bot_datasource_path = str(ini['LogWriter']['extension'])
                                    chatgpt_api_key = str(ini['chatGPTSetting']['API_key'])
                                    )

        except Exception as e:
            print("iniファイル読み込みエラー" + str(e))
            input()
            exit

class Loggings:
    """初期設定
        ログファイルの生成を行う
    """
    def __init__(self, logFilePath):
        """コンストラクタ
            ログファイルの生成を行う
            Args:
                logFilePath:ログファイル出力場所
        """
        try:
            # 新規作成or上書きモード
            if  os.path.isfile(logFilePath):
                # 上書き
                wkFileMode = "a"
            else:
                # 新規作成
                wkFileMode = "w"

            logging.basicConfig(filename = logFilePath,                                      # ログファイル名 
                                filemode = wkFileMode,                                       # ファイル書込モード
                                level    = logging.DEBUG,                                    # ログレベル
                                format   = " %(asctime)s - %(levelname)s - %(message)s "     # ログ出力フォーマット
                            )
            
        except Exception as e:
            print("ログファイル設定エラー" + str(e))
            exit
    
    def debug(self, str):
        """debugログ
            Args:
                str:任意の表示メッセージ
        """
        logging.debug(str)

    def info(self, str):
        """infoログ
            Args:
                str:任意の表示メッセージ
        """
        logging.info(str)

    def warning(self, str):
        """warningログ
            Args:
                str:任意の表示メッセージ
        """
        logging.warning(str)

    def error(self, str):
        """errorログ
            Args:
                str:任意の表示メッセージ
        """
        logging.error(str)

    def critical(self, str):
        """criticalログ
            Args:
                str:任意の表示メッセージ
        """
        logging.critical(str)
