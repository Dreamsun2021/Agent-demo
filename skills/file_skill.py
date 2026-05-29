# skills/file_skill.py
import os
import shutil

# 定义文件操作的安全根目录（当前工作目录下的 workspace 文件夹）
SAFE_ROOT = os.path.join(os.getcwd(), "workspace")


def _safe_path(file_path: str) -> str:
    """将用户提供的相对路径转换为绝对路径，并确保在 SAFE_ROOT 内"""
    safe_root = os.path.abspath(SAFE_ROOT)
    target = os.path.abspath(os.path.join(safe_root, file_path))
    if not target.startswith(safe_root):
        raise ValueError(f"路径 '{file_path}' 超出了允许的工作目录")
    return target


def _ensure_dir_exists(path: str):
    """确保目标路径的父目录存在（写操作前调用）"""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


# ────────────── 原有功能 ──────────────
def read_file(file_path: str) -> str:
    """读取指定文件的内容，若截断会标注总长度"""
    try:
        path = _safe_path(file_path)
        if not os.path.isfile(path):
            return f"错误：文件 '{file_path}' 不存在。"
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        total_len = len(content)
        if total_len > 6000:
            content = content[:6000] + f"\n... [内容已截断，文件总长度：{total_len} 字符，仅显示前 6000 字符]"
        return content
    except Exception as e:
        return f"读取文件失败：{str(e)}"

def write_file(file_path: str, content: str) -> str:
    """写入内容到文件，覆盖原有内容；自动创建父目录"""
    try:
        path = _safe_path(file_path)
        _ensure_dir_exists(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件 '{file_path}' 写入成功。"
    except Exception as e:
        return f"写入文件失败：{str(e)}"


def list_files(directory: str = "") -> str:
    """列出指定目录下的文件和子目录（根目录为 ''）"""
    try:
        path = _safe_path(directory)
        if not os.path.isdir(path):
            return f"错误：目录 '{directory}' 不存在。"
        items = os.listdir(path)
        if not items:
            return "目录为空。"
        files = []
        dirs = []
        for item in items:
            full = os.path.join(path, item)
            if os.path.isdir(full):
                dirs.append(item + "/")
            else:
                files.append(item)
        result = ""
        if files:
            result += "文件：\n" + "\n".join(files)
        if dirs:
            if result:
                result += "\n\n"
            result += "目录：\n" + "\n".join(dirs)
        return result or "目录为空。"
    except Exception as e:
        return f"列出文件失败：{str(e)}"


# ────────────── 新增功能 ──────────────
def delete_file(file_path: str) -> str:
    """删除指定的文件（不支持删除非空目录）"""
    try:
        path = _safe_path(file_path)
        if not os.path.exists(path):
            return f"错误：路径 '{file_path}' 不存在。"
        if os.path.isdir(path):
            # 为了保护数据，默认不允许直接删除目录（即使为空也可选择性开启）
            return f"错误：'{file_path}' 是一个目录。请使用专门的删除目录功能（本工具暂不支持删除目录）。"
        os.remove(path)
        return f"文件 '{file_path}' 已删除。"
    except Exception as e:
        return f"删除失败：{str(e)}"


def move_file(source: str, destination: str) -> str:
    """
    移动或重命名文件/目录。
    若目标已存在，则操作失败（不会覆盖）。
    """
    try:
        src_path = _safe_path(source)
        dst_path = _safe_path(destination)

        if not os.path.exists(src_path):
            return f"错误：源路径 '{source}' 不存在。"
        if os.path.exists(dst_path):
            return f"错误：目标 '{destination}' 已存在，操作被拒绝。"

        # 确保目标父目录存在
        _ensure_dir_exists(dst_path)

        shutil.move(src_path, dst_path)
        return f"'{source}' 已成功移动到 '{destination}'。"
    except Exception as e:
        return f"移动/重命名失败：{str(e)}"


def create_directory(directory: str) -> str:
    """创建新目录（支持多级目录）"""
    try:
        path = _safe_path(directory)
        if os.path.exists(path):
            return f"错误：'{directory}' 已存在。"
        os.makedirs(path, exist_ok=True)
        return f"目录 '{directory}' 创建成功。"
    except Exception as e:
        return f"创建目录失败：{str(e)}"


# ────────────── 工具描述和注册 ──────────────
FILE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取 workspace 中的文件内容。参数为相对于 workspace 的路径。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件相对路径，例如 'notes.txt' 或 'subdir/report.md'"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "将内容写入 workspace 中的文件，会覆盖已有文件。自动创建父目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件相对路径，例如 'output.txt'"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文本内容"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出 workspace 目录中的文件和子目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要列出的目录，留空表示根目录"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "删除 workspace 中指定的文件（不能删除目录）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要删除的文件相对路径"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "移动或重命名文件/目录。源路径和目标路径都必须在 workspace 内。如果目标已存在，操作会失败。",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "源文件/目录的相对路径"
                    },
                    "destination": {
                        "type": "string",
                        "description": "目标路径（相对）"
                    }
                },
                "required": ["source", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "在 workspace 中创建新目录（支持多级）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要创建的目录相对路径"
                    }
                },
                "required": ["directory"]
            }
        }
    }
]

FILE_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "delete_file": delete_file,
    "move_file": move_file,
    "create_directory": create_directory
}