import pytest
from src.retrieval.models import RetrievalResult, RetrievedChunk
from src.generation.generator import GroqGenerator

def test_short_circuit_pii():
    generator = GroqGenerator()
    # Ensure it short circuits PII rejections without hitting LLM (no API key needed)
    res = RetrievalResult(
        query="My PAN is 123",
        scheme_id=None,
        chunks=[],
        status="refused_pii",
        message="I cannot process PII."
    )
    answer = generator.generate(res)
    assert answer == "I cannot process PII."

def test_short_circuit_not_found():
    generator = GroqGenerator()
    res = RetrievalResult(
        query="What is the NAV?",
        scheme_id=None,
        chunks=[],
        status="not_found",
        message="I couldn't find this on the scheme pages we use"
    )
    answer = generator.generate(res)
    assert answer == "I couldn't find this on the scheme pages we use"

def test_post_validation():
    generator = GroqGenerator()
    # Test valid string
    assert generator._post_validate("The expense ratio is 0.77%.") == True
    
    # Test banned words
    assert generator._post_validate("I highly recommend investing in this fund.") == False
    assert generator._post_validate("This is better than large cap.") == False
    assert generator._post_validate("You should invest here.") == False

def test_mock_generation_url_append():
    # When no API key is set, it uses the mock response and appends the best URL
    generator = GroqGenerator()
    
    chunk = RetrievedChunk(
        chunk={"text": "Expense is 1%", "source_url": "https://hdfc.com/mid-cap", "section_title": "Expense"},
        score=0.9,
        rank=1
    )
    
    res = RetrievalResult(
        query="Expense?",
        scheme_id="scheme-A",
        chunks=[chunk],
        status="success"
    )
    
    answer = generator.generate(res)
    assert "[MOCK GROQ LLM]" in answer
    assert "https://hdfc.com/mid-cap" in answer
