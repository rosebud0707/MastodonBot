from mastodon import Mastodon, StreamListener
import requests
import random
import linecache
import logging
import configparser
import os
import datetime

class Stream(StreamListener):
    # StreamListenerを継承
    def on_notification(self,notif):
        # 通知の検知
        try:
            if notif['type'] == 'mention':
                content = notif['status']['content']
                id = notif['status']['account']['username']
                st = notif['status']
                logging.info("@" + str(id) + "さんへ返信処理開始")
                # メイン処理呼び出し
                replyMsg(content, st, id)
        except Exception as e:
            logging.critical("通知の受信に関して、エラーが発生しました。" + str(e))

# ログ出力設定
def logCreator(logFilePath):
    # 新規作成or上書きモード
    if os.path.isfile(logFilePath):
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

# データソース行数取得
def readLines():
    count = 0
    try:
        with open(os.path.dirname(__file__) + "/" + ini['botSetting']['dataSourceFileNm'], encoding="utf-8", mode="r") as f:
            for line in f:
                count += 1
            logging.info(str(count))
            return count
    except Exception as e:
        logging.critical("データ読み込みに関して、エラーが発生しました。" + str(e))    

# メイン処理
def replyMsg(content,st,id):
    try:
        logging.info("メイン処理開始")
        # インデックス生成
        rand = random.randint(1,readLines())
        # 項目設定
        target_line = linecache.getline(os.path.dirname(__file__) + "/" + ini['botSetting']['dataSourceFileNm'], rand)
        # 文書生成
        resr = "今日のあなたが作るべき役は"+ target_line + "です。"
        # クリア
        linecache.clearcache() 
        # 返信
        mastodon.status_reply(st,
                            resr,
                            id,
                            visibility=ini['botSetting']['visibilityUnlisted'])
    except Exception as e:
        logging.critical("返信に関してエラーが発生しました。" + str(e))    

# 外部設定ファイル読み込み
ini = configparser.ConfigParser()
ini.read(os.path.dirname(__file__) + r'/config.ini', 'UTF-8') #.pyと同じディレクトリに配置してる前提

# 日付
t_delta = datetime.timedelta(hours=9)
JST = datetime.timezone(t_delta, 'JST')
now = datetime.datetime.now(JST)

# ログファイルパス　.pyと同ディレクトリ + 設定ファイルのファイル名 + yyyyMMdd + 設定ファイルの拡張子
logFilePath = os.path.dirname(__file__) + '/' + ini['LogWriter']['fileNmBase'] + "_" + now.strftime('%Y%m%d')+ ini['LogWriter']['extension']

# ログファイル生成
logCreator(logFilePath)

# インスタンス化
logging.info("インスタンス生成")
mastodon = Mastodon(
         client_id = ini['botSetting']['client_id'],
         client_secret = ini['botSetting']['client_secret'],
         access_token = str(ini['botSetting']['access_token']),
         api_base_url = ini['botSetting']['api_base_url'] )

# Stream起動
logging.info("Stream起動")
mastodon.stream_user(Stream())
