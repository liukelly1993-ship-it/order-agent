from pathlib import Path

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from agent.tools.tool_mysql import search_dishes

# utils/agent_util.py → 上两级 = 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_agent():
    """构建并返回餐厅智能助手 Agent

    - 模型: deepseek-v4-flash
    - 工具: search_dishes
    - 系统提示词: 读取 agent/prompt/prompt.txt
    - 存储: InMemorySaver (todo 可改成 pg 存储)
    """
    checkpointer = InMemorySaver()
    model = init_chat_model('deepseek-v4-flash')
    tools = [search_dishes]
    with open(str(PROJECT_ROOT / 'agent' / 'prompt' / 'prompt.txt'), 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
        checkpointer=InMemorySaver()  # todo 可改成pg存储
    )
    return agent
