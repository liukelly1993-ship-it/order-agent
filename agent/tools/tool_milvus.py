import os
from pathlib import Path

import pymysql
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from pymysql.cursors import DictCursor
# 项目根目录: agent/tools/tool_milvus.py → 上三级 = 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

'''
连接向量库并添加数据
'''
from pymilvus import MilvusClient,DataType


# 连接到向量库
def get_client():
    client = MilvusClient(uri = os.getenv('MILVUS_URI'),token  = os.getenv('MILVUS_TOKEN'))
    return client

'''
@:return 返回的是一个装着 BGE 模型的 LangChain 客户端对象
'''
# Bugfix #5: 原版 get_embedding() 每次调用都新建 HuggingFaceEmbeddings 实例.
# BGE-base-zh 模型约 100MB+,首次加载需数秒; user_favorite_dishes / search_data
# 每次工具调用都会重载一次,单次工具调用白白多耗数秒.
# 改为模块级单例,进程内只加载一次,所有调用方共享同一 embeddings 实例.
_EMBEDDING_SINGLETON: HuggingFaceEmbeddings | None = None


def get_embedding():
    global _EMBEDDING_SINGLETON
    if _EMBEDDING_SINGLETON is None:
        _EMBEDDING_SINGLETON = HuggingFaceEmbeddings(
            model_name=str(PROJECT_ROOT / 'models' / 'bge-base-zh'),
            model_kwargs={
                'device': 'mps',
                'trust_remote_code': True
            },
            encode_kwargs={'normalize_embeddings': True},  # 配置ip使用 归一化,扔掉"长度"这个噪声，只留"方向"这个有效信息
        )
    return _EMBEDDING_SINGLETON


#初始化向量库并添加数据,注意: 目前是全量覆盖模式
def insert_data():
    client = get_client()
    collection_name = os.getenv("COLLECTION_NAME")
    # 初始化: 全量覆盖
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)
    # 定义集合结构
    schema = (MilvusClient.create_schema(auto_id=True)
              .add_field(field_name='id',datatype=DataType.INT64,is_primary=True)
              .add_field(field_name='vector',datatype=DataType.FLOAT_VECTOR,dim=768)
              .add_field(field_name='text',datatype=DataType.VARCHAR,max_length=1000)
              )
    # 定义索引类型
    index_params = MilvusClient.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="HNSW",
        metric_type="IP" #新人接手、怕踩坑 → 用 COSINE ; 如果已经归一化{'normalize_embeddings': True}, 了,可以换成IP效率更高,
    )

    # 创建集合
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        index_params=index_params
    )


    # text = [
    #     "hello world",
    #     "how old are you",
    #     "what is your name",
    #     "where are you from"
    # ]


    '''
[
    {
		"text" : "菜品名称:宫保鸡丁;价格:28.00;描述:经典川菜,鸡肉丁配花生米,酸甜微辣,口感丰富;菜品类别:川菜;麻辣程度:2;口味:酸甜微辣;主料:鸡肉,花生米,青椒,红椒,葱段;烹饪方法:爆炒;是否素食:0;过敏源:花生,可能含有麸质"
	},
	{
		"text" : "菜品名称:麻婆豆腐;价格:18.00;描述:四川传统名菜,嫩滑豆腐配麻辣汤汁,下饭神器;菜品类别:川菜;麻辣程度:3;口味:麻辣鲜香;主料:嫩豆腐,牛肉末,豆瓣酱,花椒;烹饪方法:烧炒;是否素食:0;过敏源:大豆,可能含有麸质"
	},
	{
		"text" : "菜品名称:清炒时蔬;价格:15.00;描述:新鲜时令蔬菜清炒,营养健康,口感清淡;菜品类别:素食;麻辣程度:0;口味:清淡爽口;主料:时令蔬菜,大蒜,盐;烹饪方法:清炒;是否素食:1;过敏源:"
	},
	{
		"text" : "菜品名称:红烧鲤鱼;价格:45.00;描述:新鲜鲤鱼红烧制作,肉质鲜美,营养丰富;菜品类别:鲁菜;麻辣程度:1;口味:咸鲜微甜;主料:鲤鱼,葱,姜,蒜,冰糖,八角;烹饪方法:红烧;是否素食:0;过敏源:鱼类"
	},
	{
		"text" : "菜品名称:蒜蓉西兰花;价格:12.00;描述:新鲜西兰花配蒜蓉,营养丰富,适合减肥人群;菜品类别:素食;麻辣程度:0;口味:蒜香清淡;主料:西兰花,大蒜,橄榄油;烹饪方法:蒸炒;是否素食:1;过敏源:无过敏原"
	}
]

    '''
    #获取真实业务数据 查询mysql  todo:方法体用到了两次需要抽取一个方法出来,传一个sql的字符串进去就行
        # 连接到数据库
    with pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE"),
            port=int(os.getenv("DB_PORT")),
            charset=os.getenv("DB_CHARSET"),
    ) as conn:
        # 创建一个新游标来执行查询
        with conn.cursor(DictCursor) as cursor:
            cursor.execute('''
                    select 
                        concat(
                            '菜品名称:', ifnull(dish_name, ''), ';' , 
                            '价格:', ifnull(price, ''), ';',
                            '描述:', ifnull(description, ''), ';',
                            '菜品类别:', ifnull(category, ''), ';',
                            '麻辣程度:', ifnull(spice_level, ''), ';',
                            '口味:', ifnull(flavor, ''), ';',
                            '主料:', ifnull(main_ingredients, ''), ';',
                            '烹饪方法:', ifnull(cooking_method, ''), ';',
                            '是否素食:', ifnull(is_vegetarian, ''), ';',
                            '过敏源:', ifnull(allergens, '')
                        ) as text
                    from menu_items
            ''')
            rows = cursor.fetchall()
            special_dishes_result = [row['text'] for row in rows]

    embeddings = get_embedding()
    #执行向量化
    vector_list = embeddings.embed_documents(special_dishes_result)
    # print(vector_list)
    data_to_insert = [
        {'vector':vec , 'text':txt} for vec ,txt in zip(vector_list , special_dishes_result)
    ]
    #数据入库,  返回值: 插入的行数和插入的主键列表。
    res = client.insert(collection_name=collection_name, data=data_to_insert)
    print(res)

