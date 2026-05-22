import chromadb
from chromadb.utils import embedding_functions

def setup_vector_database():
    # Initialize a local persistent ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Use a default embedding function (HuggingFace, lightweight)
    # The default is all-MiniLM-L6-v2 which works well for simple RAG
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="vendor_contracts",
        embedding_function=emb_fn
    )
    
    # Mock documents representing vendor policies and contracts
    documents = [
        "TechCorp Inc. Master Service Agreement: All data must be encrypted at rest and in transit. SLA guarantees 99.99% uptime. Penalty for breach is 10% of monthly fee.",
        "TechCorp Inc. Security Policy: SOC2 Type II compliant. Annual penetration testing required.",
        "CloudServe Terms of Service: Infrastructure services provided 'as-is'. No SLA provided for the Standard tier. Payment terms are net 30.",
        "SecurIT Compliance Addendum: Full GDPR and HIPAA compliance. Dedicated account manager for Enterprise tier. Cyber insurance policy covers up to $5M.",
        "DataLake Analytics Privacy Policy: Data may be shared with third-party partners for marketing purposes. User data is stored in non-encrypted S3 buckets. Opt-out available upon manual request."
    ]
    
    metadatas = [
        {"vendor": "TechCorp Inc.", "doc_type": "contract"},
        {"vendor": "TechCorp Inc.", "doc_type": "policy"},
        {"vendor": "CloudServe", "doc_type": "contract"},
        {"vendor": "SecurIT", "doc_type": "policy"},
        {"vendor": "DataLake Analytics", "doc_type": "policy"}
    ]
    
    ids = [f"doc_{i}" for i in range(len(documents))]
    
    # Insert into Chroma
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"Vector DB setup complete. Inserted {len(documents)} documents into ChromaDB.")

if __name__ == "__main__":
    setup_vector_database()
