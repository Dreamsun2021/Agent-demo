# agent/planner.py
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_NAME
from skills import get_all_tools
from logger import logger

class Planner:
    """负责与大模型交互，根据上下文和可用工具生成决策。"""

    def __init__(self, api_key: str = None, model: str = None):
        self.client = OpenAI(
            api_key=api_key or OPENAI_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=60.0,
            max_retries=1,
        )
        self.model = model or MODEL_NAME
        self.tools = get_all_tools()  # 从 skills 包加载所有工具描述

    def decide(self, messages: list) -> dict:
        """
        调用 LLM，返回决策（非流式）。
        返回格式：
        {
            "type": "tool_call",
            "tool_calls": [...]   # 原始 tool_calls 对象
        }
        或
        {
            "type": "final_answer",
            "content": "..."
        }
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if message.tool_calls:
            return {"type": "tool_call", "tool_calls": message.tool_calls}
        else:
            return {"type": "final_answer", "content": message.content}

    def decide_stream(self, messages: list):
        response_stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
            stream=True,
        )
        has_tool_call = False
        try:
            for chunk in response_stream:
                delta = chunk.choices[0].delta
                if getattr(delta, 'tool_calls', None):
                    has_tool_call = True
                    response_stream.close()
                    break
                if getattr(delta, 'content', None):
                    yield delta.content
        except Exception as e:
            logger.warning(f"流式响应处理异常: {e}")

        if has_tool_call:
            # 重新请求非流式 decide
            decision = self.decide(messages)
            logger.info(f"工具调用决策结果: {decision.get('type')} keys={list(decision.keys())}")

            if decision["type"] == "tool_call":
                # 正常情况：返回工具调用信息给调用方
                self._tool_call_result = decision
            else:
                # 异常情况：LLM 突然给了最终回答，我们直接 yield 它的内容
                logger.warning("LLM 在工具调用后返回了最终回答，将直接输出。")
                if decision.get("content"):
                    yield decision["content"]
                # 没有 tool_calls，调用方会退出工具循环，进入下一轮或结束