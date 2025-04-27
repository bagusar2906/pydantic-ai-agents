import os, uuid, json
from fastapi import FastAPI, UploadFile, Form, File
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.supabase import SupabaseVectorStore
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ChatMessageHistory, ConversationBufferMemory

from supabase import create_client, Client

load_dotenv()

# ENV
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
embedding = OpenAIEmbeddings()

vectorstore = SupabaseVectorStore(
    client=supabase,
    embedding=embedding,
    table_name="documents",
    query_name="match_documents"
)

# Chat history per session
history_store = "history/chat_logs.json"
chat_histories = {}

if os.path.exists(history_store):
    with open(history_store, "r") as f:
        chat_histories = json.load(f)

from langchain.agents.tools import tool
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field

# Define tools models
class MathInput(BaseModel):
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")

# Define tools
@tool(args_schema=MathInput)
def add_numbers(a: float, b: float) -> float:
    """Adds two numbers."""
    return a + b

class SummaryInput(BaseModel):
    text: str = Field(..., description="Text to summarize")

@tool(args_schema=SummaryInput)
def summarize_text(text: str) -> str:
    """Summarizes a paragraph of text."""
    return f"Summary: {text[:50]}..."


# Schemas for OpenWebUI
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str]
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 256

class ChatCompletionChoice(BaseModel):
    message: Message
    finish_reason: str
    index: int

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    choices: List[ChatCompletionChoice]
    model: str
    usage: dict


from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

tools = [add_numbers, summarize_text]

llm = ChatOpenAI(temperature=0)

agent_executor = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
)


app = FastAPI()

def get_history(session_id):
    return chat_histories.get(session_id, [])

def save_history(session_id, messages):
    chat_histories[session_id] = messages
    with open(history_store, "w") as f:
        json.dump(chat_histories, f)

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = []

    for file in files:
        contents = await file.read()
        text = contents.decode("utf-8")
        loader = TextLoader.from_text(text, file.filename)
        docs.extend(loader.load())

    splits = text_splitter.split_documents(docs)
    vectorstore.add_documents(splits)

    return {"status": "uploaded", "count": len(splits)}

@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    session_id = "default-session"  # Use req.model or metadata to support multi-session

    history = get_history(session_id)
    message_history = ChatMessageHistory()
    for msg in history:
        message_history.add_message({"type": msg['role'], "data": msg['content']})

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=message_history,
    )

    llm = ChatOpenAI(temperature=req.temperature)
    chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=vectorstore.as_retriever(), memory=memory)

    user_input = req.messages[-1].content

    response = agent_executor.run(user_input)

    # response = chain.run(user_input)

    updated_history = history + [{"role": "user", "content": user_input}, {"role": "assistant", "content": response}]
    save_history(session_id, updated_history)

    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(role="assistant", content=response),
                finish_reason="stop",
            )
        ],
        model=req.model or "agent-executor",
        usage={"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200},
    )
