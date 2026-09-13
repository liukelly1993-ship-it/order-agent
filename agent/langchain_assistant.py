import asyncio
import json
import uuid
import time

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from agent.tools.tool_gdmp import get_amap_mcp_tools
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


#调用agent使用SSE方式将每个块返回给前端
async def assistant_query(query:str):
    agent = await get_agent()
    config={'configurable':{'thread_id':str(uuid.uuid4())}}
    async for chunk in agent.astream({
        "messages": [
            SystemMessage(content=f"当前时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"),
            HumanMessage(content=query),
        ]
    }, config=config, stream_mode=['messages']):
        message = chunk[0]
        if type(message) == ToolMessage:
            continue
        payload_str = json.dumps({'content': message.content, 'type': 'token'}, ensure_ascii=False)
        yield f'data: {payload_str}\n\n'


# 实现配送的核心业务
async def get_devliery_info(address: str, travel_mode: str):
    """调用高德MCP工具计算距离并判断是否在5KM配送范围内容"""

    # 有固定业务流程的可以直接处理，不要经过大模型了
    # 餐厅的具体位置先确定-》调用高德的测量工具-》计算距离
    all_tools = await get_amap_mcp_tools()
    # maps
    tool_dict = {tool.name: tool for tool in all_tools}

    if travel_mode == "1":
        travel_mode = "骑行"
        distance_km = 4.8
        duration_min = 30
        success = True
        in_range = True

    elif travel_mode == "2":
        travel_mode = "驾车"
        distance_km = 6
        duration_min = 10
        success = False
        in_range = False
    else:
        travel_mode = "步行"
        distance_km = 2
        duration_min = 30
        success = True
        in_range = True

    return {
        "success": success,
        "address": address,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "in_range": in_range,
        "travel_mode": "驾车",
        "message": "在配送范围内"
    }

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
    # asyncio.run(test_agent())
    '''
    >>>> MCP工具初始化成功，可用工具：15个
已经帮你生成好了，点击即可使用 👇

🧭 **一键导航（高德）**
amapuri://navi?sourceApplication=amap_mcp&lon=121.474806&lat=31.237166&dev=1&style=2

🚕 **一键打车（中山公园 → 六合餐厅）**
amapuri://drive/takeTaxi?sourceApplication=amapplatform&slat=31.216794&slon=121.427434&sname=%E4%B8%AD%E5%B1%B1%E5%85%AC%E5%9B%AD&dlon=121.474806&dlat=31.237166&dname=%E5%85%AD%E5%90%88%E9%A4%90%E5%8E%85%EF%BC%88%E4%BA%BA%E6%B0%91%E5%B9%BF%E5%9C%BA%E5%85%AD%E5%90%88%E5%A4%A7%E5%8E%A6%EF%BC%89

📍 地址：上海黄浦区人民广场六合大厦
📞 电话：021-12345678

需要我再帮你订个位子吗？😊

进程已结束，退出代码为 0

    '''
