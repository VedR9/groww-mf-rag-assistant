import os
import subprocess
import logging
import json
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_step(name, script_path):
    logger.info(f"--- Running {name} ---")
    result = subprocess.run(["python3", script_path], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"{name} failed:\n{result.stderr}")
        return False
    logger.info(f"{name} completed.")
    return True

if __name__ == "__main__":
    logger.info("Starting full data refresh pipeline...")
    
    steps = [
        ("Fetcher", "src/mf_faq/ingestion/fetcher.py"),
        ("Extractor", "src/mf_faq/ingestion/extractor.py"),
        ("Cleaner", "src/mf_faq/ingestion/cleaner.py"),
        ("Chunker", "src/mf_faq/ingestion/chunker/service.py"),
        ("Embedder", "src/mf_faq/ingestion/embedder.py"),
        ("Indexer", "src/mf_faq/ingestion/indexer.py")
    ]
    
    success = True
    for name, script in steps:
        if os.path.exists(script):
            if not run_step(name, script):
                success = False
                break
        else:
            logger.warning(f"Script {script} not found, skipping...")
            
    status = "ok" if success else "failed"
    
    if success:
        logger.info("Refresh pipeline completed successfully.")
    else:
        logger.error("Refresh pipeline failed at one of the steps.")
        
    os.makedirs("data/index", exist_ok=True)
    with open("data/index/refresh_log.jsonl", "a", encoding="utf-8") as f:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "outcome": "completed" if success else "aborted"
        }
        f.write(json.dumps(log_entry) + "\n")
