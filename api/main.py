# 提供Agent所有能力接口
from fastapi import FastAPI

app = FastAPI()

@app.post("/chat")
def chat_endpoint():
    pass

@app.post("/clear_history")
def clear_history():
    pass


@app.get("/get_history")
def get_history():
    pass
