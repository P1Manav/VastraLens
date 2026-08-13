import streamlit as st
import os
import tempfile
import re
from PIL import Image
from agent import get_agent
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="TailorTalk", page_icon="👗", layout="wide")

st.title("👗 TailorTalk - Visual Search")
st.write("Upload a picture of a saree or share a link, and I'll find visually similar items from our catalog!")

# Initialize Agent
if "agent" not in st.session_state:
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
            # Save uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tf:
                tf.write(uploaded_file.getbuffer())
                temp_path = tf.name
            
            # Formulate query for the agent
            query = f"Find sarees similar to this image: {temp_path}"
            
            # Display user message
            st.session_state.messages.append({"role": "user", "content": "I uploaded an image. Please find similar items."})
            
            if st.session_state.agent:
                with st.spinner("Searching for matches..."):
                    try:
                        response = st.session_state.agent.run(input=query)
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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    if st.session_state.agent:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.agent.run(input=prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"An error occurred: {e}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        with st.chat_message("assistant"):
            st.markdown("Agent is not initialized. Please set GOOGLE_API_KEY.")
