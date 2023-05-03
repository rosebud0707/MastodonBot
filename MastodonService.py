"""MastodonService.py
    Mastodonに関連する処理
"""
from bs4 import BeautifulSoup 
from mastodon import Mastodon, StreamListener
import asyncio
import datetime
import GenerateToot
import hashlib

class MastodonService:
    """MastodonService
        Mastodonの初期設定を行い、StreamListerを起動する。
    """
    def __init__(self, initValues, logger):
        """コンストラクタ
            Args:
                initValues:外部設定ファイル保持データクラス
                logger:ロガーインスタンス
        """
        self.initValues = initValues
        self.mastodon = Mastodon(client_id = self.initValues.mastodon_bot_client_id,
                                client_secret = self.initValues.mastodon_bot_client_secret,
                                access_token = self.initValues.mastodon_bot_access_token,
                                api_base_url = self.initValues.mastodon_bot_api_base_url )
        self.logger = logger
        self.logger.info("StreamListnerの起動")
        self.mastodon.stream_user(Stream(self.logger, self.mastodon, self.initValues))
    
class Stream(StreamListener):
    """StreamListenerを継承
       各種StreamListenerの処理を行う
    """
    def __init__(self, logger, mastodon, initValues):
        """コンストラクタ
            Args:
                initValues:外部設定ファイル保持データクラス
                logger:ロガーインスタンス
                mastodon:Mastodonインスタンス
        """
        self.logger = logger
        self.mastodon = mastodon
        self.initValues = initValues
        self.mstdn_procedure = MastodonProcedure(self.logger, self.mastodon, self.initValues)
        self.generateToots = GenerateToot.GenerateToots(self.logger, self.initValues)
        self.dict_id = {}

    def on_notification(self, notif):
        """通知受信処理
            通知を受信した場合の処理
            Args:
                notif:通知
        """
        try:
            if notif['type'] == 'mention':
                self.logger.info("mentionの検知")

                # 各種項目の取得、設定
                st = notif['status'] # ステータス情報全般 JSON形式
                id = notif['status']['account']['username'] # id
                uri = notif['status']['uri'] # ユーザのインスタンスURI
                content_raw = notif['status']['content'] # リプライ内容
                content = self.edit_content(content_raw) # 質問文の編集

                # ID保持用のディクショナリ削除
                self.del_id()
                
                # 公開範囲設定。directでリプライされた際はdirectで、それ以外はunlistedで返答を行う。
                if notif['status']['visibility'] == 'direct':
                    visibility_status = self.initValues.mastodon_bot_visibility_direct
                else:
                    visibility_status = self.initValues.mastodon_bot_visibility_unlisted

                 # インスタンスチェック 他インスタンスへは返信を行わない。
                if self.initValues.mastodon_bot_api_base_url not in str(uri):
                    self.logger.warning("別インスタンスからのリプライ")
                 # 質問者以外のアカウントへのリプライ防止
                elif len(notif['status']['mentions']) > 1:
                    self.logger.warning("複数アカウント検知")
                # 緊急停止信号発報確認
                elif 'emergencystopsignal' in str(content): 
                    if hashlib.sha256(str(content).encode('ascii')).hexdigest() == str(self.initValues.stop):
                        self.logger.warning("緊急停止信号発報 プログラムの終了")
                        self.mastodon.status_post('緊急停止信号検知。強制終了します。', visibility = 'unlisted')
                        exit()
                # 投稿間隔チェック
                elif self.check_receive_interval(id):
                    self.logger.warning("投稿間隔が短いです。")
                # 未入力チェック
                elif len(str(content)) == 0: 
                    self.logger.warning("質問未入力")
                    self.mastodon.status_reply(st, '質問内容を入力してください。', id, visibility = visibility_status)
                # 正常処理   
                else:                             
                    self.logger.info('@' + str(id) + "さんへ返信処理開始")
                    content = "こんにちは。" + content
                    self.logger.info("質問文:" + str(content))

                    loop = asyncio.get_event_loop()
                    res = loop.run_until_complete((self.generateToots.process_wait(content))) # 回答文生成

                    self.mstdn_procedure.do_toot(res, id, st, visibility_status) # トゥート

        except Exception as e:
            self.logger.critical("通知の受信に関して、エラーが発生しました。" + str(e))
    
    def edit_content(self, content_raw):
        '''質問内容編集
            取り出したリプライの情報より、質問文を編集する。
            Args:
                content_raw:タグを含んだリプライ文
            Returns:
                編集済質問文
        '''
        try:
            self.logger.info("質問文の編集処理開始")

            # 改行の削除
            content_raw = str(content_raw).replace("<br>", " ")
            content_raw = str(content_raw).replace("</br>", " ")
            content_raw = str(content_raw).replace("<br />", " ")

            html_data = BeautifulSoup(content_raw, "html.parser")

            links = html_data.find_all("a") # リンクを抽出

            # URLを連結する
            content_links = ""
            if len(links) > 1:
                for i in range(1, len(links)):
                    content_links += links[i].get("href") + ' '

            # リプライ本文を抜き出す
            if html_data.find("span").next_sibling == None:
                content = ""
            else:
                content = html_data.find("span").next_sibling
            
            # リプライ本文とURLを結合する
            return content + content_links
        
        except Exception as e:
            self.logger.critical("質問文編集処理で、エラーが発生しました。" + str(e))
    
    def check_receive_interval(self, id):
        '''投稿間隔チェック
            同一IDより規定時間以内に再度投稿されたかを確認する。規定時間以内の場合は処理を行わない。
            Args:
                id:ユーザID
            Returns:
                True:規定時間以内
                False:規定時間外
        '''
        try:
            self.logger.info("投稿間隔チェック")
            if id not in self.dict_id.keys():
                self.dict_id[id] = datetime.datetime.now()
                return False
            elif self.dict_id[id] + datetime.timedelta(seconds=self.initValues.receive_interval) > datetime.datetime.now():
                return True
            else:
                self.dict_id[id] = datetime.datetime.now()
                return False

        except Exception as e:
            self.logger.critical("投稿間隔チェックで、エラーが発生しました。" + str(e))
            return False
    
    def del_id(self):
        '''ディクショナリ削除処理
            投稿間隔の規定時間を超えているIDの削除
        '''
        try:
            self.logger.info("ディクショナリの確認、削除")
            if len(self.dict_id) > 0:
                for key in list(self.dict_id.keys()):
                    if self.dict_id[key] + datetime.timedelta(seconds=self.initValues.receive_interval) < datetime.datetime.now():
                        self.dict_id.pop(key)

        except Exception as e:
            self.logger.critical("ディクショナリ削除処理で、エラーが発生しました。" + str(e))
            return False
        
