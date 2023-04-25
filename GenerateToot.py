"""GenerateToot.py
    OpenAI APIを用いて、質問に対する返答を生成する。
"""
import Initialize
import openai

class GenerateToots:
    def __init__(self, logger, initValues):
        self.logger = logger
        openai.api_key = str(initValues.chatgpt_api_key)

    def gen_msg(self, content):
        """レスポンス生成
            OpenAI APIを用いて、返答生成
            Args:
                content:リプライ
            Returns:
                response:返答
        """
        try:
            # OpenAIインスタンス化
            openAiInstance = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                "role": "user",
                "content": content
                }]
            )
            response = openAiInstance.choices[0].message.content
            self.logger.info("生成文：")
            self.logger.info("生成文：" + response)

            return str(response)

        except Exception as e:
            Initialize.logging.critical("文書生成に関してエラーが発生しました。" + str(e))