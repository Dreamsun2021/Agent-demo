# agent/base.py
from .memory import Memory
from .planner import Planner
from .executor import Executor
from config import SYSTEM_PROMPT
from logger import logger
from memory.long_term import search_memory, add_memory


class Agent:
    """组合记忆、规划器、执行器的智能体，对外提供统一的 chat 和 chat_stream 接口。"""

    def __init__(self, api_key: str = None, model: str = None):
        self.memory = Memory(system_prompt=SYSTEM_PROMPT)
        self.planner = Planner(api_key=api_key, model=model)
        self.executor = Executor()

    # ────────────── 非流式对话 ──────────────
    def chat(self, user_input: str) -> str:
        # 1. 检索相关长期记忆并注入上下文
        relevant_docs = search_memory(user_input, top_k=3)
        if relevant_docs:
            context = "\n".join(relevant_docs)
            self.memory.set_long_term_context(context)
        else:
            self.memory.set_long_term_context("")

        self.memory.add_user_message(user_input)
        messages = self.memory.get_messages()

        while True:
            decision = self.planner.decide(messages)
            if decision["type"] == "final_answer":
                final_answer = decision["content"]
                self.memory.add_assistant_message(content=final_answer)

                # 2. 自动将本轮交互存入长期记忆
                summary = f"用户问: {user_input}\n助手答: {final_answer}"
                add_memory(summary)

                return final_answer

            elif decision["type"] == "tool_call":
                tool_calls = decision["tool_calls"]
                assistant_msg, tool_msgs = self.executor.execute_tools(tool_calls)
                self.memory.add_assistant_message(
                    content=assistant_msg.get("content"),
                    tool_calls=assistant_msg.get("tool_calls"),
                )
                for tool_msg in tool_msgs:
                    self.memory.add_tool_result(
                        tool_call_id=tool_msg["tool_call_id"],
                        result=tool_msg["content"],
                    )
                messages = self.memory.get_messages()

            else:
                logger.error(f"Planner 返回了未知的决策类型: {decision}")
                return "抱歉，内部决策出现异常，请稍后重试。"

    # ────────────── 流式对话 ──────────────
    def chat_stream(self, user_input: str):
        # 1. 检索相关长期记忆并注入上下文
        relevant_docs = search_memory(user_input, top_k=3)
        if relevant_docs:
            context = "\n".join(relevant_docs)
            self.memory.set_long_term_context(context)
        else:
            self.memory.set_long_term_context("")

        self.memory.add_user_message(user_input)
        messages = self.memory.get_messages()

        while True:
            gen = self.planner.decide_stream(messages)
            text_buffer = ""
            for token in gen:
                text_buffer += token

            # 检查是否有工具调用
            if hasattr(self.planner, "_tool_call_result"):
                tool_decision = self.planner._tool_call_result
                del self.planner._tool_call_result

                if not isinstance(tool_decision, dict) or "tool_calls" not in tool_decision:
                    logger.error(f"tool_decision 格式错误: {tool_decision}")
                    yield "（内部错误：工具调用数据异常）"
                    return

                try:
                    assistant_msg, tool_msgs = self.executor.execute_tools(
                        tool_decision["tool_calls"]
                    )
                except Exception as e:
                    logger.error(f"工具执行失败: {e}", exc_info=True)
                    yield f"（工具执行出错：{e}）"
                    return

                self.memory.add_assistant_message(
                    content=assistant_msg.get("content"),
                    tool_calls=assistant_msg.get("tool_calls"),
                )
                for tm in tool_msgs:
                    self.memory.add_tool_result(
                        tool_call_id=tm["tool_call_id"],
                        result=tm["content"],
                    )
                messages = self.memory.get_messages()
                continue
            else:
                # 没有工具调用，最终答案已完整收集
                self.memory.add_assistant_message(content=text_buffer)

                # 2. 自动将本轮交互存入长期记忆
                summary = f"用户问: {user_input}\n助手答: {text_buffer}"
                add_memory(summary)

                # 逐字符流式输出最终回答
                for token in text_buffer:
                    yield token
                return