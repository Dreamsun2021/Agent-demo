# skills/utility_skill.py
from datetime import datetime
import time

def calculate(expression: str) -> str:
    """安全计算数学表达式"""
    try:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return "错误：表达式中包含非法字符。"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算出错：{str(e)}"

def get_current_time(_=None) -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def set_alarm(seconds: int, message: str) -> str:
    """倒计时提醒"""
    if seconds <= 0:
        return "闹钟时间必须大于 0 秒"
    if seconds > 3600:
        return "闹钟时间不能超过 3600 秒（1小时）"
    time.sleep(seconds)
    return f"⏰ 闹钟提醒：{message}"

def magic_cat(_=None) -> str:
    return """  /\\_/\\  
 ( o.o ) 
  > ^ <  """

UTIL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "当你需要进行数学计算时使用，支持加减乘除和括号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，例如'(3+5)*2'"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间。",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_alarm",
            "description": "设置一个倒计时提醒。指定秒数和提醒内容，时间到后会返回提醒消息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "integer", "description": "等待的秒数，例如 10 表示 10 秒后提醒"},
                    "message": {"type": "string", "description": "提醒的内容，例如 '该休息了'"}
                },
                "required": ["seconds", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "magic_cat",
            "description": "召唤一只猫咪",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

UTIL_FUNCTIONS = {
    "calculate": calculate,
    "get_current_time": get_current_time,
    "set_alarm": set_alarm,
    "magic_cat": magic_cat
}