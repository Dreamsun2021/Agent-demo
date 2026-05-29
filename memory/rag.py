# memory/rag.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

_embed_model = None
_client = None

def get_embed_model():
    """获取 embedding 模型（懒加载）"""
    global _embed_model
    if _embed_model is None:
        try:
            _embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"加载 embedding 模型失败: {e}")
            raise
    return _embed_model

def get_chroma_client():
    """获取 Chroma 客户端（懒加载）"""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path="./chroma_db")
    return _client

def get_or_create_collection(name: str):
    """获取或创建指定名称的集合"""
    return get_chroma_client().get_or_create_collection(name)