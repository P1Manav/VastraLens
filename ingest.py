import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import torch
import pickle
import numpy as np
from transformers import CLIPProcessor, CLIPVisionModelWithProjection
from tqdm import tqdm

# Configuration
CSV_PATH = "../byrappa_tejas_31july.csv"
EMBEDDINGS_PATH = "embeddings.npy"
METADATA_PATH = "metadata.pkl"
MODEL_ID = "openai/clip-vit-base-patch32"

print(f"Loading model {MODEL_ID}...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPVisionModelWithProjection.from_pretrained(MODEL_ID).to(device)
processor = CLIPProcessor.from_pretrained(MODEL_ID)

print("Loading dataset...")
df = pd.read_csv(CSV_PATH)

embeddings = []
metadata = []

print(f"Processing {len(df)} images...")
# df = df.head(10) # Uncomment for testing

for index, row in tqdm(df.iterrows(), total=len(df)):
    img_url = row.get("image_url")
    if pd.isna(img_url):
        continue
    
    try:
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        
        # Preprocess and get embedding
        inputs = processor(images=img, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model(**inputs)
            image_features = outputs.image_embeds
        
        # Normalize the embedding for cosine similarity
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        emb = image_features.cpu().numpy()[0]
        
        embeddings.append(emb)
        metadata.append({
            "id": index,
            "Name": row.get("Name", "Unknown"),
            "SKU": row.get("SKU", "Unknown"),
            "Price": row.get("Discounted Price", row.get("Retail Price", 0)),
            "image_url": img_url,
            "Website Link": row.get("Website Link", "")
        })
    except Exception as e:
        # print(f"Failed to process image {img_url}: {e}")
        continue

if embeddings:
    print(f"Saving embeddings for {len(embeddings)} items...")
    embeddings_np = np.array(embeddings).astype("float32")
    
    np.save(EMBEDDINGS_PATH, embeddings_np)
    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)
    
    print("Done! Embeddings and metadata saved.")
else:
    print("No embeddings were generated.")
