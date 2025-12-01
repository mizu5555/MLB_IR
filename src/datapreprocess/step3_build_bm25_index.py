import json
import os
import pickle
import jieba
import argparse
from pathlib import Path
from rank_bm25 import BM25Okapi


# ------------------------------------------------------------
# 中英混合 tokenizer
# ------------------------------------------------------------
def mixed_tokenize(text):
    tokens = []
    buff = []

    for ch in text:
        if ch.isalnum() or ch in [".", "%", "-", "/", "+"]:
            buff.append(ch)
        else:
            if buff:
                tokens.append("".join(buff))
                buff = []
            if '\u4e00' <= ch <= '\u9fff':
                tokens.extend(list(jieba.cut(ch)))

    if buff:
        tokens.append("".join(buff))

    return tokens


# ------------------------------------------------------------
# 建立 BM25 index
# ------------------------------------------------------------
def build_bm25():
    ROOT = Path(__file__).resolve().parents[2]

    input_file = ROOT / "data" / "mlb_data_adv" / "training_data.json"
    out_index = ROOT / "data" / "mlb_data_adv" / "bm25_index.pkl"
    out_corpus = ROOT / "data" / "mlb_data_adv" / "bm25_corpus.pkl"
    out_ids = ROOT / "data" / "mlb_data_adv" / "bm25_ids.pkl"

    print("📘 Loading training_data.json ...")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    corpus_tokens = []
    ids = []

    print("🔍 Tokenizing records (BM25 keyword_text)...")
    for idx, item in enumerate(data):
        ids.append(item["id"])
        tokens = mixed_tokenize(item["keyword_text"])
        corpus_tokens.append(tokens)

        if idx % 300 == 0:
            print(f"  -> processed {idx} items")

    print("🏗 Building BM25 index ...")
    bm25 = BM25Okapi(corpus_tokens)

    print("💾 Saving BM25 index and metadata ...")
    with open(out_index, "wb") as f:
        pickle.dump(bm25, f)

    with open(out_corpus, "wb") as f:
        pickle.dump(corpus_tokens, f)

    with open(out_ids, "wb") as f:
        pickle.dump(ids, f)

    print("✅ Step3 Done!")
    print(f"   - {out_index}")
    print(f"   - {out_corpus}")
    print(f"   - {out_ids}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dummy", type=str, default="", help="(reserved)")
    args = parser.parse_args()

    build_bm25()
