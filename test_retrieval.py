from src.retrieval.retriever import Retriever
r = Retriever()
res = r.search("What is the lock-in period of an ELSS tax saver fund?", top_k=3)
for i, c in enumerate(res.chunks):
    print(f"--- Chunk {i+1} Score: {c.score} ---")
    print(c.chunk.get("text", "")[:200])
