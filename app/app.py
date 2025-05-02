import streamlit as st
from agent import get_agent_executor

from chat_history import load_chat, save_chat

# Ensure streamlit is installed
try:
    import streamlit as st
except ModuleNotFoundError:
    raise ImportError("Streamlit is not installed. Please run 'pip install streamlit' to use this app.")

import time
from agent import get_agent_executor
from chat_history import load_chat, save_chat

st.set_page_config(page_title="🧠 LangChain Agent", layout="wide")
st.title("🧠 LangChain Agent with Tools")

# --- Sidebar ---
model_choice = st.sidebar.selectbox("Choose model", ["gpt-4o", "gpt-3.5-turbo", "ollama:llama3"])
st.sidebar.markdown("---")

# Reset button
if st.sidebar.button("🔄 Reset Chat"):
    st.session_state.chat_history = []
    save_chat([])  # Clear persistent chat
    st.rerun()

# Download history
if st.sidebar.button("📄 Download Chat"):
    history = "\n".join([f"{'User' if r=='user' else 'Assistant'}: {m}" for r, m in st.session_state.get("chat_history", [])])
    st.sidebar.download_button("Save .txt", history, file_name="chat_history.txt")

# --- Load chat history ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat()

# --- LangChain Agent Setup ---
agent_executor, stream_handler = get_agent_executor(model_choice)

# --- Chat input/output ---
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        container = st.empty()
        stream_handler.container = container
        time.sleep(0.5)  # typing delay
        with st.spinner("Thinking..."):
            try:
                result = agent_executor.invoke({
                    "input": user_input,
                    "chat_history": st.session_state.chat_history
                })
                
            
                reply = result["output"]

                # Extract tool used if available
                tool_used = None
                for step in result.get("intermediate_steps", []):
                    tool_used = step[0].tool
                print("Tool used:", tool_used)
                print("Reply:", reply)
                # Store assistant message with tool label
                st.session_state.chat_history.append((tool_used or "assistant", reply))
                save_chat(st.session_state.chat_history)
            except Exception as e:
                st.error(f"Error: {e}")

# --- Render chat history with avatar mapping ---
avatar_map = {
    "assistant": "🤖",
    "user": "👤",
    "wikipedia": "📚",
    "get_current_weather": "☀️",
}

for role, msg in reversed(st.session_state.chat_history):
    avatar = avatar_map.get(role, "🤖")
    with st.chat_message(role if role in ["user", "assistant"] else "assistant", avatar=avatar):
        st.markdown(msg)

# --- Autoscroll to top ---
st.markdown("""
    <script>
        window.scrollTo({ top: 0, behavior: "smooth" });
    </script>
""", unsafe_allow_html=True)