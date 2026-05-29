# memory/long_term.py
import datetime
import logging
from memory.rag import get_embed_model, get_or_create_collection

logger = logging.getLogger(__name__)

COLLECTION_NAME = "long_term_memory"


def add_memory(text: str, metadata: dict = None) -> str:
    """
    将一段文本存入长期记忆，并返回记忆 ID。
    如果 metadata 为 None，则自动添加时间戳。
    """
    if metadata is None:
        metadata = {}
    metadata["timestamp"] = datetime.datetime.now().isoformat()

    try:
        model = get_embed_model()
        collection = get_or_create_collection(COLLECTION_NAME)
        embedding = model.encode(text).tolist()
        mem_id = str(datetime.datetime.now().timestamp())
        collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[mem_id]
        )
        logger.info(f"记忆已存储: {mem_id}")
        return mem_id
    except Exception as e:
        logger.error(f"添加长期记忆失败: {e}")
        raise


def search_memory(query: str, top_k: int = 3) -> list:
    """
    根据查询文本检索最相关的长期记忆，返回文档内容列表。
    如果出错，返回空列表。
    """
    try:
        model = get_embed_model()
        collection = get_or_create_collection(COLLECTION_NAME)
        query_embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        docs = results.get("documents", [[]])[0]
        return docs
    except Exception as e:
        logger.warning(f"长期记忆搜索失败: {e}")
        return []


def get_recent_memories(n: int = 5) -> list:
    """
    获取最近添加的 n 条记忆，返回文档内容列表。
    如果出错，返回空列表。
    """
    try:
        collection = get_or_create_collection(COLLECTION_NAME)
        all_items = collection.get()
        if not all_items or not all_items["ids"]:
            return []

        # 按 ID（时间戳字符串）降序排序
        sorted_ids = sorted(all_items["ids"], reverse=True)[:n]
        docs = []
        for id_ in sorted_ids:
            # 找到对应的文档
            idx = all_items["ids"].index(id_)
            docs.append(all_items["documents"][idx])
        return docs
    except Exception as e:
        logger.warning(f"获取最近记忆失败: {e}")
        return []