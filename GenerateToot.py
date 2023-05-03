"""GenerateToot.py
    OpenAI APIを用いて、質問に対する返答を生成する。
"""
import asyncio
import openai
import time

class GenerateToots:
    """GenerateToots
        APIに質問文を投げかけて、トゥートの生成を行う。
    """
    def __init__(self, logger, initValues):
        self.logger = logger
        self.initValues = initValues
        openai.api_key = str(initValues.chatgpt_api_key)

    async def gen_msg(self, content):
        """レスポンス生成
            OpenAI APIを用いて、返答生成
            Args:
                content:リプライ
            Returns:
                response:返答
        """
        try:
            # OpenAIインスタンス化
            self.logger.info("OpenAIインスタンス化")
            openAiInstance = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                "role": "user",
                "content": content
                }]
            )

            response = openAiInstance.choices[0].message.content
            self.logger.info("生成文：" + response)
            
            return str(response)

        except Exception as e:
            self.logger.critical("文書生成に関してエラーが発生しました。" + str(e))
    
    async def process_wait(self, content):
        """タイムアウトエラー処理
            規定時間以内に応答しない場合、タイムアウトエラーとする。
            Args:
                content:リプライ
        """        
        try:
            result = await asyncio.wait_for(self.gen_msg(content), timeout=self.initValues.timeout_interval)
            return result

        except asyncio.TimeoutError:
            # Timeoutが発生したとき
            self.logger.critical("タイムアウトエラー")
            return "タイムアウトエラー"