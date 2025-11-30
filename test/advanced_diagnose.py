"""
Advanced Diagnosis Tool for MLB RAG System

This script provides an in-depth diagnosis of the retrieval system 
for a specific player and year to help debug low recall/MRR issues.

Usage:
    python test/advanced_diagnose.py "Player Name" YEAR

Example:
    python test/advanced_diagnose.py "Aaron Judge" 2022
"""

import sys
import os
import json
import pickle
import argparse
from pathlib import Path
import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- Import Core System Components ---
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.query_router import QueryRouter

def get_player_display_name(name: str) -> str:
    """
    Simple helper to normalize player names for ID creation.
    This is a stand-in for the original, missing data processing logic.
    """
    return name.strip()

# --- Configuration ---
DATA_DIR = PROJECT_ROOT / "data"
MLB_DATA_DIR = DATA_DIR / "mlb_data"
RAW_DATA_PATH = DATA_DIR / "raw" / "statcast_batters_enhanced.csv"
TEXT_CHUNKS_PATH = MLB_DATA_DIR / "text_chunks.json"
VECTOR_IDS_PATH = MLB_DATA_DIR / "vector_player_ids.pkl"
BM25_IDS_PATH = MLB_DATA_DIR / "bm25_player_ids.pkl"


def print_header(title):
    """Prints a formatted header."""
    print("\n" + "=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)

def print_subheader(title):
    """Prints a formatted subheader."""
    print("\n" + "-" * 60)
    print(f"▶ {title}")
    print("-" * 60)

def check_file_exists(path, name):
    """Checks if a file exists and prints a status message."""
    if path.exists():
        print(f"✅ {name} found at: {path}")
        return True
    else:
        print(f"❌ {name} not found at: {path}")
        return False

def main(player_name, year):
    """Main diagnosis function."""
    
    print_header(f"Running Diagnosis for: {player_name} ({year})")

    # --- Step 1: Define Expected Ground Truth ---
    expected_player_id = f"{get_player_display_name(player_name)}-{year}"
    print(f"ℹ️ Expected Player ID (Ground Truth): {expected_player_id}")

    # --- Step 2: Check Data Integrity ---
    print_header("Step 1: Data Integrity Check")
    
    # Check for raw data file
    if not check_file_exists(RAW_DATA_PATH, "Raw CSV data"):
        sys.exit(1)
        
    # Check for generated text chunks
    if not check_file_exists(TEXT_CHUNKS_PATH, "Text Chunks"):
        sys.exit(1)

    # Load text chunks and inspect the ground truth chunk
    print_subheader("Inspecting Ground Truth Text Chunk")
    with open(TEXT_CHUNKS_PATH, 'r', encoding='utf-8') as f:
        text_chunks = json.load(f)
    
    ground_truth_chunk = text_chunks.get(expected_player_id)
    
    if ground_truth_chunk:
        print(f"✅ Found ground truth chunk for '{expected_player_id}':")
        print("-" * 60)
        print(ground_truth_chunk)
        print("-" * 60)
    else:
        print(f"❌ CRITICAL: Could not find ground truth chunk for '{expected_player_id}' in text_chunks.json!")
        print("This is likely the root cause of the problem.")
        print("Please run `python src/datapreprocess/rebuild_all_data.py` and check its output.")
        sys.exit(1)

    # --- Step 3: Initialize Retrieval System ---
    print_header("Step 2: Initializing Retrieval System")
    try:
        searcher = HybridSearch()
        router = QueryRouter()
        print("✅ HybridSearch and QueryRouter initialized successfully.")
    except Exception as e:
        print(f"❌ CRITICAL: Failed to initialize retrieval system: {e}")
        sys.exit(1)

    # --- Step 4: Analyze a Test Query ---
    print_header(f"Step 3: Analyzing Test Query")
    
    test_query = f"What was {player_name}'s wOBA in {year}?"
    print(f"ℹ️ Test Query: \"{test_query}\"")

    # Route the query
    print_subheader("Query Routing")
    route_result = router.classify_query(test_query)
    query_type = route_result['query_type']
    print(f"  - Classified as: '{query_type}' (Confidence: {route_result['confidence']:.2f})")
    
    # Perform searches
    print_subheader("Individual Search Results (k=5)")

    # Vector Search
    print("\n--- Vector Search ---")
    vector_results = searcher.vector_search(test_query, k=5)
    for i, res in enumerate(vector_results, 1):
        status = "✅" if res['player_id'] == expected_player_id else "❌"
        print(f"  {i}. {status} {res['player_id']} (Score: {res['score']:.4f})")

    # BM25 Search
    print("\n--- BM25 Search ---")
    bm25_results = searcher.bm25_search(test_query, k=5)
    for i, res in enumerate(bm25_results, 1):
        status = "✅" if res['player_id'] == expected_player_id else "❌"
        print(f"  {i}. {status} {res['player_id']} (Score: {res['score']:.4f})")

    # Hybrid Search
    print_subheader("Hybrid Search Result (k=5)")
    hybrid_results = searcher.search(test_query, k=5, query_type=query_type)
    
    found_rank = -1
    for i, res in enumerate(hybrid_results, 1):
        status = "✅" if res['player_id'] == expected_player_id else "❌"
        if status == "✅":
            found_rank = i
        print(f"  {i}. {status} {res['player_id']} (Score: {res['score']:.4f})")
        # Print the content of the retrieved chunk for analysis
        print("      " + "-"*50)
        retrieved_chunk = text_chunks.get(res['player_id'], "Chunk not found!").replace('\n', ' ')
        print(f"      Content: {retrieved_chunk[:150]}...")
        print("      " + "-"*50)


    # --- Step 5: Final Summary ---
    print_header("Diagnosis Summary")
    if found_rank != -1:
        print(f"✅ SUCCESS: Ground truth '{expected_player_id}' was found at rank {found_rank} in the final hybrid search.")
        if found_rank > 1:
            print("  - NOTE: Although found, it's not the top result. Analyze the scores and content of higher-ranked results to understand why.")
    else:
        print(f"❌ FAILURE: Ground truth '{expected_player_id}' was NOT found in the top 5 hybrid search results.")
        print("  - Recommendation: ")
        print("    1. Check if Vector Search OR BM25 Search found the document. If one did and the other didn't, the hybrid weighting might be off for this query type.")
        print("    2. If neither found it, the query is too different from the ground truth text chunk. Consider revising the chunk generation logic in `rebuild_all_data.py`.")

    print("\n" + "=" * 80)
    print("Diagnosis Complete.")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Diagnosis Tool for the MLB RAG System.")
    parser.add_argument("player_name", type=str, help="The full name of the player to diagnose (e.g., 'Aaron Judge').")
    parser.add_argument("year", type=int, help="The season year to diagnose (e.g., 2022).")
    
    args = parser.parse_args()
    
    main(args.player_name, args.year)
