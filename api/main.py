# 提供Agent所有能力接口
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse
from agent.langchain_assistant import assistant_query, get_devliery_info
import sys
from pathlib import Path
import os

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))  # 将项目根目录添加到系统中
from utils.redis_utils import get_redis_client
from dotenv import load_dotenv
import re
from difflib import SequenceMatcher
from typing import Literal

load_dotenv()

app = FastAPI()

_DEFAULT_CORS_ORIGINS = [
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "https://liukelly1993-ship-it.github.io",
]
_EXTRA_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_DEFAULT_CORS_ORIGINS + _EXTRA_CORS_ORIGINS)),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def frontend():
    """返回餐厅助手前端页面。"""
    return FileResponse(ROOT_PATH / "frontend" / "index.html")


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


class FAQItem(BaseModel):
    id: str
    question: str
    answer: str


class FAQResponse(BaseModel):  # faq/suggest接口返回的数据格式
    success: bool
    query: str
    suggestions: list[FAQItem]


class DeliveryRequest(BaseModel):
    address: str = Field(description="目标配送地址")
    travel_mode: str = Field(default="2", description="配送方式 1-骑行  2-驾车  3-直线距离")


class ChatRequest(BaseModel):
    # 定义一个ChatRequest类，继承自BaseModel
    query: str = Field(description="用户输入的问题")  # 定义query字段，类型为字符串，并添加描述说明这是用户输入的问题
    limit: int = Field(default=1, description="查询的结果数量，默认为1")  # 定义limit字段，类型为整数，并添加描述说明这是返回结果数量，默认值为5
    # Bugfix #2: 原版只有 query,thread_id 由 assistant_query 内部硬编码 '001'
    # (后改为永远 uuid 新建),均无法让调用方/前端维护会话. 改为显式传入,
    # 不传则由 assistant_query 内部新建 uuid 作为新会话.
    thread_id: str | None = Field(default=None, description="会话ID;不传则由后端新建会话")


class DeliveryResponse(BaseModel):
    success: bool = Field(..., description="响应是否成功")
    message: str = Field(..., description="响应消息")
    address: str = Field(..., description="目标配送地址")
    distance_km: float = Field(..., description="配送距离（单位：公里）")
    duration_min: int | None = Field(default=None, description="配送时间（单位：分钟）")
    in_range: bool | None = Field(default=None, description="是否在配送范围内")
    travel_mode: Literal["骑行", "驾车", "直线"] = Field(default="驾车", description="配送方式")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # 以流式的方式返回结果
    # Bugfix #1: 原版 def 端点,但 assistant_query 是 async generator,
    # StreamingResponse 在同步端点里接收 async generator 会抛 RuntimeError.
    # 改为 async def,FastAPI 自动从 async 端点消费 async generator.
    return StreamingResponse(
        assistant_query(query=request.query, thread_id=request.thread_id),
        media_type="text/event-stream"
    )


def load_faq_from_redis() -> list[FAQItem]:
    """从缓存中获取FAQ"""
    client = get_redis_client(os.getenv("REDIS_URL"))
    faq_ids = client.smembers("faq:ids")

    pipeline = client.pipeline()
    full_keys = [f"faq:item:{id}" for id in faq_ids]  # 根据每个id，拼接成具体的每个faq的key
    for key in full_keys:
        pipeline.hgetall(key)

    faq_items = pipeline.execute()

    return [FAQItem(**item) for item in faq_items]


# 定义正则表达式，用于移除文本中的标点符号
_PUNCT_RE = re.compile(r"[\s,，。.!！？?;；:：'\"“”‘’（）()\[\]【】<>《》、/\\|_\-]+")


# 对文本进行清洗的函数：
def _normalize_text(text: str) -> str:
    return _PUNCT_RE.sub("", (text or "").strip())


def get_similarity_score(query: str, faq_question: str):
    """使用字符串匹配方式衡量相似度，计算query和faq_question之间的相似得分"""
    q = _normalize_text(query)
    f = _normalize_text(faq_question)

    score = SequenceMatcher(None, q, f).ratio()  # 只是判断两个字符串“长”的像不像

    a = set(list(q))
    b = set(list(f))
    jaccard_score = len(a.intersection(b)) / len(a.union(b))  # 判断两个字符串“重”的像不像

    # 如果两个字符串之间存在包含关系，添加一个正向分
    bonus = 0
    if q in f or f in q:
        bonus = 0.5

    return score * 0.6 + jaccard_score * 0.4 + bonus


#
@app.get("/faq/suggest", response_model=FAQResponse)
def faq_endpoint(query: str, limit: int):  # request:ChatRequest前端传递的数据应该是对象格式
    # 实现FAQ查询
    # 1. 从redis加载FAQ
    faq_items = load_faq_from_redis()
    """
    [FAQItem(id='address', question='位置在哪里？', answer='我们位于上海人民广场。'), FAQItem(id='phone', question='联系方式是什么？', answer='您可以添加官方微信 shanghai_123，或拨打电话 021-11111111。'), FAQItem(id='promotion', question='有什么优惠活动？', answer='优惠活动：单次消费满200九折，满500八折。'), FAQItem(id='business_hours', question='营业时间是什么时候？', answer='我们的营业时间是每天早9点至晚10点。'), FAQItem(id='parking', question='停车方便吗？', answer='可优先使用附近公共停车场或路边划线车位；车位实时情况建议电话确认：021-11111111。')]
    """

    # 2. 根据用户输入的问题，查询最相似的FAQ
    # query = request.query # 用户的问题
    scores_list = []
    for faq in faq_items:
        score = get_similarity_score(query, faq.question)  # 如果需要从语义层面衡量相似度，可以使用语义匹配模型embedding
        scores_list.append((score, faq))  # 存放每个faq的得分和faq本身

    # 根据得分排序
    scores_list.sort(key=lambda x: x[0], reverse=True)
    # 取出得分最高的FAQ
    limit = 2  # 人为写一个限制，最多返回2个
    top_faqs = scores_list[:limit]

    # 3. 返回查询结果
    return FAQResponse(
        success=True,
        query=query,
        suggestions=[faq for _, faq in top_faqs]
    )


@app.post("/delivery", response_model=DeliveryResponse)
async def delivery(request: DeliveryRequest):
    """配送接口查询"""
    result = await get_devliery_info(request.address, request.travel_mode)
    return result


@app.post("/clear_history")
def clear_history():
    pass


@app.get("/get_history")
def get_history():
    pass
