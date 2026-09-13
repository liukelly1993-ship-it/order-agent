from pymilvus import MilvusClient
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
import os
from pathlib import Path
load_dotenv()

# 项目根目录: agent/tools/tool_milvus.py → 上三级 = 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# 连接到向量库
def get_client():
    client = MilvusClient(uri = os.getenv('MILVUS_URI'),token  = os.getenv('MILVUS_TOKEN'))
    return client

'''
@:return 返回的是一个装着 BGE 模型的 LangChain 客户端对象
'''
def get_embedding():
    embeddings = HuggingFaceEmbeddings(
        model_name=str(PROJECT_ROOT / 'models' / 'bge-base-zh'),
        model_kwargs={
            'device': 'mps',
            'trust_remote_code': True
        },
        encode_kwargs={'normalize_embeddings': True},  # 配置ip使用 归一化,扔掉"长度"这个噪声，只留"方向"这个有效信息
    )
    return embeddings