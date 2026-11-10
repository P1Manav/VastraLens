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
from langgraph.prebuilt import create_react_agent

# Configuration
EMBEDDINGS_PATH = "embeddings.npy"
METADATA_PATH = "metadata.pkl"
MODEL_ID = "openai/clip-vit-base-patch32"

# Load Model
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model = None
clip_processor = None

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

def get_clip_model():
    global clip_model, clip_processor
    if clip_model is None or clip_processor is None:
        print("Loading CLIP model...")
        clip_model = CLIPVisionModelWithProjection.from_pretrained(MODEL_ID).to(device)
        clip_processor = CLIPProcessor.from_pretrained(MODEL_ID)
    return clip_model, clip_processor

def get_image_embedding(image_input):
    """Get CLIP embedding for an image from a path or URL."""
    try:
        model, processor = get_clip_model()
        
        if isinstance(image_input, dict):
            image_input = list(image_input.values())[0]
        
        if isinstance(image_input, str):
            image_input = image_input.strip(" '\"")
            if image_input == "current_upload":
                img = Image.open("uploaded_image.png").convert("RGB")
            elif image_input.startswith("http://") or image_input.startswith("https://"):
                response = requests.get(image_input, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                img = Image.open(BytesIO(response.content)).convert("RGB")
            else:
                img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
             raise ValueError(f"Unsupported image input type: {type(image_input)}")
             
        inputs = processor(images=img, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            image_features = outputs.image_embeds
        
        # Normalize
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        return image_features.cpu().numpy()[0]
    except Exception as e:
        import traceback
        with open("vastralens_debug.log", "a") as logf:
            logf.write(f"ERROR processing {image_input}: {e}\n{traceback.format_exc()}\n")
        print(f"Error getting embedding for {image_input}: {e}")
        return f"ERROR: {e}"

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
    if isinstance(embedding, str) and embedding.startswith("ERROR"):
        return f"Could not process the provided image '{image_path_or_url}'. Error details: {embedding}. Please ensure it's a valid image path or URL."
    if embedding is None:
        return f"Could not process the provided image '{image_path_or_url}'. Please ensure it's a valid image path or URL."
        
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
        llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0.2)
    except Exception as e:
        print(f"Error initializing LLM (Did you set GOOGLE_API_KEY?): {e}")
        return None

    tools = [search_visually_similar_sarees]
    system_message = "You are a helpful fashion assistant that can search for visually similar sarees based on images provided. If the user provides a local file path (e.g. C:/... or /tmp/...) or a URL, you MUST pass that EXACT string directly to the `search_visually_similar_sarees` tool. Do NOT attempt to read the file yourself or claim you cannot access it, just call the tool. Describe the products found and provide their details (SKU, price, link)."
    
    agent = create_react_agent(llm, tools, prompt=system_message)
    return agent
