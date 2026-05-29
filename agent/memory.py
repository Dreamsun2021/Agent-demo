# agent/memory.py

class Memory:
    """管理对话历史（短期记忆），未来可扩展长期记忆和 RAG 检索。"""

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
        self.history = []  # 存储所有对话消息（不含 system）

    def add_message(self, role: str, content: str = None, tool_calls: list = None,
                    tool_call_id: str = None, name: str = None):
        """添加一条消息到记忆"""
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

    def get_messages(self) -> list:
        """返回完整的消息列表，前置 system prompt"""
        return [{"role": "system", "content": self.system_prompt}] + self.history

    def clear(self):
        self.history.clear()