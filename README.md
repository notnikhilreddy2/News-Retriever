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
VERSION: 1.0
RELEASE: DEV
News retrieved successfully.
NEWS 1:
- TOPIC: AI
- TITLE: Decagon Named to 2025 Forbes AI 50 List
- CONTENT: Decagon recognized as a top AI firm in 2025 by Forbes...
- SOURCE: https://tinyurl.com/example


  GROQ_API_BASE = https://api.groq.com/openai/v1
    GROQ_MODEL_NAME = llama3-70b-8192
    # GROQ_MODEL_NAME = mixtral-8x7b-32768
    GROQ_API_KEY = #<YOUR GROQ API HERE>
