"""MastodonService.py
    Mastodonに関連する処理
"""
from mastodon import Mastodon, StreamListener
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
                content_raw = notif['status']['content']
                content = content_raw.rsplit(">")[-2].split("<")[0].strip() # リプライよりhtmlタグ除去。リプライ文だけを取得。
                st = notif['status'] # ステータス情報全般 JSON形式
                id = notif['status']['account']['username'] # id
                uri = notif['status']['uri']

                if 'emergency' in content:
                    if hashlib.sha256(str(content).encode('ascii')).hexdigest() == str(self.initValues.stop):
                        self.mastodon.status_post('強制終了します。', visibility = 'unlisted')
                        exit()

                elif self.initValues.mastodon_bot_api_base_url not in str(uri):
                    self.mastodon.status_reply(st, '特定のインスタンスのアカウント以外には返答できません。', id, visibility = 'unlisted')

                else:
                    st = notif['status'] # ステータス情報全般 JSON形式
                    id = notif['status']['account']['username'] # id
                    disp_name = notif['status']['account']['display_name'] # 表示名
                    
                    if notif['status']['visibility'] == 'direct': # 公開範囲設定。directでリプライされた際はdirectで、それ以外はunlistedで返答を行う。
                        visibility = self.initValues.mastodon_bot_visibility_direct
                    else:
                        visibility = self.initValues.mastodon_bot_visibility_unlisted
                    
                    self.logger.info("@" + str(id) + "さんへ返信処理開始")
                    content = str(content) + "必ず500文字以内で簡潔に回答してください。"
                    self.logger.info("質問文:" + str(content))

                    res = self.generateToots.gen_msg(content) # 回答文生成

                    self.mstdn_procedure.do_toot(res, id, st, visibility) # トゥート

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

    def do_toot(self, response, id, st, visibility_param):
        """トゥート処理
            生成文書を編集し、トゥートする。
            Args:
                response:生成分
                id:Mastodon User ID
                st:status
        """
        try:
            response = str(response).replace('@', '＠') # 対象者以外へのリプライ防止

            if response == 'None':
                self.mastodon.status_post('予期せぬエラーの発生。強制終了します。', visibility = 'unlisted') # bot同士の会話、予期せぬエラーでの暫定対応策
                exit()

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