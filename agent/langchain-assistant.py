import asyncio
import uuid
import time

from langchain_core.messages import HumanMessage

from utils.agent_util import get_agent


async def test_agent():
    agent = await get_agent()
    config = {"configurable": {"thread_id": "001"}}

    res = await agent.ainvoke({
        "messages": [
            {"role": "user", "content": "我现在在中山公园，帮我规划路线如何去你们餐厅？"}
        ]
    }, config=config)
    print(res["messages"][-1].content)

if __name__ == '__main__':
    '''
    agent = get_agent()
    thread_id = str(uuid.uuid4())
    # todo thread_id应该是传进来的, 需要添加到数据库中做唯一索引,做幂等
    # thread_id = '8af6020c-f549-4421-ad4a-33c81e8a9d3bxxxx132123xxxxx22'
    config = {'configurable': {'thread_id':thread_id}}
    print(thread_id)
    # input = {'messages': [HumanMessage("你好,你们餐厅有什么特色菜?")]}
    # input = {'messages': [HumanMessage("我喜欢吃辣的，帮我推荐川菜！")]}

    # input = {'messages': [HumanMessage("帮我预约一下明天上午的餐桌，10个人，2个小孩，到店时间下午6点，喜欢靠窗的座位，主菜偏好是红烧肉，备注是吃辣的。今天的时间："+time
    #                                    .strftime("%Y-%m-%d", time.localtime()))]}
    input = {'messages': [HumanMessage('我确认上面的预订，请帮我确认一下。')]}

    result = agent.invoke(input, config)

    print(result)
    print(result['messages'][-1].content)
    # '''
    asyncio.run(test_agent())
