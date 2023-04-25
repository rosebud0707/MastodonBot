"""MastodonService.py
    Mastodonに関連する処理
"""
from mastodon import Mastodon, StreamListener
import GenerateToot

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
                content = notif['status']['content']
                content = content.rsplit(">")[-2].split("<")[0].strip() #タグ除去
                
                if content == str(self.initValues.stop):
                    self.mastodon.toot('強制終了します。')
                    exit()
                else:
                    id = notif['status']['account']['username']
                    st = notif['status']
                    self.logger.info("@" + str(id) + "さんへ返信処理開始")
                    
                    content = str(content) + " 必ず500文字以内で簡潔に回答してください。"

                    self.logger.info(content)

                    res = self.generateToots.gen_msg(content)

                    self.mstdn_procedure.do_toot(res, id, st)

        except Exception as e:
            self.logger.critical("通知の受信に関して、エラーが発生しました。" + str(e))

class MastodonProcedure:
    """Mastodonの各処理を行う
    """
    def __init__(self, logger, mastodon, initValues):
        """コンストラクタ
        """
        self.logger = logger
        self.mastodon = mastodon
        self.initValues = initValues

    def do_toot(self, response, id, st):
        """トゥート処理
            生成文書を編集し、トゥートする。
            Args:
                response:生成分
                id:Mastodon User ID
                st:status
        """
        try:
            response = str(response).replace('@', '＠') # 対象者以外へのリプライ防止

            if len(response) > 480:  # トゥート上限エラー回避。バッファをみて480字超過時は分割。
                length = len(response)
                splitLine =  [response[i:i+300] for i in range(0, length, 300)]

                for num in range(len(splitLine)):
                    # 返信
                    self.mastodon.status_reply(st,
                                str(splitLine[num]),
                                id,
                                visibility = self.initValues.mastodon_bot_visibility_private)
            else:
                self.mastodon.status_reply(st,
                        str(response),
                        id,
                        visibility = self.initValues.mastodon_bot_visibility_private)
                
        except Exception as e:
            self.logger.critical("トゥート処理にて、エラーが発生しました。" + str(e))