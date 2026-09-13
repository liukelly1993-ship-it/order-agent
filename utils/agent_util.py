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
# Bugfix #4: 原版 conn 是裸局部变量,get_agent() 返回后没人持有 PG 连接,
# 进程退出时依赖 GC 关闭,不一定可靠;且若将来重建 agent,旧 conn 无法释放.
# 改为模块级变量持有,并新增 close_agent() 入口,供 FastAPI lifespan/shutdown
# 显式释放连接与清空单例,避免泄漏.
_pg_conn: psycopg.AsyncConnection | None = None


async def get_agent():
    """构建并返回餐厅智能助手 Agent

    - 模型: deepseek-v4-flash
    - 工具: search_dishes / user_favorite_dishes / make_reservation
    - 系统提示词: 读取 agent/prompt/prompt.txt
    - 存储: PostgresSaver,持久化到 PG(连接串从 .env 的 LANGGRAPH_PG_URL 读)
    """
    # 直接建连接 + 传给 saver,绕开 from_conn_string 的 context manager
    # (因为 get_agent() 要 return agent,不能让 with 块提前关闭连接)
    global agent, _pg_conn  # todo 加double check lock
    if agent is None:
        _pg_conn = await psycopg.AsyncConnection.connect(os.getenv('LANGGRAPH_PG_URL'), autocommit=True)
        checkpointer = AsyncPostgresSaver(conn=_pg_conn)

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


async def close_agent():
    """FastAPI lifespan/shutdown 时调用,显式释放 PG 连接与清空 agent 单例.

    Bugfix #4 配套: 不调用也没问题(进程退出 GC 会兜底),但显式关闭更可控,
    也能让 PG 端立刻收到 FIN 而不是等到 socket 超时.
    """
    global agent, _pg_conn
    agent = None
    if _pg_conn is not None:
        await _pg_conn.close()
        _pg_conn = None
