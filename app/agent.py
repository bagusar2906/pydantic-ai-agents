# agent.py

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor

from tools import get_current_weather, search_wikipedia
from dotenv import load_dotenv
from langchain.chat_models import ChatOllama  # Import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import MessagesPlaceholder
from langchain.agents import create_openai_functions_agent  # Import create_openai_functions_agent
from langchain.callbacks.base import BaseCallbackHandler
import os

load_dotenv()

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container=None):
        self.container = container
        self.text = ""

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        if self.container:
            self.container.markdown(self.text)
        
# Initialize your LLM
# llm = ChatOpenAI(
#     model="gpt-4o",  # or "gpt-4-turbo"
#     temperature=0,
#     callbacks=[StreamingStdOutCallbackHandler()],
#     streaming=True
# )

# Define your tools
tools = [get_current_weather, search_wikipedia]


# Create the AgentExecutor
# agent_executor = initialize_agent(
#     tools,
#     llm,
#     agent=AgentType.OPENAI_FUNCTIONS,
#     verbose=True,
# )

def get_agent_executor(model_name: str):
    # Choose model
    if model_name.startswith("ollama:"):
        llm = ChatOllama(model=model_name.split(":")[1])
    else:
        llm = ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            streaming=True,
            temperature=0
        )

    # Prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    # Stream handler
    stream_handler = StreamHandler()

    # Reassign callbacks
    llm.callbacks = [stream_handler]

    # Create agent
    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

    # Wrap in executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor, stream_handler