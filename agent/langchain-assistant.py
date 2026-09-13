import uuid
from mimetypes import init
from pathlib import Path

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

ROOT_PATH = Path(__file__).parent.parent

def get_agent():
    checkpointer = InMemorySaver()
    model = init_chat_model('deepseek-chat')
    tools = []
    with open(str(ROOT_PATH/'agent/prompt/prompt.txt'),'r',encoding='utf-8') as f:
        system_prompt = f.read()
    agent = create_agent(
        model,
        tools,
        system_prompt=system_prompt,
        checkpointer=InMemorySaver()  # todo 可改成pg存储
    )
    return agent

if __name__ == '__main__':
    agent = get_agent()
    config = {'configurable':{'thread_id': str(uuid.uuid4())}}
    input = {'messages':[HumanMessage("你好")]}
    result = agent.invoke(config, config)
    print(result['messages'][-1].content)