#搜索向量库
def search_data(query):
    client = get_client()
    collection_name = 'test_collection'
    embedding = get_embedding()
    # 单条查询向量化(搜索用) 形参:
    # 文本 -
    # 返回值:
    # 文本的嵌入。
    '''
    :param query: 查询文本
    :return: 单条文本的向量化
    '''
    vector_query = embedding.embed_query(query)
    search_resp = client.search(
        collection_name=collection_name,
        data=[vector_query],  # 搜索矢量/矢量/嵌入列表
        anns_field="vector",  # 告诉 Milvus:在哪个字段上做近似最近邻向量搜索,Approximate Nearest Neighbors(近似最近邻)
        output_fields=["text"],  # 告诉 Milvus:返回的字段
        limit=2,  # 告诉 Milvus:返回的条数
    )
    return search_resp


@tool
def user_favorite_dishes(query:str):
    '''根据用户的口味推荐菜品'''
    client = get_client()
    collection_name = os.getenv('COLLECTION_NAME')
    vector_query = get_embedding().embed_query(query)
    result = client.search(collection_name=collection_name, data=[vector_query], anns_field="vector",
                           output_fields=["text"], limit=2, )
    # 解析result
    '''
    data: [
    [
        {'id': 469050758446208451, 'distance': 0.5767658948898315, 'entity': {'text': '菜品名称:麻婆豆腐;价格: 18.00;描述:四川传统名菜,嫩滑豆腐配麻辣汤汁,下饭神器;菜品类别:川菜;麻辣程度: 3;口味:麻辣鲜香;主料:嫩豆腐,牛肉末,豆瓣酱,花椒;烹饪方法:烧炒;是否素食: 0;过敏源:大豆,可能含有麸质'
            }
        },
        {'id': 469050758446208450, 'distance': 0.5191517472267151, 'entity': {'text': '菜品名称:宫保鸡丁;价格: 28.00;描述:经典川菜,鸡肉丁配花生米,酸甜微辣,口感丰富;菜品类别:川菜;麻辣程度: 2;口味:酸甜微辣;主料:鸡肉,花生米,青椒,红椒,葱段;烹饪方法:爆炒;是否素食: 0;过敏源:花生,可能含有麸质'
            }
        }
    ]
]
    '''
    if result:
        final_result=[]
        for item in result[0]:
            # distance = item['distance']
            # todo if dis > 0.5: #阈值判断，根据实际效果调整
            item_str = item['entity']['text']
            final_result.append(item_str)
        return final_result
    else:
        return '在当前库里面没有找到和用户喜好相关的菜品'
# if __name__ == '__main__':
#     # insert_data()
#     # res = search_data("川菜")
#     # res = user_favorite_dishes("川菜")
#     # print(res)
#     pass