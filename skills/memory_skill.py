# skills/memory_skill.py
from memory.long_term import add_memory, search_memory, get_recent_memories

def remember_fact(fact: str) -> str:
    """让 Agent 主动记住一条信息"""
    mem_id = add_memory(fact)
    return f"已记住：{fact} (ID: {mem_id})"

def recall_memory(query: str) -> str:
    """Agent 主动回忆相关信息"""
    results = search_memory(query, top_k=3)
    if not results:
        return "没有找到相关记忆。"
    # 将结果格式化为文本列表
    formatted = "\n".join([f"- {r}" for r in results])
    return f"回忆到的内容：\n{formatted}"

def list_recent_memories(n: int = 5) -> str:
    """列出最近的记忆条目"""
    memories = get_recent_memories(n)
    if not memories:
        return "长期记忆为空。"
    formatted = "\n".join([f"- {m}" for m in memories])
    return f"最近的 {n} 条记忆：\n{formatted}"

# 工具描述与注册
MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "记住一条重要信息或用户偏好，存入长期记忆。例如用户的名字、喜好等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "要记住的事实或用户偏好，例如 '用户名字叫张三'"
                    }
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "从长期记忆中搜索相关信息。当需要回忆用户之前说过的话或存储的信息时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，例如 '用户喜欢的颜色'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_recent_memories",
            "description": "列出最近存入长期记忆的条目。",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "要列出的条目数量，默认为 5"
                    }
                },
                "required": []
            }
        }
    }
]

MEMORY_FUNCTIONS = {
    "remember_fact": remember_fact,
    "recall_memory": recall_memory,
    "list_recent_memories": list_recent_memories
}