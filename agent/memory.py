# agent/memory.py
class Memory:
    """管理对话历史（短期记忆），并可注入长期记忆上下文"""

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
        self.history = []  # 只保存短期消息
        self.long_term_context = ""  # 当前对话相关的长期记忆文本

    def set_long_term_context(self, context: str):
        """在系统提示词前插入长期记忆上下文"""
        self.long_term_context = context

    def get_messages(self) -> list:
        """返回完整消息列表，包含长期记忆（放在 system prompt 后）"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if self.long_term_context:
            # 将长期记忆作为额外的系统信息插入
            messages.append({"role": "system", "content": f"[相关长期记忆]\n{self.long_term_context}"})
        messages.extend(self.history)
        return messages

    # ---- 原有的 add_message, add_user_message, add_assistant_message, add_tool_result, clear 保持不变 ----
    def add_message(self, role: str, content: str = None, tool_calls: list = None,
                    tool_call_id: str = None, name: str = None):
        msg = {"role": role}
        if content is not None:
            msg["content"] = content
        if tool_calls is not None:
            msg["tool_calls"] = tool_calls
        if tool_call_id is not None:
            msg["tool_call_id"] = tool_call_id
        if name is not None:
            msg["name"] = name
        self.history.append(msg)

    def add_user_message(self, content: str):
        self.add_message("user", content=content)

    def add_assistant_message(self, content: str = None, tool_calls: list = None):
        self.add_message("assistant", content=content, tool_calls=tool_calls)

    def add_tool_result(self, tool_call_id: str, result: str):
        self.add_message("tool", content=result, tool_call_id=tool_call_id)

    def clear(self):
        self.history.clear()