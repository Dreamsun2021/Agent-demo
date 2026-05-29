# memory/long_term.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import datetime

# 使用本地轻量 embedding 模型（首次运行会自动下载）
EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')

# Chroma 客户端（数据保存在项目根目录的 chroma_db 文件夹）
client = chromadb.PersistentClient(path="./chroma_db")

# 获取或创建集合（长期记忆）
collection = client.get_or_create_collection("long_term_memory")


def add_memory(text: str, metadata: dict = None) -> str:
    """将一段文本存入长期记忆，返回记忆 ID"""
    if metadata is None:
        metadata = {}
    metadata["timestamp"] = datetime.datetime.now().isoformat()

    # 生成向量
    embedding = EMBED_MODEL.encode(text).tolist()

    # 使用时间戳作为 ID（生产环境可用 UUID）
    mem_id = str(datetime.datetime.now().timestamp())
    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[mem_id]
    )
    return mem_id


def search_memory(query: str, top_k: int = 3) -> list:
    """根据查询文本检索最相关的长期记忆，返回文档内容列表"""
    query_embedding = EMBED_MODEL.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    # 提取 documents 部分
    docs = results.get("documents", [[]])[0]
    return docs


def get_recent_memories(n: int = 5) -> list:
    """获取最近添加的 n 条记忆"""
    all_items = collection.get()
    if not all_items or not all_items["ids"]:
        return []
    # 按时间戳排序（id 是时间戳）
    sorted_ids = sorted(all_items["ids"], reverse=True)[:n]
    docs = []
    for id_ in sorted_ids:
        idx = all_items["ids"].index(id_)
        docs.append(all_items["documents"][idx])
    return docs