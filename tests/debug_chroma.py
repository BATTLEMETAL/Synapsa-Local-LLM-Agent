try:
    print("Importing chromadb.utils.embedding_functions...")
    from chromadb.utils import embedding_functions
    print("✅ Import successful.")
    
    print("Attempting to instantiate SentenceTransformerEmbeddingFunction...")
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    print("✅ Instantiation successful.")
    
    val = ef(["test"])
    print(f"✅ Embedding successful. Vector length: {len(val[0])}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
