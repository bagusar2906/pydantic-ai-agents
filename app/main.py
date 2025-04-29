# app/main.py

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import time
import uuid
from fastapi.responses import StreamingResponse
import asyncio
from agent import agent_executor


# Incoming message format
class Message(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    stream: bool = False
    model: str
    messages: List[Message]



# Response format
class ChatCompletionChunkChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: ChatCompletionChunkChoiceDelta
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]

# Function to simulate typing chunk by chunk
async def chat_stream_generator(reply_text: str, model: str) -> AsyncGenerator[str, None]:
    reply_id = str(uuid.uuid4())
    created_time = int(time.time())
    for idx, chunk in enumerate(reply_text.split()):
        chunk_data = ChatCompletionChunk(
            id=reply_id,
            object="chat.completion.chunk",
            created=created_time,
            model=model,
            choices=[
                ChatCompletionChunkChoice(
                    index=0,
                    delta=ChatCompletionChunkChoiceDelta(
                        content=chunk + " "
                    )
                )
            ]
        )
        yield f"data: {chunk_data.json()}\n\n"
        await asyncio.sleep(0.2)  # slow typing effect
    # Final message
    done_data = ChatCompletionChunk(
        id=reply_id,
        object="chat.completion.chunk",
        created=created_time,
        model=model,
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=ChatCompletionChunkChoiceDelta(),
                finish_reason="stop"
            )
        ]
    )
    yield f"data: {done_data.json()}\n\n"
    yield "data: [DONE]\n\n"

# FastAPI app
app = FastAPI()


from fastapi.middleware.cors import CORSMiddleware

# Define different personalities (models)
models = {
    "friendly-bot": lambda messages: f"😊 Thanks for saying: {messages[-1].content}, how can I help?",
    "grumpy-bot": lambda messages: f"Ugh... {messages[-1].content}... I guess I can help...",
    "tech-support-bot": lambda messages: f"Tech support mode: {messages[-1].content}. Let's fix this!"
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



from fastapi.responses import JSONResponse

@app.get("/v1/models")
async def list_models():
    return JSONResponse({
        "object": "list",
        "data": [
            {
                "id": "friendly-bot",
                "object": "model",
            },
            {
                "id": "grumpy-bot",
                "object": "model",
            },
            {
                "id": "tech-support-bot",
                "object": "model",
            }
            # Add more models if you want
        ]
    })



@app.post("/v1/chat/completions")
async def chat_completions(chat: ChatRequest):
    model = chat.model
    # qmessages = chat.messages
   
    user_message = chat.messages[-1].content


    # Call the agent
    full_response = await agent_executor.ainvoke(
        {"input": user_message}
    )

    print(full_response)
    # Your bot generates response text
    # full_response = f"Hello from {model}! You said: {messages[-1].content}"
    # Handle different models
    if model not in models:
        return {"error": "Model not found"}
    
    full_response = models[model](messages)
  
    # stream mode: send small chunks

    return StreamingResponse(chat_stream_generator(full_response, model), media_type="text/event-stream")
