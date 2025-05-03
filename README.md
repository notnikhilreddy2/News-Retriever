# News-Retriever

Version = 1.1.2
# 📰 News-Retriever (Reddit Edition)

News-Retriever is a Python application that fetches the latest news articles from the internet using the [NewsAPI](https://newsapi.org/), optionally enriches them with AI-generated keywords using a Groq-hosted language model, and can post curated summaries to Reddit.

This project is ideal for building a personal news bot, automation tool, or news aggregation service.

---

## 🚀 Features

- 🔍 **Search News**: Fetches news based on a keyword or AI-generated related topics.
- 🧠 **LLM Keyword Generation**: Uses Groq-hosted LLMs like LLaMA 3 or Mixtral to generate relevant subtopics.
- 📰 **Content Extraction**: Parses and summarizes full article text.
- 📬 **Reddit Posting**: Posts formatted articles to a configured subreddit.
- 📦 **CSV Caching**: Stores and deduplicates articles locally to avoid repeat posts.

---

## 📸 Preview

```
.env file data

VERSION = 1.0
RELEASE = 'DEV' #just get the news and print to terminal
# RELEASE = 'TEST' #generates post but doesn't post it
# RELEASE = 'PROD' #generated post and posts to social media

GROQ_API_BASE = https://api.groq.com/openai/v1
GROQ_MODEL_NAME = llama3-70b-8192
# GROQ_MODEL_NAME = mixtral-8x7b-32768
GROQ_API_KEY = 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

SEARCH_KEYWORD = 'AI'
ARTICLE_COUNT = 5
AUTO_GENERATE_KEYWORDS = True
KEYWORD_COUNT = 1
NEWS_COUNTRY = 'United States'

REDDIT_CLIENT_ID=PHjLXAw_bNhMcBzMfA9hdg
REDDIT_CLIENT_SECRET=HQa4pSXUQOVoPvucHkUDEJQJ3r0wNA
REDDIT_USER_AGENT=script:news-retriever:v1.0 (by u/Top_Beach_9052)
REDDIT_USERNAME=Top_Beach_9052
REDDIT_PASSWORD=Project@123
