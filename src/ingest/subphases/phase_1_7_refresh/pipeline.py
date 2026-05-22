import os
import subprocess
import logging
import json
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, index_dir: str = "data/index"):
        self.index_dir = index_dir

    def refresh(self, force=False, dry_run=False, skip_fetch=False) -> bool:
        logger.info("Starting full data refresh pipeline...")
        
        steps = [
            ("Fetcher", ["python3", "-m", "src.ingest", "1.1"]),
            ("Extractor", ["python3", "-m", "src.ingest", "1.2"]),
            ("Cleaner", ["python3", "-m", "src.ingest", "1.3"]),
            ("Chunker", ["python3", "-m", "src.ingest", "1.4"]),
            ("Embedder", ["python3", "-m", "src.ingest", "1.5"]),
            ("Indexer", ["python3", "-m", "src.ingest", "1.6"])
        ]
        
        if skip_fetch:
            steps = steps[1:]
            
        success = True
        for name, cmd in steps:
            logger.info(f"--- Running {name} ---")
            if dry_run:
                logger.info(f"[Dry Run] Would run: {' '.join(cmd)}")
                continue
                
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"{name} failed:\n{result.stderr}")
                success = False
                break
            logger.info(f"{name} completed successfully.")
            
        status = "ok" if success else "failed"
        
        if not dry_run:
            os.makedirs(self.index_dir, exist_ok=True)
            with open(os.path.join(self.index_dir, "refresh_log.jsonl"), "a", encoding="utf-8") as f:
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": status,
                    "outcome": "completed" if success else "aborted"
                }
                f.write(json.dumps(log_entry) + "\n")
                
        return success

if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.refresh()
