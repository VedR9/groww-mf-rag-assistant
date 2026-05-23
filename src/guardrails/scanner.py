import re
from typing import Tuple, Optional

class PIIScanner:
    """Scans queries for personally identifiable information (PII)."""
    
    # Regex patterns for Indian context
    PATTERNS = {
        "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
        "Aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
        "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "Phone": r"\b(?:\+?91|0)?[6789]\d{9}\b",
        "Account": r"\b\d{9,18}\b"
    }

    @classmethod
    def scan(cls, query: str) -> bool:
        """Returns True if PII is detected, False otherwise."""
        for pattern in cls.PATTERNS.values():
            if re.search(pattern, query, re.IGNORECASE):
                return True
        return False

class IntentClassifier:
    """Classifies if a query is factual (allowed), advisory (blocked), or a greeting."""
    
    ADVISORY_PATTERNS = [
        r"\bshould (i|we) invest\b",
        r"\bwhich is better\b",
        r"\brecommend\b",
        r"\bgood investment\b",
        r"\bbuy or sell\b",
        r"\bbest (mutual )?fund\b",
        r"\bwill it go up\b",
        r"\bpredict\b",
        r"\bsuggest\b",
        r"\bgood.*fund\b",
        r"\bwhich.*fund\b"
    ]

    GREETING_PATTERNS = [
        r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening|howdy)\b",
        r"^(how are you|what's up|whats up)\b"
    ]
    
    @classmethod
    def classify(cls, query: str) -> str:
        """Returns 'advisory', 'greeting', or 'factual'."""
        query_lower = query.lower().strip()
        
        # Check greetings first
        for pattern in cls.GREETING_PATTERNS:
            if re.search(pattern, query_lower):
                return "greeting"
                
        # Check advisory
        for pattern in cls.ADVISORY_PATTERNS:
            if re.search(pattern, query_lower):
                return "advisory"
                
        return "factual"

class RefusalEngine:
    """Handles templated refusals for advisory or PII queries."""
    
    # We use one of the 5 allowed URLs for educational linking.
    DEFAULT_URL = "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"
    
    @classmethod
    def get_pii_refusal(cls) -> Tuple[str, Optional[str]]:
        """Returns (Refusal message, citation_url)"""
        return (
            "For your security, please do not share personal identifiers like PAN, account numbers, or phone numbers. I cannot process this request.",
            None
        )
        
    @classmethod
    def get_advisory_refusal(cls) -> Tuple[str, Optional[str]]:
        """Returns (Refusal message, citation_url)"""
        return (
            "I am a facts-only assistant and cannot provide investment advice, fund recommendations, or performance predictions. For factual information about mutual fund structures, you can read more here.",
            cls.DEFAULT_URL
        )
