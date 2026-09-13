# 将FAQ数据同步到Redis中
from typing import List, Dict
from redis import Redis
from dotenv import load_dotenv
import os

load_dotenv()

#将FAQ数据同步到Redis中
FAQ_ITEMS: List[Dict[str, str]] = [
    {"id": "business_hours", "question": "营业时间是什么时候？", "answer": "我们的营业时间是每天早9点至晚10点。"},
    {"id": "address", "question": "位置在哪里？", "answer": "我们位于上海人民广场。"},
    {"id": "phone", "question": "联系方式是什么？", "answer": "您可以添加官方微信 shanghai_123，或拨打电话 021-11111111。"},
    {"id": "parking", "question": "停车方便吗？", "answer": "可优先使用附近公共停车场或路边划线车位；车位实时情况建议电话确认：021-11111111。"},
    {"id": "promotion", "question": "有什么优惠活动？", "answer": "优惠活动：单次消费满200九折，满500八折。"},
]


def get_redis_client():
    return Redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)


def faq_data_to_redis():
    redis_client = get_redis_client()
    pipline = redis_client.pipeline()
    
    all_faq_ids = "faq:ids" # 用来记录当前所有的faq问题的id
    
    for item in FAQ_ITEMS:
        faq_id = item.get("id")
        fat_question = item.get("question")
        faq_answer = item.get("answer")
        key = f"faq:item:{faq_id}"
        pipline.hset(key, mapping={
            "id": faq_id,
            "question": fat_question, 
            "answer": faq_answer
            }
        )
        pipline.sadd(all_faq_ids, faq_id) #Set {key：{v1,v2,v3,v4}}
        
    pipline.execute()
        
    print("FAQ数据同步完成")
    
if __name__ == "__main__":
    faq_data_to_redis()