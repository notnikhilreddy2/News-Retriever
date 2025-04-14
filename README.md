# News-Retriever

Add these variables in your .env file:

    VERSION = 1.0
    RELEASE = 'DEV' #just get the news and print to terminal
    # RELEASE = 'TEST' #generates post but doesn't post it
    # RELEASE = 'PROD' #generated post and posts to social media

    GROQ_API_BASE = https://api.groq.com/openai/v1
    GROQ_MODEL_NAME = llama3-70b-8192
    # GROQ_MODEL_NAME = mixtral-8x7b-32768
    GROQ_API_KEY = #<YOUR GROQ API HERE>

    SEARCH_KEYWORD = 'AI'
    ARTICLE_COUNT = 5
    AUTO_GENERATE_KEYWORDS = True
    KEYWORD_COUNT = 1
    NEWS_COUNTRY = 'United States'

    POST_TO_THREADS = False
    THREADS_USERNAME = ''
    THREADS_PASSWORD = ''