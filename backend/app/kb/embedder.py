"""Not used, by design (H15).

Retrieval is keyword matching over a small, reviewed body of text (`app/explain/retriever.py`): a
few dozen passages per language, where embeddings would add a model, a vector store and a similarity
threshold without making the answer better. If the knowledge base grows to the point where keywords
start missing passages, this is where an embedder would go.
"""
