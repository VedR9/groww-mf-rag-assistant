import json
import logging
from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup
import trafilatura

logger = logging.getLogger(__name__)

class Extractor:
    def __init__(self):
        # Must-have anchors from architecture.md
        self.must_have_anchors = ["Expense Ratio", "Exit Load", "Min SIP", "Scheme Details", "Riskometer", "Benchmark", "FAQs"]
        
        # Additional sections to extract if present
        self.target_sections = ["Fund Manager", "Fund House", "About", "Overview", "Minimum Investments", "Fund Details", "Exit Load and Tax"]

    def extract(self, html: str, scheme_id: str, source_url: str, fetched_at: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        sections = []
        anchors_found = {anchor: False for anchor in self.must_have_anchors}
        
        # Extract general page text first
        text = soup.get_text(separator="\n", strip=True)
        
        # Let's find specific sections by looking at all headers/divs with specific text
        # Since we don't know the exact DOM of Groww, we will do a heuristic approach
        # Extracting key facts directly
        def extract_table_facts():
            facts = {}
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = row.find_all(["th", "td"])
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True)
                        val = cells[1].get_text(strip=True)
                        facts[key] = val
            return facts
        
        # Fallback text search for facts
        def find_fact(keyword):
            elem = soup.find(lambda tag: tag.name in ['div', 'span', 'td', 'th', 'h2', 'h3'] and tag.string and keyword.lower() in tag.string.lower())
            if elem:
                # Get parent text or next sibling
                parent = elem.find_parent('div')
                if parent:
                    return parent.get_text(separator=" ", strip=True)
            return None

        # Build sections heuristically
        for section_name in self.must_have_anchors + self.target_sections:
            if section_name == "Riskometer":
                svgs = soup.find_all('svg')
                found = False
                for svg in svgs:
                    alt = svg.get('aria-label') or svg.get('alt')
                    if alt and "risk" in alt.lower():
                        sections.append({"name": "Riskometer", "text": alt})
                        anchors_found["Riskometer"] = True
                        found = True
                        break
                continue

            # Look for explicit headers
            header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'div'] and tag.text and section_name.lower() in tag.text.lower() and len(tag.text) < 50)
            if header:
                if section_name in anchors_found:
                    anchors_found[section_name] = True
                    
                parent = header.find_parent('section') or header.find_parent('div')
                if parent:
                    sections.append({"name": section_name, "text": parent.get_text(separator=" ", strip=True)})
                else:
                    sections.append({"name": section_name, "text": header.get_text(separator=" ", strip=True)})
            else:
                # Text check for must-have
                if section_name in anchors_found and section_name.lower() in text.lower():
                    anchors_found[section_name] = True
                    # Try to extract the sentence containing it
                    for sentence in text.split('\n'):
                        if section_name.lower() in sentence.lower():
                            sections.append({"name": section_name, "text": sentence})
                            break
                            
        # If "Fund Details" is missing, let's try to extract table facts
        table_facts = extract_table_facts()
        if table_facts:
            table_text = " ".join([f"{k} {v}" for k, v in table_facts.items()])
            sections.append({"name": "Fund Details", "text": table_text})
            
            for k in table_facts:
                for anchor in anchors_found:
                    if anchor.lower() in k.lower():
                        anchors_found[anchor] = True
        
        # Trafilatura for "About" or Main Body if nothing else worked well
        extracted_text = trafilatura.extract(html, include_tables=True)
        if extracted_text:
            sections.append({"name": "Main Body", "text": extracted_text})

        # Calculate health: if >= 4 must have anchors present, it's ok
        health = "ok" if sum(anchors_found.values()) >= 4 else "degraded"
        
        # Remove duplicate section names (keep first)
        seen = set()
        unique_sections = []
        for s in sections:
            if s["name"] not in seen:
                seen.add(s["name"])
                unique_sections.append(s)

        return {
            "scheme_id": scheme_id,
            "source_url": source_url,
            "fetched_at": fetched_at,
            "sections": unique_sections,
            "must_have_anchors": anchors_found,
            "extraction_health": health
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import glob
    import os
    extractor = Extractor()
    raw_dirs = glob.glob("data/raw/*")
    for raw_dir in raw_dirs:
        scheme_id = os.path.basename(raw_dir)
        meta_path = os.path.join(raw_dir, "meta.json")
        if not os.path.exists(meta_path):
            continue
        with open(meta_path, "r") as f:
            meta = json.load(f)
        html_files = glob.glob(os.path.join(raw_dir, "*.html"))
        if not html_files:
            continue
        html_file = html_files[0]
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()
        
        extracted = extractor.extract(html, scheme_id, meta["url"], meta["fetched_at"])
        out_dir = Path("data/processed") / scheme_id
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "extracted.json", "w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2)
        logger.info(f"Extracted {scheme_id} -> extraction_health: {extracted['extraction_health']}")
