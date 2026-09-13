import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver

from agent.tools.tool_milvus import user_favorite_dishes
from agent.tools.tool_mysql import search_dishes, make_reservation

# utils/agent_util.py → 上两级 = 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / '.env')


def get_agent():
    """构建并返回餐厅智能助手 Agent

    - 模型: deepseek-v4-flash
    - 工具: search_dishes / user_favorite_dishes / make_reservation
    - 系统提示词: 读取 agent/prompt/prompt.txt
    - 存储: PostgresSaver,持久化到 PG(连接串从 .env 的 LANGGRAPH_PG_URL 读)
    """
    # 直接建连接 + 传给 saver,绕开 from_conn_string 的 context manager
    # (因为 get_agent() 要 return agent,不能让 with 块提前关闭连接)
    conn = psycopg.connect(os.getenv('LANGGRAPH_PG_URL'), autocommit=True)
    checkpointer = PostgresSaver(conn=conn)
    checkpointer.setup()  # 首次建表,后续幂等(IF NOT EXISTS)
    model = init_chat_model('deepseek-v4-flash')
    tools = [search_dishes,user_favorite_dishes,make_reservation]
    with open(str(PROJECT_ROOT / 'agent' / 'prompt' / 'prompt.txt'), 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer
    )
    return agent
