import streamlit as st
import os
import tempfile
import re
import base64
from PIL import Image
from agent import get_agent
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="TailorTalk", page_icon="👗", layout="wide")

st.title("👗 TailorTalk - Visual Search")
st.write("Upload a picture of a saree or share a link, and I'll find visually similar items from our catalog!")

# Always initialize/reload Agent
st.session_state.agent = get_agent()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Image Upload
with st.sidebar:
    st.header("Upload Image")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "webp"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        if st.button("Search for this image"):
            # Save uploaded file to a local relative path to avoid LLM local path filters
            with open("uploaded_image.png", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Formulate query for the agent
            query = "I uploaded an image. Please use your search tool to find similar sarees. Pass the exact string 'current_upload' as the argument to the tool."
            
            # Display user message
            st.session_state.messages.append({"role": "user", "content": "I uploaded an image. Please find similar items."})
            
            if st.session_state.agent:
                with st.spinner("Searching for matches..."):
                    try:
                        messages = [(m["role"], m["content"]) for m in st.session_state.messages]
                        messages.append(("user", query))
                        response_payload = st.session_state.agent.invoke({"messages": messages})
                        response = response_payload["messages"][-1].content
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.session_state.messages.append({"role": "assistant", "content": f"An error occurred: {e}"})
            else:
                 st.session_state.messages.append({"role": "assistant", "content": "Agent is not initialized. Please ensure GOOGLE_API_KEY is set."})

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask me something or provide an image link..."):
    # If the user pasted a raw base64 image
    if prompt.startswith("data:image"):
        try:
            header, b64data = prompt.split(",", 1)
            img_data = base64.b64decode(b64data)
            with open("uploaded_image.png", "wb") as f:
                f.write(img_data)
            prompt = "I provided an image. Please use your search tool to find similar sarees. Pass the exact string 'current_upload' as the argument to the tool."
        except Exception as e:
            pass
            
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    if st.session_state.agent:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Convert messages to format expected by LangGraph
                    messages = [(m["role"], m["content"]) for m in st.session_state.messages]
                    response_payload = st.session_state.agent.invoke({"messages": messages})
                    response = response_payload["messages"][-1].content
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"An error occurred: {e}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        with st.chat_message("assistant"):
            st.markdown("Agent is not initialized. Please set GOOGLE_API_KEY.")
