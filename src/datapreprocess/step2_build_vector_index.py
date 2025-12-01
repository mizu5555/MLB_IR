import json
import argparse
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


def build_vector_index(embedding_model):
    ROOT = Path(__file__).resolve().parents[2]
    INPUT_FILE = ROOT / "data" / "mlb_data_adv" / "training_data.json"

    OUTPUT_DIR = ROOT / "data" / "mlb_data_adv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("📘 Loading training_data.json ...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        training_data = json.load(f)

    print(f"📦 Loaded {len(training_data)} records")

    # --------------------------------------------------------
    # Load embedding model
    # --------------------------------------------------------
    print(f"🔁 Initializing embedding model: {embedding_model}")
    model = SentenceTransformer(embedding_model)

    embeddings = []
    vector_ids = []  # store **index (int)**, NOT string id

    # --------------------------------------------------------
    # Compute embeddings
    # --------------------------------------------------------
    print("🔁 Encoding records ...")

    for idx, item in enumerate(training_data):
        text = item["embedding_text"]
        emb = model.encode(text)
        embeddings.append(emb)
        vector_ids.append(idx)   # <<<<<< KEY FIX HERE

    embeddings = np.array(embeddings).astype("float32")
    dim = embeddings.shape[1]

    print(f"📐 Embedding dim = {dim}, shape = {embeddings.shape}")

    # --------------------------------------------------------
    # Save embeddings
    # --------------------------------------------------------
    np.save(OUTPUT_DIR / "vector_embeddings.npy", embeddings)

    with open(OUTPUT_DIR / "vector_ids.json", "w", encoding="utf-8") as f:
        json.dump(vector_ids, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------------
    # Build FAISS index
    # --------------------------------------------------------
    print("🔁 Building FAISS index ...")
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, str(OUTPUT_DIR / "vector_index.faiss"))
    print("✅ Vector index saved to vector_index.faiss")
    print("✅ Step2 done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str,
                        default="sentence-transformers/all-MiniLM-L6-v2", 
                        help="Embedding model name")
    # sentence-transformers/all-MiniLM-L6-v2
    # 中英混
    # intfloat/multilingual-e5-base
    # intfloat/multilingual-e5-large
    # 英文
    # sentence-transformers/all-mpnet-base-v2
    args = parser.parse_args()

    build_vector_index(args.model)
