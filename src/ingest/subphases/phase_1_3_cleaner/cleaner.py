import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Cleaner:
    def __init__(self):
        self.boilerplate_terms = [
            "Mutual fund investments are subject to market risks",
            "You may also like",
            "Read all scheme related documents carefully"
        ]

    def clean(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        cleaned_sections = []
        for section in doc.get("sections", []):
            name = section["name"]
            text = section["text"]
            
            if "FAQ" in name.upper() or "FREQUENTLY ASKED" in name.upper():
                continue
                
            for term in self.boilerplate_terms:
                text = text.replace(term, "")
                
            text = unicodedata.normalize("NFKC", text)
            
            text = re.sub(r'\bRs\.?\s*', '₹', text, flags=re.IGNORECASE)
            text = re.sub(r'\bINR\b', '₹', text, flags=re.IGNORECASE)
            text = text.replace("–", "-").replace("—", "-")
            text = text.replace('"', '"').replace('"', '"')
            
            text = re.sub(r'\s+', ' ', text).strip()
            
            if "Fund Manager" in name:
                text = text.split('.')[0] + '.'
            if "Fund House" in name:
                text = re.sub(r'[\w\.-]+@[\w\.-]+', '', text)
                text = re.sub(r'(?i)website:?\s*\S+', '', text)
                text = re.sub(r'(?i)phone:?\s*\S+', '', text)
                
            if text:
                cleaned_sections.append({"name": name, "text": text})

        return {
            "scheme_id": doc["scheme_id"],
            "source_url": doc["source_url"],
            "fetched_at": doc["fetched_at"],
            "sections": cleaned_sections,
            "must_have_anchors": doc["must_have_anchors"],
            "extraction_health": doc["extraction_health"]
        }


if __name__ == "__main__":
    import glob
    import os
    cleaner = Cleaner()
    processed_dirs = glob.glob("data/processed/*")
    for pdir in processed_dirs:
        scheme_id = os.path.basename(pdir)
        ext_path = os.path.join(pdir, "extracted.json")
        if not os.path.exists(ext_path):
            continue
        with open(ext_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
            
        cleaned = cleaner.clean(doc)
        with open(os.path.join(pdir, "cleaned.json"), "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)
        print(f"Cleaned {scheme_id} -> {len(cleaned['sections'])} sections")

