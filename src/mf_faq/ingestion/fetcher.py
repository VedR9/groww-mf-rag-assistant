import json
import logging
import time
import urllib.robotparser
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

import httpx
import yaml
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Groww MF FAQ Assistant (Research Project)"

@dataclass
class FetchResult:
    url: str
    scheme_id: str
    status: str  # "ok", "skipped", "error"
    http_status: int
    fetcher_kind: str
    content_hash_raw: Optional[str] = None
    fetched_at: Optional[str] = None


class Fetcher:
    def __init__(self, sources_path: str = "config/sources.yaml", raw_dir: str = "data/raw"):
        self.sources_path = Path(sources_path)
        self.raw_dir = Path(raw_dir)
        self.urls = self._load_urls()
        self.required_keywords = ["Expense Ratio", "Exit Load", "Min SIP"]
        self.min_length = 5000  # Minimum text length to consider valid without JS

    def _load_urls(self) -> List[str]:
        if not self.sources_path.exists():
            raise FileNotFoundError(f"Sources config not found: {self.sources_path}")
        with open(self.sources_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("urls", [])

    def _check_robots(self) -> bool:
        """Check if we are allowed to scrape groww.in"""
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url("https://groww.in/robots.txt")
        try:
            rp.read()
            # check the first url or a generic scheme url
            if self.urls:
                return rp.can_fetch(USER_AGENT, self.urls[0])
            return True
        except Exception as e:
            logger.warning(f"Could not read robots.txt, assuming allowed: {e}")
            return True

    def _extract_scheme_id(self, url: str) -> str:
        return url.rstrip("/").split("/")[-1]

    def _get_existing_meta(self, scheme_dir: Path) -> dict:
        meta_file = scheme_dir / "meta.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def fetch_all(self) -> List[FetchResult]:
        if not self._check_robots():
            logger.error("Scraping disallowed by robots.txt. Aborting run.")
            return []

        results = []
        for url in self.urls:
            try:
                result = self._fetch_single(url)
                results.append(result)
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                results.append(FetchResult(
                    url=url,
                    scheme_id=self._extract_scheme_id(url),
                    status="error",
                    http_status=0,
                    fetcher_kind="none"
                ))
        return results

    def _fetch_single(self, url: str) -> FetchResult:
        scheme_id = self._extract_scheme_id(url)
        scheme_dir = self.raw_dir / scheme_id
        scheme_dir.mkdir(parents=True, exist_ok=True)
        
        meta = self._get_existing_meta(scheme_dir)
        etag = meta.get("etag")
        
        headers = {"User-Agent": USER_AGENT}
        if etag:
            headers["If-None-Match"] = etag

        with httpx.Client(follow_redirects=False) as client:
            resp = client.get(url, headers=headers)

        if resp.status_code == 304:
            logger.info(f"304 Not Modified for {url}. Skipping.")
            return FetchResult(
                url=url,
                scheme_id=scheme_id,
                status="skipped",
                http_status=304,
                fetcher_kind=meta.get("fetcher_kind", "unknown"),
                content_hash_raw=meta.get("content_hash_raw"),
                fetched_at=meta.get("fetched_at")
            )

        if resp.status_code in (301, 302, 307, 308):
            logger.error(f"Governance Alert: {url} redirected to {resp.headers.get('Location')}. Not following.")
            raise ValueError(f"Redirects not allowed: {resp.status_code}")

        if resp.status_code >= 400:
            logger.error(f"HTTP {resp.status_code} for {url}. Stopping.")
            raise ValueError(f"Client/Server Error: {resp.status_code}")

        html_content = resp.text
        fetcher_kind = "httpx"
        new_etag = resp.headers.get("etag")

        # Validation
        soup = BeautifulSoup(html_content, "html.parser")
        text_content = soup.get_text(separator=" ", strip=True)
        
        missing_keywords = [kw for kw in self.required_keywords if kw.lower() not in text_content.lower()]
        if len(text_content) < self.min_length or missing_keywords:
            logger.info(f"Fallback to playwright for {url} (length={len(text_content)}, missing={missing_keywords})")
            html_content = self._fetch_with_playwright(url)
            fetcher_kind = "playwright"
            new_etag = None # Playwright doesn't easily expose this in simple sync get

        # Hashing and saving
        content_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        html_file = scheme_dir / f"{timestamp}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        new_meta = {
            "url": url,
            "fetched_at": timestamp,
            "http_status": resp.status_code,
            "etag": new_etag,
            "content_hash_raw": content_hash,
            "fetcher_kind": fetcher_kind
        }
        with open(scheme_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(new_meta, f, indent=2)

        return FetchResult(
            url=url,
            scheme_id=scheme_id,
            status="ok",
            http_status=resp.status_code,
            fetcher_kind=fetcher_kind,
            content_hash_raw=content_hash,
            fetched_at=timestamp
        )

    def _fetch_with_playwright(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            response = page.goto(url, wait_until="networkidle")
            
            if response and response.status >= 400:
                browser.close()
                raise ValueError(f"Playwright HTTP Error: {response.status}")
                
            content = page.content()
            browser.close()
            return content

if __name__ == "__main__":
    fetcher = Fetcher()
    results = fetcher.fetch_all()
    health = "ok" if all(r.status in ("ok", "skipped") for r in results) else "degraded"
    print(f"Fetcher Health: {health}")
    for r in results:
        print(f"{r.scheme_id}: {r.status} ({r.fetcher_kind})")
