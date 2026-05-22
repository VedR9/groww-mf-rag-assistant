import hashlib
import json
import logging
import re
import uuid
import os
import glob
from typing import Dict, Any, List, Iterable
import yaml

logger = logging.getLogger(__name__)

class Chunker:
    def __init__(self, amc_config_path: str = "config/amc.yaml"):
        self.scheme_map = {}
        try:
            with open(amc_config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                for scheme in config.get("schemes", []):
                    self.scheme_map[scheme["slug"]] = scheme["name"]
        except Exception as e:
            logger.warning(f"Failed to load amc.yaml: {e}")

    def _get_tokens(self, text: str) -> int:
        return len(text.split())

    def _hash(self, text: str) -> str:
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _split_long_section(self, text: str, soft_cap: int = 150, hard_cap: int = 200, overlap: int = 30) -> List[str]:
        parts = re.split(r'(\.\s+|\|\s*\|\s*)', text)
        
        units = []
        current_unit = ""
        for part in parts:
            current_unit += part
            if re.match(r'^(\.\s+|\|\s*\|\s*)$', part) or not part:
                if current_unit.strip():
                    units.append(current_unit.strip())
                current_unit = ""
        if current_unit.strip():
            units.append(current_unit.strip())

        chunks = []
        current_chunk = ""
        last_unit = ""
        
        for unit in units:
            if not current_chunk:
                current_chunk = unit
            else:
                combined = current_chunk + " " + unit
                if self._get_tokens(combined) > soft_cap and self._get_tokens(current_chunk) > 0:
                    chunks.append(current_chunk)
                    if self._get_tokens(last_unit) <= overlap:
                        current_chunk = last_unit + " " + unit
                    else:
                        current_chunk = unit
                else:
                    current_chunk = combined
            last_unit = unit
                    
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def chunk(self, doc: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        scheme_id = doc.get("scheme_id", "")
        scheme_name = self.scheme_map.get(scheme_id, scheme_id.replace("-", " ").title())
        
        all_text = " ".join([s["text"] for s in doc.get("sections", [])])
        stable_hash = self._hash(all_text)
        
        chunks = []
        for section in doc.get("sections", []):
            name = section.get("name", "Unknown")
            text = section.get("text", "")
            
            if self._get_tokens(text) < 5:
                continue
                
            if name in ["Main Body", "About"]:
                text_chunks = self._split_long_section(text)
            else:
                text_chunks = [text]
                
            for tc in text_chunks:
                if self._get_tokens(tc) < 5:
                    continue
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "scheme_id": scheme_id,
                    "scheme_name": scheme_name,
                    "doc_type": "Product_Page",
                    "source_url": doc.get("source_url", ""),
                    "section": name,
                    "section_source": "html_section",
                    "last_updated": doc.get("fetched_at", ""),
                    "content_hash": self._hash(tc),
                    "stable_content_hash": stable_hash,
                    "text": tc
                })
                
        return chunks


if __name__ == "__main__":
    import glob
    import os
    chunker = Chunker()
    processed_dirs = glob.glob("data/processed/*")
    total_chunks = 0
    for pdir in processed_dirs:
        if not os.path.isdir(pdir):
            continue
        cleaned_path = os.path.join(pdir, "cleaned.json")
        if not os.path.exists(cleaned_path):
            continue
            
        with open(cleaned_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
            
        chunks = list(chunker.chunk(doc))
        
        chunks_path = os.path.join(pdir, "chunks.jsonl")
        with open(chunks_path, "w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c) + "\n")
                
        print(f"Chunked {os.path.basename(pdir)} -> {len(chunks)} chunks")
        total_chunks += len(chunks)
        
    print(f"Total chunks generated: {total_chunks}")

