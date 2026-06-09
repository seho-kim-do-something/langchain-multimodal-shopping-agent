import os
import tempfile

import streamlit as st

from shopping_agent import agent

st.set_page_config(page_title="AI Shopping Assistant", page_icon="🛒")
st.title("🛒 AI Shopping Assistant")
st.caption("Tell me what you want — I'll search, rate, and order the best match for you.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------------------------------------------
# Sidebar - shop by image
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Shop by Image")
    st.caption("Upload a photo of a product and I'll find similar items in our store.")

    uploaded_file = st.file_uploader("Upload product image", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)

    if uploaded_file and st.button("Find similar products", use_container_width=True):
        suffix = os.path.splitext(uploaded_file.name)[1] or ".jpg"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            image_path = tmp.name
        st.session_state.pending_image_path = image_path

        prompt = f"I uploaded a product image. Please analyze it and find similar products in the store. Image path: {image_path}"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_image = uploaded_file.name
        st.rerun()

# -----------------------------------------------------------------------------
# Chat history
# -----------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        content = msg["content"]
        if msg["role"] == "user" and "Image path:" in content:
            st.markdown("📷 Uploaded product image")
        else:
            st.markdown(content.replace("$", r"\$"))

# -----------------------------------------------------------------------------
# Run agent after image upload has created a pending image request
# -----------------------------------------------------------------------------
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and "pending_image" in st.session_state:
    with st.chat_message("assistant"):
        with st.spinner("Analyzing image and searching..."):
            result = agent.invoke({"messages": st.session_state.messages})
            response = result["messages"][-1].content.replace("`", "")
        st.markdown(response.replace("$", r"\$"))

    st.session_state.messages.append({"role": "assistant", "content": response})

    if "pending_image_path" in st.session_state:
        try:
            os.remove(st.session_state.pending_image_path)
        except OSError:
            pass
        del st.session_state.pending_image_path

    del st.session_state.pending_image
    st.rerun()

# -----------------------------------------------------------------------------
# Text chat input
# -----------------------------------------------------------------------------
if prompt := st.chat_input("e.g. I want organic beauty products under $25 with 4+ rating"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.invoke({"messages": st.session_state.messages})
            response = result["messages"][-1].content.replace("`", "")
        st.markdown(response.replace("$", r"\$"))

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()