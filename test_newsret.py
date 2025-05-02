import pytest
import os
import praw
from unittest.mock import patch
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

@pytest.fixture
def reddit_client():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
    )

def test_env_variables_present():
    assert os.getenv("REDDIT_CLIENT_ID") is not None
    assert os.getenv("REDDIT_CLIENT_SECRET") is not None
    assert os.getenv("REDDIT_USERNAME") is not None
    assert os.getenv("REDDIT_PASSWORD") is not None
    assert os.getenv("REDDIT_USER_AGENT") is not None

def test_reddit_authentication(reddit_client):
    assert reddit_client.user.me() is not None

@patch("praw.models.Subreddit.submit")
def test_mocked_post_submission(mock_submit, reddit_client):
    mock_submit.return_value.url = "https://reddit.com/fake-post"
    subreddit = reddit_client.subreddit("test")
    submission = subreddit.submit(title="Fake", selftext="Mock test")
    assert submission.url == "https://reddit.com/fake-post"

# Simulate your news fetching function from news_retriever.py
def fetch_news():
    # Dummy simulated response; replace with real fetch in integration
    return [{"title": "Breaking News", "url": "http://example.com"}]

def test_news_fetching_returns_articles():
    news = fetch_news()
    assert isinstance(news, list)
    assert "title" in news[0] and "url" in news[0]

def test_empty_news_submission_is_handled(reddit_client):
    # Try submitting empty title/body to test failure handling
    with pytest.raises(Exception):
        reddit_client.subreddit("test").submit(title="", selftext="")
