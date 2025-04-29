# This module contains utility functions and tools for the application.
from langchain_core.tools import tool

@tool
def get_current_weather(location: str) -> str:
    """Get the current weather in a given location."""
    return f"The weather in {location} is sunny!"

@tool
def search_wikipedia(query: str) -> str:
    """Search Wikipedia for a topic."""
    return f"Wikipedia says {query} is great!"
