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

def extract_text(response):
    if isinstance(response, list):
        text = ""
        for block in response:
            if isinstance(block, dict) and block.get("type") == "text":
                text += block.get("text", "") + "\n"
            elif isinstance(block, str):
                text += block + "\n"
        return text.strip()
    return str(response)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* Swiss Dark Theme Colors */
:root {
    --bg-color: #0A0A0A;
    --sidebar-bg: #121212;
    --text-color: #FAFAFA;
    --text-muted: #888888;
    --input-bg: #1A1A1A;
    --border-color: #2A2A2A;
    --accent: #FFFFFF;
    --accent-text: #000000;
}

/* Typography Overrides */
.stApp, h1, h2, h3, h4, p, label, .stMarkdown, .stChatMessage p {
    font-family: 'Plus Jakarta Sans', -apple-system, system-ui, sans-serif !important;
}
h1, h2, h3 {
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}
span[class*="icon"] {
    font-family: 'Material Icons' !important;
}

/* App Background */
.stApp {
    background-color: var(--bg-color);
    color: var(--text-color);
}
.stApp > header {
    background-color: transparent !important;
}

/* Sidebar Background */
[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color);
}
[data-testid="stSidebar"] * {
    color: var(--text-color);
}
[data-testid="stSidebar"] hr {
    border-color: var(--border-color);
}

/* Chat Input Styling with Shadow */
[data-testid="stBottom"] {
    background-color: transparent !important;
    padding-bottom: 0 !important;
}
[data-testid="stBottom"] > div {
    padding-bottom: 0 !important;
}
[data-testid="stChatInput"] {
    background-color: transparent !important;
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}
[data-testid="stChatInput"] textarea {
    background-color: var(--input-bg) !important;
    color: white !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 4px !important;
    padding: 16px 24px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.2s ease-in-out;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--text-muted) !important;
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6) !important;
}
[data-testid="stChatInput"] button {
    background-color: var(--accent) !important;
    color: var(--accent-text) !important;
    border-radius: 4px !important;
}

/* Chat Message Styling */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    padding: 1.5rem 0 !important;
}
.stChatMessageAvatar {
    background-color: transparent !important;
    border-radius: 4px !important;
}

/* Layout */
.block-container {
    padding-top: 4rem !important;
    padding-bottom: 8rem !important;
    max-width: 760px !important;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
[data-testid="collapsedControl"] { display: none !important; }

/* File uploader styling */
[data-testid="stFileUploader"] {
    background-color: var(--input-bg);
    border-radius: 4px;
    padding: 15px;
    border: 1px solid var(--border-color);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

/* High Contrast Buttons */
.stButton>button {
    width: 100%;
    border-radius: 4px;
    background-color: #1A1A1A !important;
    color: #FFFFFF !important;
    border: 1px solid #333333 !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 12px 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.stButton>button * {
    color: #FFFFFF !important;
}
.stButton>button:hover {
    background-color: #FFFFFF !important;
    border-color: #FFFFFF !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(255, 255, 255, 0.15) !important;
}
.stButton>button:hover * {
    color: #000000 !important;
}

/* Subtle image styling */
[data-testid="stImage"] img {
    border-radius: 4px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    border: 1px solid var(--border-color);
}
</style>
""", unsafe_allow_html=True)

st.title("👗 TailorTalk")
st.markdown("<p style='color: #B4B4B4; font-size: 1.1rem; margin-bottom: 2rem;'>Share a picture of a saree, and I'll find visually similar items from our catalog!</p>", unsafe_allow_html=True)

# Always initialize/reload Agent
st.session_state.agent = get_agent()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []



# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg.get("display", msg["content"]))

# Chat Input
if prompt := st.chat_input("Ask me something or provide an image link...", accept_file=True, file_type=["jpg", "jpeg", "png", "webp"]):
    
    # Safely extract text and files from the prompt object
    try:
        raw_text = prompt.text
        files = prompt.files
    except AttributeError:
        try:
            raw_text = prompt.get("text", "")
            files = prompt.get("files", [])
        except AttributeError:
            raw_text = prompt
            files = []
            
    is_base64 = isinstance(raw_text, str) and raw_text.startswith("data:image")
    has_image = bool(files) or is_base64
    
    display_text = raw_text
    llm_query = raw_text

    # If the user pasted a raw base64 image
    if is_base64:
        try:
            header, b64data = raw_text.split(",", 1)
            img_data = base64.b64decode(b64data)
            with open("uploaded_image.png", "wb") as f:
                f.write(img_data)
            display_text = "I provided an image."
            llm_query = "I provided an image. Please use your search tool to find similar sarees. Pass the exact string 'current_upload' as the argument to the tool."
        except Exception as e:
            pass
    elif files:
        with open("uploaded_image.png", "wb") as f:
            f.write(files[0].getbuffer())
        if not raw_text:
            display_text = "I provided an image."
            llm_query = "I uploaded an image. Please use your search tool to find similar sarees. Pass the exact string 'current_upload' as the argument to the tool."
        else:
            llm_query = raw_text + " Please use your search tool to find similar sarees. Pass the exact string 'current_upload' as the argument to the tool."
            
    st.session_state.messages.append({"role": "user", "content": llm_query, "display": display_text})
    
    with st.chat_message("user"):
        if has_image:
            st.image("uploaded_image.png", width=300)
        st.markdown(display_text)
        
    if st.session_state.agent:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Convert messages to format expected by LangGraph
                    messages = [(m["role"], m["content"]) for m in st.session_state.messages]
                    response_payload = st.session_state.agent.invoke({"messages": messages})
                    response = extract_text(response_payload["messages"][-1].content)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response, "display": response})
                except Exception as e:
                    error_msg = f"An error occurred: {e}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg, "display": error_msg})
    else:
        with st.chat_message("assistant"):
            st.markdown("Agent is not initialized. Please set GOOGLE_API_KEY.")
