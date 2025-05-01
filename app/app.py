import streamlit as st
from agent import get_agent_executor


from chat_history import load_chat, save_chat



st.set_page_config(page_title="🧠 LangChain Agent", layout="wide")
st.title("🧠 LangChain Agent with Tools")

# --- Sidebar ---
model_choice = st.sidebar.selectbox("Choose model", ["gpt-4o", "gpt-3.5-turbo", "ollama:llama3"])
st.sidebar.markdown("---")

# --- Load chat history ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat()

# --- LangChain Agent Setup ---
agent_executor, stream_handler = get_agent_executor(model_choice)

# --- Chat input/output ---
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        container = st.empty()
        stream_handler.container = container
        with st.spinner("Thinking..."):
            try:
                result = agent_executor.invoke({
                    "input": user_input,
                    "chat_history": st.session_state.chat_history
                })
                reply = result["output"]
                st.session_state.chat_history.append(("assistant", reply))
                save_chat(st.session_state.chat_history)
            except Exception as e:
                st.error(f"Error: {e}")

# --- Render chat history ---
for role, msg in st.session_state.chat_history:
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(msg)