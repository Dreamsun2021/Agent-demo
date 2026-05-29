# config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# ========== 大模型配置 ==========
MODEL_NAME = "deepseek-chat"

# ========== SMTP 配置（非敏感部分） ==========
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# ========== 密钥与敏感信息（从环境变量读取） ==========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")
# ========== Python 代码执行权限 ==========
# 可选值：
#   "safe"      - 仅限基础内置函数，禁止任何模块导入或文件 IO（默认）
#   "extended"  - 允许导入常用安全标准库（如 math, random, json, datetime 等）
#   "unsafe"    - 完全开放，允许任意导入和文件读写（仅限完全受信任的本地环境！）
CODE_EXECUTION_MODE = "unsafe"  # 根据需要修改

# 在 extended 模式下额外允许的模块白名单
EXTENDED_MODULES = [
    "math", "random", "json", "datetime", "re",
    "collections", "itertools", "statistics", "string",
    "fractions", "decimal", "typing", "textwrap", "hashlib"
]

# 工作目录，file_skill 和 code_skill 均使用此根目录
WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# ========== 提示词加载 ==========
def load_system_prompt() -> str:
    """从 prompts/system_prompt.txt 读取系统提示词"""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

SYSTEM_PROMPT = load_system_prompt()