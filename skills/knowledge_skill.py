# skills/knowledge_skill.py
import os
import re
import logging
from memory.rag import get_embed_model, get_or_create_collection

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_base"
CHUNK_SIZE = 500  # 每个文本块的大小（字符数）

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list:
    """按段落和固定长度分割文本"""
    # 先按空行分段，再在段落内按固定大小切割
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            # 超长段落进一步切割（尽量在句子边界切）
            start = 0
            while start < len(para):
                end = start + chunk_size
                if end >= len(para):
                    chunks.append(para[start:])
                    break
                # 尝试在句子结尾切割
                split_pos = para.rfind('。', start, end)
                if split_pos == -1:
                    split_pos = para.rfind('.', start, end)
                if split_pos == -1:
                    split_pos = end  # 找不到句子边界就直接切
                chunks.append(para[start:split_pos+1])
                start = split_pos + 1
    return chunks

def add_document(file_path: str) -> str:
    """
    将文档加载、分块并存入知识库。
    支持 .txt, .md, .pdf (需要安装 pypdf 或 PyPDF2)。
    """
    try:
        if not os.path.isfile(file_path):
            return f"错误：文件 '{file_path}' 不存在。"
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt' or ext == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif ext == '.pdf':
            try:
                from pypdf import PdfReader
            except ImportError:
                return "错误：读取 PDF 需要 pypdf 库。请运行 `pip install pypdf`。"
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            return f"不支持的文件格式：{ext}。请提供 .txt, .md 或 .pdf 文件。"

        if not text.strip():
            return "文件中没有可提取的文本内容。"

        # 分块
        chunks = _chunk_text(text)
        if not chunks:
            return "文件内容为空，无法添加。"

        # 存入向量库
        model = get_embed_model()
        collection = get_or_create_collection(COLLECTION_NAME)
        embeddings = model.encode(chunks).tolist()
        metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]
        ids = [f"{file_path}_{i}" for i in range(len(chunks))]
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        return f"成功添加文档 '{file_path}'（共 {len(chunks)} 个片段）。"
    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        return f"添加文档失败：{str(e)}"

def search_knowledge(query: str, top_k: int = 3) -> str:
    """从知识库中检索与查询相关的文本片段"""
    try:
        model = get_embed_model()
        collection = get_or_create_collection(COLLECTION_NAME)
        query_embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        docs = results.get("documents", [[]])[0]
        if not docs:
            return "未找到相关知识。"
        return "\n---\n".join(docs)
    except Exception as e:
        logger.error(f"知识检索失败: {e}")
        return f"检索失败：{str(e)}"

# 工具描述
KNOWLEDGE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_document",
            "description": "将本地文档（.txt, .md, .pdf）内容添加到知识库中，使其内容可被搜索。参数为文件的绝对路径或相对于 workspace 的路径。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径，例如 'notes.txt' 或 'C:/docs/manual.pdf'"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "从已添加的知识库中搜索相关内容，并返回最相关的文本片段。适用于回答基于文档的问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，例如 '什么是面向对象编程'"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

KNOWLEDGE_FUNCTIONS = {
    "add_document": add_document,
    "search_knowledge": search_knowledge
}