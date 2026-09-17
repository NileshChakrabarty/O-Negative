#!/usr/bin/env python3
"""
RAG Engine for O-Negative

Handles:
1. Loading and chunking eligibility rules
2. Embedding rules using sentence-transformers
3. Storing in ChromaDB for fast retrieval
4. Retrieving relevant rules for agent queries
"""

import os
import chromadb

from backend.config import CHROMA_DB_PATH
from backend.knowledge.eligibility_rules import get_all_rules

# Determine embedding model
USE_OPENAI_EMBEDDINGS = os.getenv("OPENAI_API_KEY", "") != ""

if USE_OPENAI_EMBEDDINGS:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    EMBEDDING_MODEL = "text-embedding-3-small"
else:
    # Fall back to sentence-transformers (local, no API key needed)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    EMBEDDING_MODEL = "all-MiniLM-L6-v2 (local)"

PRIMARY_COLLECTION_NAME = "o_negative_eligibility"
LEGACY_COLLECTION_NAME = "rakt_setu_eligibility"


class RAGEngine:
    """Retrieval-Augmented Generation engine for blood donation eligibility rules."""
    
    def __init__(self):
        """Initialize ChromaDB and load eligibility rules."""
        # Create ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # Prefer existing populated collection or primary
        existing = [c.name for c in self.client.list_collections()]
        target_name = PRIMARY_COLLECTION_NAME
        if LEGACY_COLLECTION_NAME in existing and PRIMARY_COLLECTION_NAME not in existing:
            target_name = LEGACY_COLLECTION_NAME

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=target_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load rules
        self.rules = get_all_rules()
        print(f"Loaded {len(self.rules)} eligibility rules")
    
    def embed_text(self, text: str) -> list:
        """
        Embed text using OpenAI or local sentence-transformers.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (list of floats)
        """
        if USE_OPENAI_EMBEDDINGS:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        else:
            embedding = model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
    
    def populate_collection(self):
        """
        Embed all eligibility rules and store in ChromaDB.
        Only run once to populate the collection.
        """
        if self.collection.count() > 0:
            print(f"✓ Collection already populated with {self.collection.count()} rules")
            return
        
        print(f"Embedding and storing {len(self.rules)} rules in ChromaDB...")
        
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for i, rule in enumerate(self.rules):
            rule_id = rule["id"]
            text = rule["text"]
            source = rule["source"]
            category = rule["category"]
            
            embedding = self.embed_text(text)
            
            ids.append(rule_id)
            documents.append(text)
            embeddings.append(embedding)
            metadatas.append({
                "source": source,
                "category": category,
                "rule_id": rule_id
            })
            
            if (i + 1) % 5 == 0:
                print(f"  Embedded {i + 1}/{len(self.rules)} rules...")
        
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"✓ Successfully stored {len(self.rules)} rules in ChromaDB")
    
    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        """
        Retrieve relevant eligibility rules for a query.
        
        Args:
            query: Query text (e.g., "can I donate if I'm on antibiotics?")
            k: Number of results to return (default 5)
        
        Returns:
            List of {rule_id, text, source, category, relevance_score}
        """
        query_embedding = self.embed_text(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        
        retrieved_rules = []
        
        if results["ids"] and results["ids"][0]:
            for i, rule_id in enumerate(results["ids"][0]):
                document = results["documents"][0][i]
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                relevance_score = 1 - distance
                
                retrieved_rules.append({
                    "rule_id": rule_id,
                    "text": document,
                    "source": metadata.get("source", "Unknown"),
                    "category": metadata.get("category", "Unknown"),
                    "relevance_score": max(0, relevance_score)
                })
        
        return retrieved_rules
    
    def retrieve_by_category(self, category: str, k: int = 10) -> list[dict]:
        """
        Retrieve rules by category.
        
        Args:
            category: Category name (e.g., "Medication restrictions")
            k: Number of results
        
        Returns:
            List of rules in that category
        """
        results = self.collection.get(
            where={"category": category},
            limit=k,
            include=["documents", "metadatas"]
        )
        
        retrieved_rules = []
        if results["ids"]:
            for i, rule_id in enumerate(results["ids"]):
                retrieved_rules.append({
                    "rule_id": rule_id,
                    "text": results["documents"][i],
                    "source": results["metadatas"][i].get("source", "Unknown"),
                    "category": results["metadatas"][i].get("category", "Unknown"),
                    "relevance_score": 1.0
                })
        
        return retrieved_rules


_rag_engine = None

def get_rag_engine() -> RAGEngine:
    """Get or create the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
        _rag_engine.populate_collection()
    return _rag_engine
