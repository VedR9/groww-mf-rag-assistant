"""Phase 3 Generation using Groq."""

import os
import re
from typing import Optional
from groq import Groq
from src.retrieval.models import RetrievalResult

class GroqGenerator:
    def __init__(self, model_name: Optional[str] = None):
        # Relies on GROQ_API_KEY being set in the environment
        self.client = Groq() if os.environ.get("GROQ_API_KEY") else None
        self.model_name = model_name or os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
        
        self.system_prompt = (
            "You are a strict, factual assistant for Groww Mutual Funds. "
            "You must only answer based on the provided context. "
            "Do NOT provide financial advice. "
            "Keep your answer to a maximum of 3 sentences. "
            "Never invent facts or URLs."
        )
        
        self.banned_words = [r"\brecommend", r"\bbetter\b", r"\bbuy\b", r"\bsell\b", r"\bshould invest\b"]
        
    def _post_validate(self, text: str) -> bool:
        """Returns True if valid (no banned words), False if it contains advice."""
        text_lower = text.lower()
        for pattern in self.banned_words:
            if re.search(pattern, text_lower):
                return False
        return True

    def generate(self, retrieval_result: RetrievalResult) -> str:
        """Generates an answer based on the retrieval result."""
        
        # 1. Short-circuit logic for misses and PII
        if retrieval_result.status != "success":
            return retrieval_result.message or "I couldn't find this on the scheme pages we use."
            
        # 2. Context Packing
        context_blocks = []
        best_url = None
        max_date = None
        
        for i, c in enumerate(retrieval_result.chunks):
            chunk_data = c.chunk
            if i == 0:
                best_url = chunk_data.get("source_url")
            
            # Find the max date for the footer
            chunk_date = chunk_data.get("last_updated") or chunk_data.get("fetched_at")
            if chunk_date:
                if not max_date or chunk_date > max_date:
                    max_date = chunk_date
                    
            context_blocks.append(f"--- Section: {chunk_data.get('section_title', 'Unknown')} ---\n{chunk_data.get('text', '')}")
            
        context_str = "\n\n".join(context_blocks)
        
        user_prompt = f"Context:\n{context_str}\n\nQuery: {retrieval_result.query}"
        
        footer = f"\n\nLast updated from sources: {max_date[:10] if max_date else 'Unknown'}"
        
        # In testing environments without an API key, we return a mock response
        if not self.client:
            return f"[MOCK GROQ LLM] Based on context: {context_str[:50]}...\n\nSource: {best_url}{footer}"
            
        # 3. Groq Inference
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=256
            )
            llm_text = response.choices[0].message.content.strip()
            
            # 4. Post-Validation
            if not self._post_validate(llm_text):
                return f"I cannot provide financial recommendations or subjective comparisons.\n\nSource: {best_url}{footer}"
                
            # 5. Citation Attachment
            if best_url:
                llm_text += f"\n\nSource: {best_url}"
                
            llm_text += footer
            
            return llm_text
            
        except Exception as e:
            return f"Error during generation: {str(e)}"
