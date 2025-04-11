# news_gui.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, 
                             QListWidget, QMessageBox, QComboBox, QSpinBox, QCheckBox)
from PyQt5.QtCore import Qt
from news_retriever import NewsRetriever
from news_poster import NewsPoster
import os
from dotenv import load_dotenv
import newspaper
newspaper.settings.CACHE_DIRECTORY = newspaper.settings.CF_CACHE_DIRECTORY

load_dotenv()

class NewsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("News Retrieval and Posting App")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize components
        self.news_retriever = NewsRetriever()
        self.news_poster = NewsPoster()
        self.current_news = None
        
        self.init_ui()
        
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Search section
        search_layout = QHBoxLayout()
        
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter search keyword...")
        search_layout.addWidget(self.keyword_input)
        
        self.article_count = QSpinBox()
        self.article_count.setRange(1, 20)
        self.article_count.setValue(5)
        self.article_count.setToolTip("Number of articles to retrieve")
        search_layout.addWidget(QLabel("Article Count:"))
        search_layout.addWidget(self.article_count)
        
        self.search_button = QPushButton("Search News")
        self.search_button.clicked.connect(self.search_news)
        search_layout.addWidget(self.search_button)
        
        main_layout.addLayout(search_layout)
        
        # News list section
        self.news_list = QListWidget()
        self.news_list.itemClicked.connect(self.show_news_details)
        main_layout.addWidget(self.news_list)
        
        # News details section
        self.news_details = QTextEdit()
        self.news_details.setReadOnly(True)
        main_layout.addWidget(self.news_details)
        
        # Post controls
        post_layout = QHBoxLayout()
        
        self.post_button = QPushButton("Post to Threads")
        self.post_button.clicked.connect(self.post_to_threads)
        self.post_button.setEnabled(False)
        post_layout.addWidget(self.post_button)
        
        main_layout.addLayout(post_layout)
        
        # Status bar
        self.status_bar = self.statusBar()
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def search_news(self):
        keyword = self.keyword_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Warning", "Please enter a search keyword.")
            return
        
        self.status_bar.showMessage("Searching for news...")
        QApplication.processEvents()  # Update UI
        
        try:
            # Temporarily override environment variables
            os.environ['SEARCH_KEYWORD'] = keyword
            os.environ['ARTICLE_COUNT'] = str(self.article_count.value())
            
            news = self.news_retriever.get_news()
            self.current_news = news
            
            self.news_list.clear()
            if news:
                for key, item in news.items():
                    self.news_list.addItem(f"{key}: {item['TITLE']}")
                self.status_bar.showMessage(f"Found {len(news)} news articles.", 5000)
            else:
                self.status_bar.showMessage("No news found.", 5000)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}", 5000)
            QMessageBox.critical(self, "Error", f"An error occurred while retrieving news:\n{str(e)}")
    
    def show_news_details(self, item):
        if not self.current_news:
            return
            
        # Extract the news key from the list item
        text = item.text()
        news_key = text.split(":")[0].strip()
        
        if news_key in self.current_news:
            news_item = self.current_news[news_key]
            details = f"""
            <h2>{news_item['TITLE']}</h2>
            <p><b>Topic:</b> {news_item['TOPIC']}</p>
            <p><b>Source:</b> <a href='{news_item['SOURCE']}'>{news_item['SOURCE']}</a></p>
            <hr>
            <p>{news_item['CONTENT']}</p>
            """
            self.news_details.setHtml(details)
            self.post_button.setEnabled(True)
    
    def post_to_threads(self):
        current_item = self.news_list.currentItem()
        if not current_item or not self.current_news:
            return
            
        text = current_item.text()
        news_key = text.split(":")[0].strip()
        
        if news_key in self.current_news:
            news_item = self.current_news[news_key]
            
            reply = QMessageBox.question(
                self, 
                "Confirm Post", 
                f"Are you sure you want to post this news to Threads?\n\nTitle: {news_item['TITLE']}", 
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    self.status_bar.showMessage("Posting to Threads...")
                    QApplication.processEvents()  # Update UI
                    
                    # Post the news
                    self.news_poster.post_to_threads(news_item)
                    
                    self.status_bar.showMessage("News posted to Threads successfully!", 5000)
                    QMessageBox.information(self, "Success", "News posted to Threads successfully!")
                except Exception as e:
                    self.status_bar.showMessage(f"Error posting to Threads: {str(e)}", 5000)
                    QMessageBox.critical(self, "Error", f"Failed to post to Threads:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = NewsApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
