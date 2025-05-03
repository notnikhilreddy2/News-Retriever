import os
import requests
import pandas as pd
from urllib.parse import urlparse
from newspaper import Article
from pyshorteners import Shortener
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class ToolManager:
    """
    A utility class to fetch and cache news articles using NewsAPI
    and parse them with newspaper3k. Supports keyword-based querying,
    basic deduplication, and local CSV caching.
    """

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
        self.urls_file = os.path.join(cache_dir, "news_database.csv")
        self.exclude_websites = exclude_websites or ["cnn.com"]
        self.shortener = Shortener(timeout=5)

        os.makedirs(cache_dir, exist_ok=True)

    @staticmethod
    def _domain(url: str) -> str:
        return urlparse(url).netloc.lower()

    def _is_excluded(self, url: str) -> bool:
        return any(self._domain(url).endswith(domain) for domain in self.exclude_websites)

    def _dedup(self, urls: List[str], keywords: List[str]) -> Tuple[List[str], List[str]]:
        """Deduplicate articles while preserving associated keywords."""
        merged: Dict[str, str] = {}
        for url, keyword in zip(urls, keywords):
            merged[url] = f"{merged.get(url, '')}, {keyword}".strip(', ')
        return list(merged.keys()), list(merged.values())

    def _fetch_urls(self, keyword: str) -> List[str]:
        """Fetch article URLs from NewsAPI for a given keyword."""
        params = {
            "q": keyword,
            "language": "en",
            "from": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "sortBy": "popularity",
            "pageSize": self.article_count,
            "apiKey": self.api_key,
        }

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        data = response.json()
        if data.get("status") != "ok":
            raise RuntimeError(data.get("message", "Unknown NewsAPI error"))

        return [
            article["url"]
            for article in data.get("articles", [])
            if article.get("url") and not self._is_excluded(article["url"])
        ]

    def _ensure_csv(self) -> pd.DataFrame:
        """Ensure the CSV cache file exists and return its DataFrame."""
        if not os.path.isfile(self.urls_file):
            columns = ["source", "short_url", "keyword", "title", "content", "status"]
            pd.DataFrame(columns=columns).to_csv(self.urls_file, index=False)
        return pd.read_csv(self.urls_file)

    def _scrape(self, urls: List[str], keywords: List[str]):
        """Scrape full article text and cache to CSV."""
        df = self._ensure_csv()
        urls, keywords = self._dedup(urls, keywords)
        articles = []

        for url, keyword in zip(urls, keywords):
            try:
                article = Article(url)
                article.download()
                article.parse()

                if article.text and len(article.text.split()) > 50:
                    short_url = self.shortener.tinyurl.short(url)
                    article.keyword = keyword
                    article.short_url = short_url
                    df.loc[len(df)] = [url, short_url, keyword, article.title, article.text, "success"]
                    articles.append(article)
                else:
                    df.loc[len(df)] = [url, None, keyword, None, None, "empty"]
            except Exception:
                df.loc[len(df)] = [url, None, keyword, None, None, "error"]

        df.to_csv(self.urls_file, index=False)
        return articles

    def get_news_articles(self, keywords: List[str], count: Optional[int] = None):
        """Main method to get structured news data from keywords."""
        count = count or self.article_count
        all_urls, all_keywords = [], []

        for keyword in keywords:
            try:
                urls = self._fetch_urls(keyword)[:count]
                all_urls.extend(urls)
                all_keywords.extend([keyword] * len(urls))
            except Exception as e:
                print(f"[ToolManager] Fetch failed for '{keyword}': {e}")

        # If nothing is fetched, return a static fallback sample
        if not all_urls:
            return {
                "NEWS 1": {
                    "TOPIC": "AI",
                    "TITLE": "Decagon Named to 2025 Forbes AI 50 List of Top Artificial Intelligence Companies",
                    "CONTENT": "SAN FRANCISCO--(BUSINESS WIRE)--Decagon ...",
                    "SOURCE": "https://tinyurl.com/2dm2xvn4",
                }
            }

        articles = self._scrape(all_urls, all_keywords)
        return {
            f"NEWS {i}": {
                "TOPIC": article.keyword,
                "TITLE": article.title,
                "CONTENT": article.text.replace("\n\n", "\n")[:1000],  # limit to 1000 chars
                "SOURCE": article.short_url,
            }
            for i, article in enumerate(articles, 1)
        }


# Example usage
if __name__ == "__main__":
    manager = ToolManager()
    articles = manager.get_news_articles(["AI", "climate change"], count=3)
    for key, article in articles.items():
        print(f"{key}: {article['TITLE']} ({article['SOURCE']})")

