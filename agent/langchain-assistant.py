import uuid

from langchain_core.messages import HumanMessage

from utils.agent_util import get_agent


if __name__ == '__main__':
    agent = get_agent()
    config = {'configurable': {'thread_id': str(uuid.uuid4())}}
    input = {'messages': [HumanMessage("你好,你们餐厅有什么特色菜?")]}
    result = agent.invoke(input, config)
    print(result)
    print(result['messages'][-1].content)
