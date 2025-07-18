# chatbot_simulator.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class MessageRequest(BaseModel):
    message: str

@app.post("/ask")
def respond(req: MessageRequest):
    if "building" in req.message.lower():
        return {"response": "Hello! How can I assist you with your building project?"}
    return {"response": "Default reply"}
