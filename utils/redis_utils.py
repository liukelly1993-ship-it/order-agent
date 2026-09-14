from redis import Redis #同步对象
from redis.asyncio import Redis as AsyncRedis #异步对象
from utils.env_utils import resolve_service_url

def get_redis_client(url):
    client = Redis.from_url(resolve_service_url(url), decode_responses=True)
    return client

async def asyn_get_redis_client():
    client = AsyncRedis(
        host="localhost",
        port=6380,
        ssl=False,
        decode_responses=False
    )
    return client
