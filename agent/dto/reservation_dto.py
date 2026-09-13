from pydantic import BaseModel, Field

class ReservationToolArgsInfo(BaseModel):
    num_people:int = Field(description="预订人数")
    num_children:int = Field(description="预订儿童人数")
    arrival_time:str = Field(description="到店时间，格式：YYYY-MM-DD HH")
    seat_preference:str= Field(description="座位偏好")
    main_dish_preference:str=Field(description="主菜偏好")
    other_comments:str= Field(description="其他备注")

