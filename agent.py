import os
import pickle
import numpy as np
import torch
from PIL import Image
import requests
from io import BytesIO
from transformers import CLIPProcessor, CLIPVisionModelWithProjection
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# Configuration
EMBEDDINGS_PATH = "embeddings.npy"
METADATA_PATH = "metadata.pkl"
MODEL_ID = "openai/clip-vit-base-patch32"

# Load Model
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Loading CLIP model for agent...")
try:
    clip_model = CLIPVisionModelWithProjection.from_pretrained(MODEL_ID).to(device)
    clip_processor = CLIPProcessor.from_pretrained(MODEL_ID)
except Exception as e:
    print(f"Error loading CLIP model: {e}")

# Load embeddings and metadata
def load_embeddings_and_metadata():
    try:
        embeddings = np.load(EMBEDDINGS_PATH)
        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)
        return embeddings, metadata
    except Exception as e:
        print(f"Warning: Could not load embeddings or metadata: {e}")
        return None, []

def get_image_embedding(image_input):
    """Get CLIP embedding for an image from a path or URL."""
    try:
        if isinstance(image_input, str):
            if image_input.startswith("http://") or image_input.startswith("https://"):
                response = requests.get(image_input, timeout=10)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content)).convert("RGB")
            else:
                img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
             raise ValueError("Unsupported image input type.")
             
        inputs = clip_processor(images=img, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = clip_model(**inputs)
            image_features = outputs.image_embeds
        
        # Normalize
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        return image_features.cpu().numpy()[0]
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

@tool
def search_visually_similar_sarees(image_path_or_url: str) -> str:
    """
    Search for visually similar sarees in the database using an image.
    Use this tool whenever the user provides an image or asks to find similar clothing to an image.
    Input should be the file path or URL of the image.
    Returns a formatted string containing the top matching items, their prices, and links.
    """
    dataset_embeddings, metadata = load_embeddings_and_metadata()
    if dataset_embeddings is None or not metadata:
        return "The database is currently empty or not loaded properly. Please make sure the dataset is ingested."
        
    embedding = get_image_embedding(image_path_or_url)
    if embedding is None:
        return "Could not process the provided image. Please ensure it's a valid image path or URL."
        
    # Calculate cosine similarity (dot product since vectors are normalized)
    scores = np.dot(dataset_embeddings, embedding)
    
    # Get top 5 matches
    k = 5
    top_indices = np.argsort(scores)[::-1][:k]
    
    results = []
    for i, idx in enumerate(top_indices):
        score = scores[idx]
        if idx < len(metadata):
            item = metadata[idx]
            result_str = (
                f"{i+1}. **{item['Name']}**\n"
                f"   - SKU: {item['SKU']}\n"
                f"   - Price: INR {item['Price']}\n"
                f"   - Similarity Score: {score:.4f}\n"
                f"   - Buy Link: {item['Website Link']}\n"
                f"   - Image URL: {item['image_url']}"
            )
            results.append(result_str)
            
    if not results:
        return "No similar items found."
        
    return "Found the following similar items:\n\n" + "\n\n".join(results)

def get_agent():
    """Initializes and returns the LangChain agent."""
    try:
        llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-1.5-flash")
    except Exception as e:
        print(f"Error initializing LLM (Did you set GOOGLE_API_KEY?): {e}")
        return None

    tools = [search_visually_similar_sarees]
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    agent = initialize_agent(
        tools, 
        llm, 
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True
    )
    return agent
