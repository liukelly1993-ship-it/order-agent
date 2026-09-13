from redis import Redis
from dotenv import load_dotenv
import os
load_dotenv()

def redis_command_demo1():
    # 连接本地的 Redis 服务
    client = Redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)

    # 设置键值对 创建了一个字符串类型
    client.set('name', 'Alice') # 设置键值对 key=value

    # 获取键值对
    name = client.get('name')
    print(name)
    
    
    # 创建一个hash结构 : {name:bob, age:20, location:上海}
    client.hset('user:1', 
                mapping={
                    'name': 'bob',
                    'age': 20,
                })
    
    # 获取hash结构
    user = client.hgetall('user:1')
    print(user)

def redis_command_demo2():
    # 连接本地的 Redis 服务
    client = Redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)


    # 1.构建管道
    pipeline = client.pipeline()
    
    # 2.打包
    # 设置键值对 创建了一个字符串类型
    pipeline.set('name', 'Alice') # 设置键值对 key=value

    # 获取键值对
    pipeline.get('name')
  
    
    # 创建一个hash结构 : {name:bob, age:20, location:上海}
    pipeline.hset('user:1', 
                mapping={
                    'name': 'bob',
                    'age': 20,
                })
    
    # 获取hash结构
    pipeline.hgetall('user:1')
    
    # 3.执行
    results = pipeline.execute()
    print(results)
    

if __name__ == '__main__':
    redis_command_demo2()