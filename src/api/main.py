import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

# Limit PyTorch memory overhead before loading sentence-transformers
try:
    import torch
    torch.set_num_threads(1)
except ImportError:
    pass

from src.api.schema import ChatRequest, ChatResponse
from src.guardrails.scanner import PIIScanner, IntentClassifier, RefusalEngine
from src.retrieval.retriever import Retriever
from src.generation.generator import GroqGenerator

app = FastAPI(title="Groww MF RAG API")

# Update CORS to allow requests from the Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins so Vercel can connect seamlessly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
try:
    retriever = Retriever()
    generator = GroqGenerator()
except Exception as e:
    # Handle missing index gracefully during startup/tests
    retriever = None
    generator = GroqGenerator()

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # 1. PII Scan
    if PIIScanner.scan(request.message):
        ans, url = RefusalEngine.get_pii_refusal()
        return ChatResponse(answer=ans, citation_url=url, refused=True)
        
    # 2. Intent Classification
    intent = IntentClassifier.classify(request.message)
    if intent == "advisory":
        ans, url = RefusalEngine.get_advisory_refusal()
        return ChatResponse(answer=ans, citation_url=url, refused=True)
    elif intent == "greeting":
        return ChatResponse(
            answer="Hello! I am the Groww Mutual Fund Assistant. I can help answer factual questions about HDFC Mutual Fund schemes. How can I assist you today?",
            citation_url=None,
            refused=False
        )
    elif intent == "farewell":
        return ChatResponse(
            answer="Goodbye! Feel free to return if you have more questions about HDFC Mutual Funds. Have a great day!",
            citation_url=None,
            refused=False
        )
    elif intent == "gratitude":
        return ChatResponse(
            answer="You're very welcome! Let me know if there's anything else you need help with.",
            citation_url=None,
            refused=False
        )
        
    # 3. Retrieval
    if not retriever:
        raise HTTPException(status_code=500, detail="Retriever not initialized (index may be missing)")
        
    retrieval_result = retriever.search(query=request.message, top_k=3)
    
    # 4. Generation
    # generator.generate returns the full string with the footer and citation appended.
    # To cleanly map to ChatResponse, we need to extract citation_url and footer if present, 
    # but since generator appends them to the string, we can just return the combined string 
    # as the answer, or we could parse it back. For simplicity, we just return the full text.
    # We will attempt to parse out the source if possible.
    
    full_response = generator.generate(retrieval_result)
    
    # Simple parser to extract URL and footer if present
    ans = full_response
    citation_url = None
    footer = None
    
    if "Source: " in ans:
        parts = ans.split("Source: ")
        ans = parts[0].strip()
        url_part = parts[1].strip()
        if "Last updated from sources:" in url_part:
            url_lines = url_part.split("Last updated from sources:")
            citation_url = url_lines[0].strip()
            footer = "Last updated from sources: " + url_lines[1].strip()
        else:
            citation_url = url_part
    
    return ChatResponse(
        answer=ans,
        citation_url=citation_url,
        footer=footer,
        refused=False
    )
