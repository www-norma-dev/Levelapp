#!/usr/bin/env python3
"""
Interactive RAG evaluation testing script.
"""
import requests
import json
import sys
import os
import subprocess

# Check if running in WSL/Ubuntu and use Windows IP
if os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
    # Try different Windows host IPs
    try:
        # Method 1: Use hostname
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            # Use the first IP from hostname
            BASE_URL = f"http://{result.stdout.strip().split()[0]}:8080"
        else:
            # Fallback to common Windows host IPs
            BASE_URL = "http://host.docker.internal:8080"
    except:
        # Final fallback
        BASE_URL = "http://localhost:8080"
else:
    BASE_URL = "http://localhost:8080"

print(f"Using API endpoint: {BASE_URL}")

def test_rag_interactive():
    print("RAG Evaluation Interactive Test")
    print("=" * 50)
    
    # Step 1: Initialize and get chunks (hardcoded values)
    page_url = "https://www.ionos.com"
    model_id = "meta-llama/Llama-3.3-70B-Instruct"
    user_prompt = "What are ionos main services?"
    print(f"\nConfig:\n  page_url: {page_url}\n  model_id: {model_id}\n  prompt: {user_prompt}")
    print("\nStep 1: Initializing RAG and scraping page...")
    try:
        init_response = requests.post(
            f"{BASE_URL}/rag/init",
            json={
                "page_url": page_url,
                "model_id": model_id,
                "chunk_size": 500,
            },
            timeout=60,
        )
        
        if init_response.status_code != 200:
            print(f"ERROR: Init failed: {init_response.text}")
            return
            
        init_data = init_response.json()
        print(f"SUCCESS: RAG initialized. Session ID: {init_data['session_id']}")
        
        # Display chunks
        chunks = init_data['chunks']
        print(f"Found {len(chunks)} chunks:\n")
        
        for i, chunk in enumerate(chunks):
            print(f"[{i}] Chunk {i} ({chunk['word_count']} words):")
            print("-" * 40)
            print(chunk['content'])
            print("-" * 40)
            print()
        
        # Interactive chunk selection
        manual_order_input = input("Please select chunks (comma-separated indices, e.g., 0,1,2): ").strip()
        selected_indices = [int(x.strip()) for x in manual_order_input.split(",")]
        
        print(f"Selected chunks: {selected_indices}")
        
        # Step 2: Generate expected answer
        print("\nStep 2: Generating expected answer...")
        expected_response = requests.post(
            f"{BASE_URL}/rag/generate-expected",
            json={
                "session_id": init_data['session_id'],
                "manual_order": selected_indices,  # ← Changed from selected_chunk_indices
                "prompt": user_prompt,
            },
            timeout=90,
        )
        
        if expected_response.status_code != 200:
            print(f"ERROR: Expected answer generation failed: {expected_response.text}")
            return
            
        expected_data = expected_response.json()
        print(f"Generated expected answer: {expected_data['generated_answer']}")  
        
        # Interactive editing
        edit_input = input("\nEdit the expected answer (or press Enter to keep as is): ").strip()
        if edit_input:
            expected_answer = edit_input
        else:
            expected_answer = expected_data['generated_answer'] 
        
        print(f"Final expected answer: {expected_answer}")
        
        # Step 3: Query chatbot and evaluate
        print("\nStep 3: Querying chatbot and evaluating...")
        evaluation_response = requests.post(
            f"{BASE_URL}/rag/evaluate",
            json={
                "session_id": init_data['session_id'],
                "prompt": user_prompt,
                "expected_answer": expected_answer,
                "model_id": model_id,
            },
            timeout=180,
        )
        
        if evaluation_response.status_code != 200:
            print(f"ERROR: Evaluation failed: {evaluation_response.text}")
            return
            
        evaluation_data = evaluation_response.json()
        
        # Display results
        print("\n" + "=" * 50)
        print("EVALUATION RESULTS")
        print("=" * 50)
        print(f"Chatbot Answer: {evaluation_data['chatbot_answer']}")
        print(f"Expected Answer: {evaluation_data['expected_answer']}")
        print()
        print("METRICS:")
        m = evaluation_data['metrics']
        print(f"  BLEU Score: {m['bleu_score']:.4f}")
        print(f"  ROUGE-L F1: {m['rouge_l_f1']:.4f}")
        print(f"  METEOR Score: {m['meteor_score']:.4f}")
        print(f"  BERTScore P/R/F1: {m['bertscore_precision']:.4f}/{m['bertscore_recall']:.4f}/{m['bertscore_f1']:.4f}")
        print()
        print("LLM EVALUATION:")
        judge = evaluation_data['llm_comparison']
        print(f"  Better Answer: {judge['better_answer']}")
        print(f"  Justification: {judge['justification']}")
        if judge.get('missing_facts'):
            print("  Missing Facts:")
            for fact in judge['missing_facts']:
                print(f"   - {fact}")
        
    except requests.exceptions.ConnectTimeout:
        print(f"ERROR: Connection timeout to {BASE_URL}")
        print("Make sure the LevelApp server is running on Windows")
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {BASE_URL}")
        print("Make sure the LevelApp server is running on Windows")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_rag_interactive()