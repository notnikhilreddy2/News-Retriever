import os
import json
import pandas as pd
import random
from autogen import AssistantAgent, UserProxyAgent
from tool_manager import ToolManager
from typing import Annotated

class NewsRetriever:
    def __init__(self):
        # Load environment variables
        self.SEARCH_KEYWORD = os.getenv("SEARCH_KEYWORD")
        self.ARTICLE_COUNT = int(os.getenv("ARTICLE_COUNT", 5))
        self.KEYWORD_COUNT = int(os.getenv("KEYWORD_COUNT", 3))
        self.NEWS_COUNTRY = os.getenv("NEWS_COUNTRY")
        self.AUTO_GENERATE_KEYWORDS = os.getenv("AUTO_GENERATE_KEYWORDS", "False").lower() == "true"

        self.GROQ_API_BASE = os.getenv("GROQ_API_BASE")
        self.GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")

        # Setup LLM config
        llm_config = {
            "cache_seed": 42,
            "config_list": [{
                "model": self.GROQ_MODEL_NAME,
                "api_key": self.GROQ_API_KEY,
                "base_url": self.GROQ_API_BASE
            }],
        }

        # Define agents
        self.news_collector_agent = AssistantAgent(
            name="news_collector_agent",
            llm_config=llm_config,
            system_message=(
                f"You are skilled at collecting recent news articles. "
                f"Generate a list of {self.KEYWORD_COUNT} subtopics closely related to the given topic. "
                f"Use the provided tool to collect news about these topics."
            ),
            max_consecutive_auto_reply=1
        )

        self.user_proxy_agent = UserProxyAgent(
            name="User",
            system_message="You are a helpful AI assistant. Return 'TERMINATE' when the task is done.",
            is_termination_msg=lambda msg: msg.get("content") and "TERMINATE" in msg["content"],
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        # Register the tool with both agents
        self.news_collector_agent.register_for_llm(
            name="get_news_articles_tool",
            description="Collect news articles about a list of topics on the internet."
        )(self.get_news_articles_tool)

        self.user_proxy_agent.register_for_execution(
            name="get_news_articles_tool"
        )(self.get_news_articles_tool)

    # Static tool used by the agents to collect news
    @staticmethod
    def get_news_articles_tool(
        keyword_list: Annotated[list, "List of keywords"],
        count: Annotated[int, "Number of articles to fetch"]
    ):
        tool_manager = ToolManager()
        news = tool_manager.get_news_articles(keyword_list, count)
        return news

    # Main method to get news
    def get_news(self, topic, count):
        try:
            if self.AUTO_GENERATE_KEYWORDS:
                chat_results = self.user_proxy_agent.initiate_chats([
                    {
                        "recipient": self.news_collector_agent,
                        "message": f"Collect {count} news articles about the topic '{topic}' from the internet.",
                        "clear_history": True,
                        "silent": False,
                        "summary_method": "last_msg",
                    },
                ])
                return chat_results[0].summary
            else:
                print("AUTO_GENERATE_KEYWORDS is disabled. No news fetched.")
                return None

        except Exception as e:
            print(f"❌ Global Error: {str(e)}")
            raise

# Test module directly:
if __name__ == "__main__":
    retriever = NewsRetriever()
    news = retriever.get_news("technology", 5)
    if news:
        print("📰 News Summary:")
        print(news)
    else:
        print("⚠️ No news retrieved.")