class MastodonProcedure:
    """Mastodonの各処理を行う
    """
    def __init__(self, logger, mastodon, initValues):
        """コンストラクタ
        """
        self.logger = logger
        self.mastodon = mastodon
        self.initValues = initValues

    def do_toot(self, response, id, st, visibility_param):
        """トゥート処理
            生成文書を編集し、トゥートする。
            Args:
                response:生成分
                id:Mastodon User ID
                st:status
        """
        try:
            if response == 'None':
                self.logger.critical("予期せぬエラーの発生。")
                self.mastodon.status_post('予期せぬエラーの発生。強制終了します。', visibility = 'unlisted') # bot同士の会話、予期せぬエラーでの暫定対応策
                exit()

            response = str(response).replace('@', '＠') # リプライの防止

            self.logger.info("トゥート")
            if len(response) > 480:  # トゥート上限エラー回避。バッファをみて480字超過時は分割。
                length = len(response)
                splitLine =  [response[i:i+300] for i in range(0, length, 300)]

                for num in range(len(splitLine)):
                    # 返信
                    self.mastodon.status_reply(st,
                                str(splitLine[num]),
                                id,
                                visibility = visibility_param)
            else:
                self.mastodon.status_reply(st,
                        str(response),
                        id,
                        visibility = visibility_param)
                
        except Exception as e:
            self.logger.critical("トゥート処理にて、エラーが発生しました。" + str(e))