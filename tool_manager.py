import os
import json
import requests
import pandas as pd
from urllib.parse import quote, urlparse
from bs4 import BeautifulSoup
from newspaper import Article
from pyshorteners import Shortener
from typing import Annotated
from gnews import GNews
import random
from datetime import datetime, timedelta


class ToolManager:
    def __init__(self, article_count=5, cache_dir=".cache", exclude_websites=None):
        self.article_count = article_count
        self.cache_dir = cache_dir
        self.urls_file = f"{self.cache_dir}/news_database.csv"
        self.google_news = GNews()
        self.google_news.period = '24h'
        self.google_news.max_results = self.article_count
        self.google_news.country = 'United States'
        self.google_news.language = 'english'
        self.google_news.exclude_websites = exclude_websites if exclude_websites else ['cnn.com']
        self.shortener = Shortener(timeout=5)
        self.NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", 'bdb6ca050c0742b3a0e2dba3f593a338')

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    # def get_decoding_params(self, gn_art_id):
    #     headers = {'User-Agent': 'Mozilla/5.0'}
    #     response = requests.get(f"https://news.google.com/articles/{gn_art_id}", headers=headers)
    #     response.raise_for_status()
    #     soup = BeautifulSoup(response.text, "lxml")
    #     div = soup.select_one("c-wiz > div")
    #     return {
    #         "signature": div.get("data-n-a-sg"),
    #         "timestamp": div.get("data-n-a-ts"),
    #         "gn_art_id": gn_art_id,
    #     }

    # def decode_urls(self, articles):
    #     articles_reqs = [
    #         [
    #             "Fbv4je",
    #             f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{art["gn_art_id"]}",{art["timestamp"]},"{art["signature"]}"]',
    #         ]
    #         for art in articles
    #     ]
    #     payload = f"f.req={quote(json.dumps([articles_reqs]))}"
    #     headers = {"content-type": "application/x-www-form-urlencoded;charset=UTF-8"}
    #     response = requests.post(
    #         url="https://news.google.com/_/DotsSplashUi/data/batchexecute",
    #         headers=headers,
    #         data=payload,
    #     )
    #     response.raise_for_status()
    #     return [json.loads(res[2])[1] for res in json.loads(response.text.split("\n\n")[1])[:-2]]
    # from googlenewsdecoder import gnewsdecoder

     #def decode_urls(self, articles):
      #   print('Articles:', articles)
       #  interval_time = 1  # interval is optional, default is None

