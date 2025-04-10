import os
from dotenv import load_dotenv
from news_retriever import NewsRetriever
from news_poster import NewsPoster

load_dotenv()

VERSION = os.getenv('VERSION')
RELEASE = os.getenv('RELEASE')
POST_TO_THREADS = True if os.getenv("POST_TO_THREADS") == 'True' else False

def get_news():
    news_retriever = NewsRetriever()

    try:
        news = news_retriever.get_news()
        if news:
            print("News retrieved successfully.")
            return news
        else:
            print("No news found.")
            return None
    except Exception as e:
        print(f"An error occurred while retrieving news: {e}")

def post_news(news):
    news_poster = NewsPoster()
    try:
        if POST_TO_THREADS:
            news_poster.post_to_threads(news)
            print("News posted to Threads successfully.")
    except Exception as e:
        print(f"An error occurred while posting news: {e}")

def print_run_info():
    print("VERSION:", VERSION)
    print("RELEASE:", RELEASE)
    print("POST_TO_THREADS:", POST_TO_THREADS)

if __name__ == "__main__":
    print_run_info()
    news = get_news()
    if news:
        post_news(news)
