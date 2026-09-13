from redis import Redis

def get_redis_client(url):
    client = Redis.from_url(url, decode_responses=True)
    return client