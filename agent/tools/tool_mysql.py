import os

import pymysql
from dotenv import load_dotenv
from langchain_core.tools import tool
from pymysql.cursors import DictCursor


load_dotenv()


@tool
def search_dishes():
    '''搜索查询餐厅的菜品,返回餐厅菜品数据'''
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
                    dish_name as 菜品名称, 
                    price as 价格, 
                    description as 描述, 
                    category as 菜品类别, 
                    spice_level as 麻辣程度, 
                    flavor as 口味, 
                    main_ingredients as 主料, 
                    cooking_method as 烹饪方法, 
                    is_vegetarian as 是否素食, 
                    allergens as 过敏源
                    from menu_items
                where 
                    is_featured = 1
            ''')
            special_dishes = cursor.fetchall()
    return special_dishes