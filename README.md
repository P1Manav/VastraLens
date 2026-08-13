# TailorTalk - Visual Image Search Agent

This repository contains the TailorTalk visual search agent for sarees. 
It uses **OpenAI's CLIP model** to generate high-quality image embeddings and **LangChain** to power a conversational agent that can find visually similar sarees from the provided catalog.

## Technical Stack Choices
1. **Embedding Model**: `openai/clip-vit-base-patch32` (via HuggingFace `transformers`). CLIP is specifically chosen because it natively understands the relationship between text and images and is excellent for zero-shot image retrieval. It captures fine-grained visual details like color, fabric texture, and pattern better than standard CNNs (like ResNet).
2. **Vector Database**: For simplicity and ease of deployment to platforms like Streamlit Cloud, the embeddings are stored locally as a NumPy array (`embeddings.npy`) along with metadata (`metadata.pkl`), and similarities are computed using cosine similarity (dot product). This avoids the need to host and manage an external vector database like Pinecone or Qdrant for a small dataset (~1000 items).
3. **Agent Framework**: LangChain's conversational agent (`CHAT_CONVERSATIONAL_REACT_DESCRIPTION`) with `gemini-1.5-flash` as the reasoning engine.
4. **Frontend**: Streamlit.

## Setup Instructions (Local)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ingest the dataset**:
   If the dataset has not been processed yet, run the ingest script. Ensure `byrappa_tejas_31july.csv` is in the parent directory or update `CSV_PATH` in `ingest.py`.
   ```bash
   python ingest.py
   ```
   *Note: This will download images and generate `embeddings.npy` and `metadata.pkl`. This step must be done before running the app.*

3. **Set your Google API Key**:
   Set your Google API key (for Gemini) in your environment variables.
   ```bash
   # On Windows (Command Prompt)
   set GOOGLE_API_KEY=AIzaSy...
   # On Mac/Linux
   export GOOGLE_API_KEY="AIzaSy..."
   ```

4. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

## Deployment to Streamlit Community Cloud

To deploy this app so it works "out of the box" for the reviewer:

1. Create a GitHub repository and push all files in this directory (including `requirements.txt`, `app.py`, `agent.py`, `ingest.py`, `embeddings.npy`, and `metadata.pkl`).
   *Note: Ensure `embeddings.npy` and `metadata.pkl` are pushed so the reviewer doesn't have to run the ingest script.*
2. Go to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click "New app" and connect your GitHub repository.
4. Select `app.py` as the Main file path.
5. Before deploying, go to **Advanced settings** and add your `GOOGLE_API_KEY` to the Secrets section:
   ```toml
   GOOGLE_API_KEY = "AIzaSy..."
   ```
6. Click **Deploy!** 

Your app will be live and you can share the URL for the final submission.

## Assumptions & Trade-offs
- **CLIP Model Size**: We used the `base-patch32` CLIP model to balance accuracy and memory constraints for Streamlit Cloud deployment (which usually offers ~1GB RAM for free tiers). A larger model (like SigLIP or CLIP-Large) would yield better fine-grained accuracy at the cost of higher latency and memory usage.
- **In-memory Vector Search**: For 1075 images, an in-memory NumPy dot-product is practically instantaneous and drastically simplifies deployment architecture compared to a hosted vector DB (e.g., Pinecone). If the dataset grows to hundreds of thousands of images, migrating to a dedicated vector database is recommended.
# tailortalk_assignment
# tailortalk_assignment
