import os
from dotenv import load_dotenv
from news_retriever import NewsRetriever
# from news_poster import NewsPoster

# Load environment variables from .env file
load_dotenv()

class NewsManager:
    def __init__(self):
        # Load version info from environment (optional/debug)
        self.VERSION = os.getenv('VERSION')
        self.RELEASE = os.getenv('RELEASE')
        # self.POST_TO_THREADS = os.getenv("POST_TO_THREADS", "False").lower() == 'true'

        print(f"VERSION: {self.VERSION}")
        print(f"RELEASE: {self.RELEASE}")

        # Initialize the retriever
        self.news_retriever = NewsRetriever()

    # Get top X news articles for a topic
    def get_news(self, topic, count):
        try:
            news = self.news_retriever.get_news(topic, count)
            if news:
                print("✅ News retrieved successfully.")
                return news
            else:
                print("⚠️ No news found.")
                return None
        except Exception as e:
            print(f"❌ Error retrieving news: {e}")
            return None

    # Optional posting function, commented out for now
    # def post_news(self, news):
    #     news_poster = NewsPoster()
    #     try:
    #         if self.POST_TO_THREADS:
    #             news_poster.post_to_threads(news)
    #             print("✅ News posted to Threads successfully.")
    #     except Exception as e:
    #         print(f"❌ Error posting news: {e}")

# Run manually to test
if __name__ == "__main__":
    manager = NewsManager()
    # Hardcoded test query
    test_topic = "technology"
    test_count = 5
    news = manager.get_news(test_topic, test_count)
    if news:
        for article in news:
            print(f"- {article['title']}")
    else:
        print("❌ No news found.")
