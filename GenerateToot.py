"""GenerateToot.py
    OpenAI APIを用いて、質問に対する返答を生成する。
"""
import asyncio

import openai


class GenerateToots:
    """GenerateToots
        APIに質問文を投げかけて、トゥートの生成を行う。
    """
    def __init__(self, logger, initValues):
        self.logger = logger
        self.initValues = initValues
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
            self.logger.info("OpenAIインスタンス化")
            openAiInstance = openai.ChatCompletion.create(
                model=self.initValues.chatGPT_model,
                temperature=self.initValues.temperature,
                messages=[{"role": "system", "content": self.initValues.role_system_content},
                          {"role": "user","content": content}]
            )

            response = openAiInstance.choices[0].message.content
            self.logger.info("生成文：" + response)
            
            return str(response)

        except Exception as e:
            self.logger.critical("文書生成に関してエラーが発生しました。" + str(e))
            return "chatGPTでエラーが発生しました。"
    
    async def process_wait(self, content):
        """タイムアウトエラー処理
            規定時間以内に応答しない場合、タイムアウトエラーとする。
            Args:
                content:リプライ
        """        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(loop.run_in_executor(None, self.gen_msg, content), timeout=self.initValues.timeout_interval)
            return result

        except asyncio.TimeoutError:
            # Timeoutが発生したとき
            self.logger.critical("タイムアウトエラー")
            return "タイムアウトエラー。しばらく経ってから再度投稿してください。"