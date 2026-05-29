# skills/shell_skill.py
import subprocess
import os
import platform

def execute_command(command: str) -> str:
    """
    执行一个 shell 命令并返回输出。
    为了安全，只允许执行白名单中的命令，且不保留交互式进程。
    """
    allowed_commands = ["dir", "echo", "date", "time", "whoami", "hostname", "ping", "ipconfig", "systeminfo", "tasklist"]
    if platform.system() != "Windows":
        allowed_commands.extend(["ls", "pwd", "uname", "whoami", "uptime"])

    # 提取第一个单词（命令名）
    cmd_name = command.strip().split()[0] if command.strip() else ""
    if cmd_name not in allowed_commands:
        return f"错误：命令 '{cmd_name}' 不在白名单中。允许的命令：{allowed_commands}"

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        if not output.strip():
            return "命令执行成功，但没有输出。"
        return output[:2000]  # 限制输出长度，防止 LLM 上下文溢出
    except subprocess.TimeoutExpired:
        return "错误：命令执行超时（30秒）。"
    except Exception as e:
        return f"命令执行失败：{str(e)}"


SHELL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "执行一个安全的 shell 命令。可用的命令包括：dir, echo, date, time, whoami, hostname, ping, ipconfig, systeminfo, tasklist, 以及 Linux 下的 ls, pwd 等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令，例如 'dir' 或 'ping localhost'"
                    }
                },
                "required": ["command"]
            }
        }
    }
]

SHELL_FUNCTIONS = {
    "execute_command": execute_command
}