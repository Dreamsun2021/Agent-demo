# skills/code_skill.py
import sys
import io
import traceback
import threading
import os
from config import CODE_EXECUTION_MODE, EXTENDED_MODULES, WORKSPACE_DIR
from logger import logger

# ───────────── 安全策略 ─────────────
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
    """根据当前配置构建安全的全局命名空间"""
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

def execute_python(code: str) -> str:
    """在沙箱中执行 Python 代码，返回输出。"""
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    result = ""
    exc_info = None

    def run_code():
        nonlocal result, exc_info
        # 切换到统一工作目录
        old_cwd = os.getcwd()
        try:
            try:
                os.chdir(WORKSPACE_DIR)
            except Exception:
                pass

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
                    # exec 不直接产生结果，结果已通过 print 输出到 stdout
                    result = ""  # 确保 result 有值，避免 None
            except Exception:
                exc_info = traceback.format_exc()
        finally:
            # 恢复原工作目录
            try:
                os.chdir(old_cwd)
            except Exception:
                pass

    thread = threading.Thread(target=run_code, daemon=True)
    thread.start()
    thread.join(timeout=EXEC_TIMEOUT)

    sys.stdout = old_stdout
    sys.stderr = old_stderr

    output = stdout_capture.getvalue()
    errors = stderr_capture.getvalue()

    # 处理超时
    if thread.is_alive():
        return f"错误：代码执行超时（超过 {EXEC_TIMEOUT} 秒）"

    # 处理异常
    if exc_info:
        return f"执行异常：\n{exc_info}"

    # 合并输出
    final_output = (output + errors + result).strip()
    if len(final_output) > MAX_OUTPUT:
        final_output = final_output[:MAX_OUTPUT] + "\n...（输出被截断）"
    return final_output or "代码执行完成，无输出。"


# ───────────── 工具注册 ─────────────
CODE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": (
                "执行 Python 代码并返回输出。可用于计算、数据处理、文本分析等。"
                "在扩展模式下，你可以使用 math, random, json, datetime, re, collections, itertools, statistics, string 等常用标准库。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要执行的 Python 代码字符串"
                    }
                },
                "required": ["code"]
            }
        }
    }
]

CODE_FUNCTIONS = {
    "execute_python": execute_python
}