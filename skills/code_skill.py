# skills/code_skill.py
import sys
import io
import os
import traceback
import threading
from sys import exc_info

from config import CODE_EXECUTION_MODE, EXTENDED_MODULES
from config import WORKSPACE_DIR

SAFE_BUILTINS = {
    'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool,
    'chr': chr, 'complex': complex, 'dict': dict, 'divmod': divmod,
    'enumerate': enumerate, 'filter': filter, 'float': float, 'format': format,
    'frozenset': frozenset, 'getattr': getattr, 'hasattr': hasattr,
    'hash': hash, 'hex': hex, 'int': int, 'isinstance': isinstance,
    'issubclass': issubclass, 'iter': iter, 'len': len, 'list': list,
    'map': map, 'max': max, 'min': min, 'next': next, 'object': object,
    'oct': oct, 'ord': ord, 'pow': pow, 'print': print, 'range': range,
    'repr': repr, 'reversed': reversed, 'round': round, 'set': set,
    'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum,
    'tuple': tuple, 'type': type, 'zip': zip,
}

EXEC_TIMEOUT = 5
MAX_OUTPUT = 3000

def _build_globals() -> dict:
    if CODE_EXECUTION_MODE == "unsafe":
        g = {"__builtins__": __builtins__}
        g.update({'open': open, 'os': __import__('os'), 'sys': sys})
        return g
    g = {"__builtins__": SAFE_BUILTINS}
    if CODE_EXECUTION_MODE == "extended":
        for mod_name in EXTENDED_MODULES:
            try:
                mod = __import__(mod_name)
                g[mod_name] = mod
            except ImportError:
                pass
    return g

def _execute_raw(code: str) -> dict:
    """
    执行代码并返回捕获的输出和异常信息。
    返回：
    {
        "stdout": str,
        "stderr": str,
        "result": str,
        "error": str or None,
        "timed_out": bool
    }
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_capture, stderr_capture

    result = ""
    exc_info = None
    error = None
    timed_out = False

    def run_code():
        nonlocal result, exc_info
        # 保存当前工作目录，并切换到统一的工作目录
        old_cwd = os.getcwd()
        try:
            os.chdir(WORKSPACE_DIR)
        except Exception:
            pass  # 若目录不存在，容错继续

        try:
            # 先尝试作为表达式求值
            try:
                compiled = compile(code, '<string>', 'eval')
                safe_globals = _build_globals()
                exec_result = eval(compiled, safe_globals, {})
                result = repr(exec_result)
            except SyntaxError:
                # 不是表达式，按 exec 执行
                compiled = compile(code, '<string>', 'exec')
                safe_globals = _build_globals()
                exec(compiled, safe_globals, {})
        except Exception:
            exc_info = traceback.format_exc()
        finally:
            # 恢复原工作目录
            try:
                os.chdir(old_cwd)
            except Exception:
                pass

# ───────────── 旧接口：简洁版 ─────────────
def execute_python(code: str) -> str:
    """执行 Python 代码并返回简短输出（兼容原有工具）"""
    exec_result = _execute_raw(code)
    if exec_result["timed_out"]:
        return f"错误：代码执行超时（超过 {EXEC_TIMEOUT} 秒）"
    if exec_result["error"]:
        return f"执行异常：\n{exec_result['error']}"
    output = (exec_result["stdout"] + exec_result["stderr"] + exec_result["result"]).strip()
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + "\n...（输出被截断）"
    return output or "代码执行完成，无输出。"

# ───────────── 新接口：详细调试版 ─────────────
def execute_python_debug(code: str) -> str:
    """
    执行 Python 代码并返回完整的控制台内容（成功或报错），
    包含标准输出、标准错误、表达式结果、异常信息和超时状态。
    以便 Agent 根据错误修改代码并重试。
    """
    exec_result = _execute_raw(code)
    parts = []

    # 状态指示
    if exec_result["timed_out"]:
        parts.append(f"[超时] 代码执行超过 {EXEC_TIMEOUT} 秒")
    elif exec_result["error"]:
        parts.append("[失败] 代码执行出错")
    else:
        parts.append("[成功] 代码执行完成")

    # 标准输出
    if exec_result["stdout"].strip():
        parts.append("--- 标准输出 ---\n" + exec_result["stdout"].rstrip("\n"))

    # 标准错误
    if exec_result["stderr"].strip():
        parts.append("--- 标准错误 ---\n" + exec_result["stderr"].rstrip("\n"))

    # 表达式结果
    if exec_result["result"]:
        parts.append("--- 返回值 ---\n" + exec_result["result"])

    # 异常信息
    if exec_result["error"]:
        parts.append("--- 异常详情 ---\n" + exec_result["error"].rstrip("\n"))

    final = "\n".join(parts)
    if len(final) > MAX_OUTPUT:
        final = final[:MAX_OUTPUT] + "\n...（输出被截断）"
    return final


# ───────────── 工具注册 ─────────────
CODE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "执行 Python 代码并返回输出。适合简单计算或不需要调试的情况。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python 代码"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_debug",
            "description": (
                "执行 Python 代码并返回完整的控制台内容（标准输出、错误信息、返回值、异常详情等），"
                "帮助定位代码错误并修复。当需要编写复杂代码或之前执行出错时，推荐使用此工具。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python 代码"}
                },
                "required": ["code"]
            }
        }
    }
]

CODE_FUNCTIONS = {
    "execute_python": execute_python,
    "execute_python_debug": execute_python_debug
}