# agent/executor.py
import json

import logger
from logger import logger
from skills import get_tool_function_map


class Executor:
    """负责执行工具调用，并返回对应的消息片段。"""

    def __init__(self):
        self.function_map = get_tool_function_map()  # 获取所有工具函数

    def execute_tools(self, tool_calls) -> tuple:
        """
        执行 tool_calls 并返回：
        - assistant_msg: 包含 tool_calls 的 assistant 消息字典
        - tool_msgs: 包含工具执行结果的 tool 消息列表
        """
        # 构建 assistant 消息（记录将要调用的工具）
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": []
        }
        for tc in tool_calls:
            assistant_msg["tool_calls"].append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            })

        # 执行工具，收集结果
        tool_msgs = []
        for tc in tool_calls:
            func_name = tc.function.name
            func_args = json.loads(tc.function.arguments)
            func = self.function_map[func_name]

            # 在 execute_tools 方法内替换 print
            logger.info(f"调用工具: {func_name}({func_args})")

            result = func(**func_args)

            tool_msgs.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })

        return assistant_msg, tool_msgs