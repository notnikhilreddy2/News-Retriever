import os
from dotenv import load_dotenv
from news_retriever import NewsRetriever
# from news_poster import NewsPoster

load_dotenv()

class NewsManager:
    def __init__(self):
        VERSION = os.getenv('VERSION')
        RELEASE = os.getenv('RELEASE')
        # POST_TO_THREADS = True if os.getenv("POST_TO_THREADS") == 'True' else False
        print("VERSION:", VERSION)
        print("RELEASE:", RELEASE)
        self.news_retriever = NewsRetriever()

    def get_news(self, topic, count):
        try:
            news = self.news_retriever.get_news(topic, count)
            if news:
                print("News retrieved successfully.")
                return news
            else:
                print("No news found.")
                return None
        except Exception as e:
            print(f"An error occurred while retrieving news: {e}")
            return None

    # def post_news(self, news):
    #     news_poster = NewsPoster()
    #     try:
    #         if POST_TO_THREADS:
    #             news_poster.post_to_threads(news)
    #             print("News posted to Threads successfully.")
    #     except Exception as e:
    #         print(f"An error occurred while posting news: {e}")

if __name__ == "__main__":
    manager = NewsManager()
    news = manager.get_news()
    if news:
        print("News retrieved successfully.")
        # retriever.post_news(news)
    else:
        print("No news found.")
    # news = get_news()
#     if news:
#         post_news(news)
