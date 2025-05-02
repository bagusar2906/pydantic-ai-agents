import streamlit as st
import uuid

import streamlit as st
import uuid


def auto_scroll_to_bottom( threshold_px: int = 100, enable_button: bool = True):
    """
    Scrolls to the bottom automatically if user is near the bottom.
    Optionally shows a floating 'Scroll to Bottom' button if not near the bottom.

    Args:
        threshold_px (int): How close (in px) the user must be to the bottom to auto-scroll.
        enable_button (bool): Whether to show a scroll-to-bottom button.
    """
    scroll_id = f"scroll-anchor-{uuid.uuid4()}"
    st.markdown(f'<div id="{scroll_id}"></div>', unsafe_allow_html=True)

    # JavaScript: auto-scroll and optional button
    js_code = f"""
    <script>
        const anchor = document.getElementById("{scroll_id}");

        function scrollToBottom() {{
            anchor.scrollIntoView({{ behavior: "smooth" }});
        }}

        function checkScroll() {{
            const isAtBottom = Math.abs(window.innerHeight + window.scrollY - document.body.offsetHeight) < {threshold_px};
            const button = document.getElementById("scroll-btn");

            if (!isAtBottom && !button) {{
                const btn = document.createElement("button");
                btn.innerText = "⬇ Scroll to Bottom";
                btn.id = "scroll-btn";
                btn.style.position = "fixed";
                btn.style.bottom = "20px";
                btn.style.right = "20px";
                btn.style.padding = "10px 14px";
                btn.style.zIndex = 9999;
                btn.style.border = "none";
                btn.style.backgroundColor = "#4CAF50";
                btn.style.color = "white";
                btn.style.borderRadius = "6px";
                btn.style.cursor = "pointer";
                btn.onclick = scrollToBottom;
                document.body.appendChild(btn);
            }} else if (isAtBottom && button) {{
                button.remove();
            }}

             if (anchor && isAtBottom) {{
                anchor.scrollIntoView({{ behavior: "smooth" }});
            }}
        }}

        window.addEventListener("scroll", checkScroll);
        window.addEventListener("load", checkScroll);
    </script>
    """

    if enable_button:
        st.markdown(js_code, unsafe_allow_html=True)
