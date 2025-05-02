from langchain.callbacks.base import BaseCallbackHandler
import time

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container=None, delay: float = 0.05):
        self.container = container
        self.text = ""
        self.delay = delay

    def on_llm_new_token(self, token: str, **kwargs):
        self.text += token
        if self.container:
            # Typing effect
            for char in token:
                self.container.markdown(self.text + "▌", unsafe_allow_html=False)
                time.sleep(self.delay)
            self.container.markdown(self.text, unsafe_allow_html=False)  # Final display

    def finalize(self):
        if self.container:
            self.container.markdown(self.text, unsafe_allow_html=False)

       