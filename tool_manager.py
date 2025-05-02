import os
import requests
import pandas as pd
from urllib.parse import urlparse
from newspaper import Article
from pyshorteners import Shortener
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class ToolManager:
    """Fetch and cache news articles using NewsAPI."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(
        self,
        *,
        newsapi_key: str = os.getenv("NEWSAPI_KEY", "bdb6ca050c0742b3a0e2dba3f593a338"),
        article_count: int = 5,
        cache_dir: str = ".cache",
        exclude_websites: Optional[List[str]] = None,
    ) -> None:
        self.api_key = newsapi_key
        self.article_count = article_count
        self.cache_dir = cache_dir
        self.urls_file = f"{cache_dir}/news_database.csv"
        self.exclude_websites = exclude_websites or ["cnn.com"]
        self.shortener = Shortener(timeout=5)

        os.makedirs(cache_dir, exist_ok=True)

    @staticmethod
    def _domain(url: str) -> str:
        return urlparse(url).netloc.lower()

    def _is_excluded(self, url: str) -> bool:
        return any(self._domain(url).endswith(dom) for dom in self.exclude_websites)

    def _dedup(self, urls: List[str], kws: List[str]) -> Tuple[List[str], List[str]]:
        merged: Dict[str, str] = {}
        for u, k in zip(urls, kws):
            merged[u] = f"{merged.get(u, '')}, {k}".strip(', ')
        return list(merged.keys()), list(merged.values())

    def _fetch_urls(self, keyword: str) -> List[str]:
        params = {
            "q": keyword,
            "language": "en",
            "from": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "sortBy": "popularity",
            "pageSize": self.article_count,
            "apiKey": self.api_key,
        }
        data = requests.get(self.BASE_URL, params=params, timeout=10).json()
        if data.get("status") != "ok":
            raise RuntimeError(data.get("message", "Unknown NewsAPI error"))
        return [a["url"] for a in data.get("articles", []) if a.get("url") and not self._is_excluded(a["url"])]

    def _ensure_csv(self) -> pd.DataFrame:
        if not os.path.isfile(self.urls_file):
            cols = ["source", "short_url", "keyword", "title", "content", "status"]
            pd.DataFrame(columns=cols).to_csv(self.urls_file, index=False)
        return pd.read_csv(self.urls_file)

    def _scrape(self, urls: List[str], kws: List[str]):
        df = self._ensure_csv()
        urls, kws = self._dedup(urls, kws)
        arts = []
        for url, kw in zip(urls, kws):
            try:
                art = Article(url)
                art.download(); art.parse()
                if art.text and len(art.text.split()) > 50:
                    short = self.shortener.tinyurl.short(url)
                    art.keyword, art.short_url = kw, short
                    df.loc[len(df)] = [url, short, kw, art.title, art.text, "success"]
                    arts.append(art)
                else:
                    df.loc[len(df)] = [url, None, kw, None, None, "empty"]
            except Exception:
                df.loc[len(df)] = [url, None, kw, None, None, "error"]
        df.to_csv(self.urls_file, index=False)
        return arts

    def get_news_articles(self, keywords: List[str], count: Optional[int] = None):
        count = count or self.article_count
        all_urls, all_kws = [], []
        for kw in keywords:
            try:
                urls = self._fetch_urls(kw)[:count]
                all_urls.extend(urls)
                all_kws.extend([kw] * len(urls))
            except Exception as e:
                print(f"[ToolManager] fetch failed for '{kw}': {e}")

        if not all_urls:
            return {
                "NEWS 1": {
                    "TOPIC": "AI",
                    "TITLE": "Decagon Named to 2025 Forbes AI 50 List of Top Artificial Intelligence Companies",
                    "CONTENT": "SAN FRANCISCO--(BUSINESS WIRE)--Decagon ...",
                    "SOURCE": "https://tinyurl.com/2dm2xvn4",
                }
            }

        articles = self._scrape(all_urls, all_kws)
        return {
            f"NEWS {i}": {
                "TOPIC": a.keyword,
                "TITLE": a.title,
                "CONTENT": a.text.replace("\n\n", "\n")[:1000],
                "SOURCE": a.short_url,
            }
            for i, a in enumerate(articles, 1)
        }
