import streamlit as st
from agent import get_agent_executor


from chat_history import load_chat, save_chat

def render_chat_history(chat_history, skip_last_user=False, skip_last_assistant=False):
    for i, (role, msg) in enumerate(chat_history):
        is_last = i == len(chat_history) - 1
        if (skip_last_assistant and role == "assistant" and is_last) or \
           (skip_last_user and role == "user" and is_last):
            continue
        with st.chat_message("user" if role == "user" else "assistant", avatar="🧑" if role == "user" else "🤖"):
            st.markdown(msg)


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

    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)
    st.session_state.chat_history.append(("user", user_input))
    
    # Autoscroll using placeholder
    message_placeholder = st.empty()
    with st.chat_message("assistant", avatar="🤖"):
        stream_handler.container = message_placeholder
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
render_chat_history(
    st.session_state.chat_history,
    skip_last_user=bool(user_input),
    skip_last_assistant=bool(user_input)
)



# for role, msg in st.session_state.chat_history:
#     with st.chat_message("user" if role == "user" else "assistant", avatar="🧑" if role == "user" else "🤖"):
#         st.markdown(msg)