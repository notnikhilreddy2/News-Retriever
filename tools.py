from typing import Annotated

def get_news_articles_tool(keyword_list: Annotated[list, "The list of keywords"], count: Annotated[int, "The number of news articles to collect from the internet"]) -> str:
    pass