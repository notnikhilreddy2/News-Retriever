import os
import json
import pandas as pd
import random
from autogen import AssistantAgent, UserProxyAgent
from tool_manager import ToolManager
from typing import Annotated

class NewsRetriever:
    def __init__(self):
        self.SEARCH_KEYWORD = os.getenv("SEARCH_KEYWORD")
        self.ARTICLE_COUNT = os.getenv("ARTICLE_COUNT")
        self.KEYWORD_COUNT = os.getenv("KEYWORD_COUNT")
        self.NEWS_COUNTRY = os.getenv("NEWS_COUNTRY")
        self.AUTO_GENERATE_KEYWORDS = True if os.getenv("AUTO_GENERATE_KEYWORDS") == 'True' else False

        self.GROQ_API_BASE = os.getenv("GROQ_API_BASE")
        self.GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")

        llm_config = {
            "cache_seed": 42,
            "config_list": [{
                "model": self.GROQ_MODEL_NAME,
                "api_key": self.GROQ_API_KEY,
                "base_url": self.GROQ_API_BASE
            }],
        }

        self.news_collector_agent = AssistantAgent(
            "news_collector_agent",
            llm_config=llm_config,
            system_message=f"""You are good at collecting recent news articles about a given keyword on the internet. 
            You should generate a list of {self.KEYWORD_COUNT} topics closely related to the given keyword. 
            Use the provided tool to collect news about the generated list of topics.""",
            max_consecutive_auto_reply=1
        )

        self.user_proxy_agent = UserProxyAgent(
            name="User",
            system_message="You are a helpful AI assistant. Return 'TERMINATE' when the task is done.",
            is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        self.news_collector_agent.register_for_llm(name="get_news_articles_tool", description="Collect news articles about a list of topics on the internet.")(self.get_news_articles_tool)
        self.user_proxy_agent.register_for_execution(name="get_news_articles_tool")(self.get_news_articles_tool)

    @staticmethod
    def get_news_articles_tool(keyword_list: Annotated[list, "List of keywords"], count: Annotated[int, "Number of articles to fetch"]):
            tool_manager = ToolManager()
            news = tool_manager.get_news_articles(keyword_list, count)
            # print('NEWS: ', news)
            return news

    def get_news(self):
        try:
            if self.AUTO_GENERATE_KEYWORDS==True:
                chat_results = self.user_proxy_agent.initiate_chats([
                    {
                        "recipient": self.news_collector_agent,
                        "message": f"Collect {self.KEYWORD_COUNT} news articles about the topic '{self.SEARCH_KEYWORD}' from the internet.",
                        "clear_history": True,
                        "silent": False,
                        "summary_method": "last_msg",
                    },
                ])
                # print('CHAT RESULTS: ', chat_results[0].summary)
                return chat_results[0].summary
            else:
                pass
                # return None
                
        except Exception as e:
            print(f"Global Error: {str(e)}")
            raise e
