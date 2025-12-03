# tools/search_memory.py
import os
import sys
from pinecone import Pinecone

# 1. Configuration
API_KEY = os.getenv("PINECONE_API_KEY") # Ensure this is set in your terminal/env
INDEX_NAME = "gemini-code-assistant"    # Must match your ingest script

def search(query):
    if not API_KEY:
        print("Error: PINECONE_API_KEY environment variable not set.")
        return

    # 2. Initialize Pinecone
    pc = Pinecone(api_key=API_KEY)
    index = pc.Index(INDEX_NAME)

    # 3. Embed the query (Using Gemini Embeddings via LangChain or direct API)
    # NOTE: For simplicity, the agent often needs the *same* embedding logic as ingestion.
    # If you used 'models/embedding-001' in ingestion, you need it here.
    # Below is a placeholder using a mock or you can import your embedding function.
    
    # -- OPTION A: If you have the embedding logic in a shared module, import it --
    # from my_project.embeddings import get_embedding
    # vector = get_embedding(query)
    
    # -- OPTION B: Using LangChain (easiest if installed) --
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GOOGLE_API_KEY"))
        vector = embeddings.embed_query(query)
    except ImportError:
        print("Error: langchain-google-genai not installed or GOOGLE_API_KEY not set.")
        return

    # 4. Query Pinecone
    results = index.query(
        vector=vector,
        top_k=5,
        include_metadata=True
    )

    # 5. Print results for the Agent to read
    print(f"\n--- Search Results for: '{query}' ---\n")
    for match in results['matches']:
        score = match['score']
        source = match['metadata'].get('source', 'Unknown')
        text = match['metadata'].get('text', '')[:500] # Snippet only
        print(f"Source: {source} (Score: {score:.2f})")
        print(f"Content: {text}...\n")
        print("-" * 30)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/search_memory.py 'your query here'")
        sys.exit(1)
    
    query_text = sys.argv[1]
    search(query_text)
