import sqlite3
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

class EpisodicMemoryDB:
    """Short-term memory using SQLite for recent interactions."""
    def __init__(self, db_path: str = 'episodic_memory.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()

    def add_event(self, user_id: str, query: str, response: str, timestamp: Optional[datetime] = None):
        ts = timestamp or datetime.utcnow()
        self.conn.execute(
            'INSERT INTO memory (user_id, query, response, timestamp) VALUES (?, ?, ?, ?)',
            (user_id, query, response, ts)
        )
        self.conn.commit()

    def get_recent(self, user_id: str, limit: int = 10) -> List[Tuple[str, str, str]]:
        cur = self.conn.execute(
            'SELECT query, response, timestamp FROM memory WHERE user_id=? ORDER BY timestamp DESC LIMIT ?',
            (user_id, limit)
        )
        return cur.fetchall()

    def close(self):
        self.conn.close()

class SemanticMemoryChroma:
    """Long-term memory using ChromaDB for semantic search and retrieval."""
    def __init__(self, persist_dir: str = 'chroma_semantic_memory'):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.Client(Settings(persist_directory=persist_dir))
        self.collection = self.client.get_or_create_collection('semantic_memory')
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()

    def add_profile(self, user_id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        embedding = self.embed_fn([text])[0]
        meta = {"user_id": user_id}
        if metadata:
            meta.update(metadata)
        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[meta]
        )

    def search(self, user_id: str, query: str, n_results: int = 3) -> List[str]:
        embedding = self.embed_fn([query])[0]
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where={"user_id": user_id}
        )
        return results.get('documents', [])

    def clear_user_data(self, user_id: str):
        self.collection.delete(where={"user_id": user_id})

# Example usage:
if __name__ == "__main__":
    # Episodic (short-term)
    epi = EpisodicMemoryDB()
    epi.add_event('user1', 'What is Rome?', 'Rome is the capital of Italy.')
    print('Recent:', epi.get_recent('user1'))
    epi.close()

    # Semantic (long-term)
    sem = SemanticMemoryChroma()
    sem.add_profile('user1', 'User likes history, travel, and Italian culture.')
    print('Semantic search:', sem.search('user1', 'Tell me about Italy'))
