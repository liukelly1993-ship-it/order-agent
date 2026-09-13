import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware, ModelRetryMiddleware
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent.tools.tool_gdmp import get_amap_mcp_tools
from agent.tools.tool_milvus import user_favorite_dishes
from agent.tools.tool_mysql import search_dishes, make_reservation

# utils/agent_util.py → 上两级 = 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / '.env')

# 模块级单例占位,get_agent() 第一次调用时填充
agent = None


async def get_agent():
    """构建并返回餐厅智能助手 Agent

    - 模型: deepseek-v4-flash
    - 工具: search_dishes / user_favorite_dishes / make_reservation
    - 系统提示词: 读取 agent/prompt/prompt.txt
    - 存储: PostgresSaver,持久化到 PG(连接串从 .env 的 LANGGRAPH_PG_URL 读)
    """
    # 直接建连接 + 传给 saver,绕开 from_conn_string 的 context manager
    # (因为 get_agent() 要 return agent,不能让 with 块提前关闭连接)
    global agent #todo 加double check lock
    if agent is None:
        conn = await psycopg.AsyncConnection.connect(os.getenv('LANGGRAPH_PG_URL'), autocommit=True)
        checkpointer = AsyncPostgresSaver(conn=conn)

        # TODO: 切换短期记忆的存储方式，比如基于Redis实现短期记忆
        #redis_client = await asyn_get_redis_client()
        #print("redis对象："+redis_client.__str__())
        #checkpointer = AsyncRedisSaver(redis_client=redis_client) #基于Redis实现长期记忆
        #await checkpointer.asetup() #初始化

        await checkpointer.setup()  # 首次建表,后续幂等(IF NOT EXISTS)
        llm = init_chat_model('deepseek-v4-flash')
        amap_mcp_tools = await  get_amap_mcp_tools()
        tools = [search_dishes,user_favorite_dishes,make_reservation] + amap_mcp_tools
        with open(str(PROJECT_ROOT / 'agent' / 'prompt' / 'prompt.txt'), 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        agent = create_agent(
            llm,
            tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,
            middleware=[

                ToolRetryMiddleware(
                    max_retries=3, # 最大重试次数
                    backoff_factor=2, # 每次重试的退避因子
                    initial_delay=1, # 初始延迟时间
                ),
                ModelRetryMiddleware(
                    max_retries=3, # 最大重试次数
                    backoff_factor=2, # 每次重试的退避因子
                    initial_delay=1, # 初始延迟时间
                ),
                # todo 异常处理...
            ]
        )
    return agent