#         source_url = "https://news.google.com/read/CBMi2AFBVV95cUxPd1ZCc1loODVVNHpnbFFTVHFkTG94eWh1NWhTeE9yT1RyNTRXMVV2S1VIUFM3ZlVkVjl6UHh3RkJ0bXdaTVRlcHBjMWFWTkhvZWVuM3pBMEtEdlllRDBveGdIUm9GUnJ4ajd1YWR5cWs3VFA5V2dsZnY1RDZhVDdORHRSSE9EalF2TndWdlh4bkJOWU5UMTdIV2RCc285Q2p3MFA4WnpodUNqN1RNREMwa3d5T2ZHS0JlX0MySGZLc01kWDNtUEkzemtkbWhTZXdQTmdfU1JJaXY?hl=en-US&gl=US&ceid=US%3Aen"

 #        try:
  #           decoded_url = gnewsdecoder(source_url, interval=interval_time)

   #          if decoded_url.get("status"):
    #             print("Decoded URL:", decoded_url["decoded_url"])
     #        else:
      #           print("Error:", decoded_url["message"])
       #  except Exception as e:
      #       print(f"Error occurred: {e}")

    def deduplicate_news_list(self, urls, keywords):
        urls_dict = {}
        for i in range(len(urls)):
            if urls[i] not in urls_dict:
                urls_dict[urls[i]] = keywords[i]
            else:
                urls_dict[urls[i]] += ', ' + keywords[i]
        return list(urls_dict.keys()), list(urls_dict.values())

    def create_news_dict(self, article_list):
        news_dict = {}
        for i, article in enumerate(article_list):
            news_key = f"NEWS {i+1}"
            news_dict[news_key] = {
                "TOPIC": article.keyword,
                "TITLE": article.title,
                "CONTENT": article.text.replace('\n\n', '\n')[:1000],
                "SOURCE": article.short_url
            }
        return news_dict

    def read_news_articles(self, urls, keywords):
        if not os.path.isfile(self.urls_file):
            df_urls = pd.DataFrame(columns=['source', 'keyword', 'title', 'content', 'status'])
            df_urls.to_csv(self.urls_file)
        else:
            df_urls = pd.read_csv(self.urls_file, index_col='Unnamed: 0')

        # urls = [url for url in urls if url not in df_urls['urls'].values]
        urls, keywords = self.deduplicate_news_list(urls, keywords)

        if len(urls) == 0:
            return []

        article_list = []
        for i in range(len(urls)):
            try:
                article = Article(urls[i])
                article.download()
                article.parse()
                if article.text and len(article.text.strip().split('\n')) > 1:
                    article.keyword = keywords[i]
                    df_urls = pd.concat([pd.DataFrame([[urls[i], article.keyword, article.title, article.text.replace('\n\n', '\n'), 'success']], columns=df_urls.columns), df_urls], ignore_index=True)
                    article_list.append(article)
                else:
                    df_urls = pd.concat([pd.DataFrame([[urls[i], None, None, None, 'empty content']], columns=df_urls.columns), df_urls], ignore_index=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                df_urls = pd.concat([pd.DataFrame([[urls[i], None, None, None, 'scraping error']], columns=df_urls.columns), df_urls], ignore_index=True)
        df_urls.to_csv(self.urls_file)
        return article_list

    def get_news_articles(self, keyword_list, count):
        self.google_news.max_results = count
        urls, keywords = [], []

        for keyword in keyword_list:
            try:
                # sources = self.google_news.get_news(keyword)
                url = ('https://newsapi.org/v2/everything?'
                    f'q={keyword}&'
                    f'from={(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}&'
                    'sortBy=popularity&'
                    f'apiKey={self.NEWSAPI_KEY}')
                # print('URL: ', url)
                response = requests.get(url).json()
                sources = response['articles']
                sources = [source['url'] for source in sources if source['url']]
                sources = random.sample(sources, min(count, len(sources)))
                # print('SOURCES: ', sources)
                # print(response.json())
            except Exception as e:
                print(f"Error fetching news for {keyword}: {e}")
                continue
            # print('SOURCES: ', sources)
            for source in sources:
                try:
                    # art_id = urlparse(source['url']).path.split("/")[-1]
                    # print('Art ID: ', art_id)
                    # params = self.get_decoding_params(art_id)
                    # print('PARAMS: ', params)
                    # decoded = self.decode_urls([params])
                    # print('DECODED: ', decoded)
                    if source:
                        urls.append(source)
                        keywords.append(keyword)
                except Exception as e:
                    #print stack trace
                    import traceback
                    traceback.print_exc()
                    print(f"Error decoding URL for {keyword}: {e}")
                    continue

        if len(urls) == 0:
            # default news
            return {"NEWS 1": {"TOPIC": "AI", "TITLE": "Decagon Named to 2025 Forbes AI 50 List of Top Artificial Intelligence Companies", "CONTENT": "SAN FRANCISCO--(BUSINESS WIRE)--Decagon, the leading innovator in conversational AI agents for customer experience, today announced it has been named to the 2025 Forbes AI 50 — Forbes\" annual list of the most promising, privately-held companies using artificial intelligence to shape the future of business and society. This marks Decagon’s first appearance on the prestigious list, which spotlights standout AI companies across North America.\n'Being able to effectively handle tasks like refunds or account changes is table stakes. What sets the best products apart is their ability to meet customers where they are, completing complex workflows and delivering deeply personalized experiences.'\nShare\nWith growing hype around AI agents, few companies have delivered meaningful, enterprise-ready results. Decagon sets itself apart by building AI agents that drive immediate and measurable impact. Its technology is used by well-known companies — including Hertz, Eventbrite, Duolingo, ClassPass, Noti", "SOURCE": "https://tinyurl.com/2dm2xvn4"}}
            # return None

        # print('URLs: ', urls[0])
        article_list = self.read_news_articles(urls, keywords)
        # print('Article List: ', len(article_list))

        for article in article_list:
            try:
                article.short_url = self.shortener.tinyurl.short(article.url)
            except Exception as e:
                print(f"Error shortening URL: {e}")
                article.short_url = article.url
        
        print('Article List: ', article_list)

        result = self.create_news_dict(article_list)
        # print('RESULT: ', result)
        return result
