"""MastodonService.py
    Mastodonに関連する処理
"""
from mastodon import Mastodon, StreamListener
from bs4 import BeautifulSoup 
import GenerateToot
import hashlib

class MastodonService:

    def __init__(self, initValues, logger):
        """コンストラクタ
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
        """
        self.logger = logger
        self.mastodon = mastodon
        self.initValues = initValues
        self.mstdn_procedure = MastodonProcedure(self.logger, self.mastodon, self.initValues)
        self.generateToots = GenerateToot.GenerateToots(self.logger, self.initValues)

    def on_notification(self, notif):
        """通知受信処理
            通知を受信した場合の処理
        """
        try:
            if notif['type'] == 'mention':
                self.logger.info("mentionの検知")

                # 各種項目の取得、設定。
                st = notif['status'] # ステータス情報全般 JSON形式
                id = notif['status']['account']['username'] # id
                uri = notif['status']['uri'] # ユーザのインスタンスURI
                content_raw = notif['status']['content'] # リプライ内容
                content = self.EditContents(content_raw) # 質問文の編集

                if notif['status']['visibility'] == 'direct': # 公開範囲設定。directでリプライされた際はdirectで、それ以外はunlistedで返答を行う。
                    visibility_status = self.initValues.mastodon_bot_visibility_direct
                else:
                    visibility_status = self.initValues.mastodon_bot_visibility_unlisted

                if self.initValues.mastodon_bot_api_base_url not in str(uri): # インスタンスチェック
                    self.logger.warning("別インスタンスからのリプライ")

                elif len(notif['status']['mentions']) > 1: # 質問者以外のアカウントへのリプライ防止
                    self.logger.warning("複数アカウント検知")

                elif 'emergencystopsignal' in str(content): # 緊急停止信号発報確認
                    if hashlib.sha256(str(content).encode('ascii')).hexdigest() == str(self.initValues.stop):
                        self.logger.warning("緊急停止信号発報 プログラムの終了")
                        self.mastodon.status_post('緊急停止信号検知。強制終了します。', visibility = 'unlisted')
                        exit()

                elif len(str(content)) == 0: # 未入力チェック
                    self.logger.warning("質問未入力")
                    self.mastodon.status_reply(st, '質問内容を入力してください。', id, visibility = visibility_status)

                else:
                    # 正常処理                                        
                    self.logger.info('@' + str(id) + "さんへ返信処理開始")
                    content = "質問します。" + content
                    self.logger.info("質問文:" + str(content))

                    res = self.generateToots.gen_msg(content) # 回答文生成

                    self.mstdn_procedure.do_toot(res, id, st, visibility_status) # トゥート

        except Exception as e:
            self.logger.critical("通知の受信に関して、エラーが発生しました。" + str(e))
    
    def EditContents(self, content_raw):
        '''質問内容編集
            取り出したリプライの情報より、質問文を編集する。
        '''
        try:
            self.logger.info("質問文の編集処理開始")

            html_data = BeautifulSoup(content_raw, "html.parser")

            links = html_data.find_all("a") # リンクを抽出

            # URLを連結する
            content_links = ""
            if len(links) > 1:
                for i in range(1, len(links)):
                    content_links += links[i].get("href") + ' '

            # リプライ本文を抜き出す。
            if html_data.find("span").next_sibling == None:
                content = ""
            else:
                content = html_data.find("span").next_sibling
            
            # リプライ本文とURLを結合する。
            return content + content_links
        
        except Exception as e:
            self.logger.critical("質問文編集処理で、エラーが発生しました。" + str(e))        
        
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