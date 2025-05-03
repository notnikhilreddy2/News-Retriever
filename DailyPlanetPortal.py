import sys
import math
import os
from dotenv import load_dotenv
import json
import ast
import praw
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                             QMessageBox, QTextEdit, QLineEdit, QComboBox, QDialog, QFormLayout)
from PyQt5.QtGui import (QPixmap, QPalette, QBrush, QPainter, QColor, QFont, QImage)
from PyQt5.QtCore import (Qt, QTimer, QPropertyAnimation, QRectF, pyqtProperty)
from news_manager import NewsManager
import pandas as pd

# Load environment variables
load_dotenv()

class LoadingSpinner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self.setFixedSize(40, 40)
        self.setStyleSheet("background: transparent;")
        self.load_frames()

    def load_frames(self):
        self.points = []
        r = 15
        for i in range(12):
            angle = i * 30
            x = 20 + r * 0.5 * math.cos(math.radians(angle)) - 3
            y = 20 + r * 0.5 * math.sin(math.radians(angle)) - 3
            self.points.append((x, y))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor("#00FFFF")  # neon blue
        for i in range(12):
            color.setAlphaF((i + 1) / 12.0)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            index = (i + self._progress // 10) % 12
            x, y = self.points[index]
            painter.drawEllipse(QRectF(x, y, 6, 6))

    @pyqtProperty(int)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self.update()


class NewsBrowserDialog(QDialog):
    def __init__(self, news_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔥 Browse Hot News")
        self.resize(600, 500)

        self.news_manager = news_manager
        self.db_path = getattr(self.news_manager, "urls_file",
                               os.path.join(".cache", "news_database.csv"))

        vbox = QVBoxLayout(self)

        # top bar:   [ keyword box ] [Search] [History]
        hbox = QHBoxLayout()
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("keyword (e.g. AI, climate, F1 …)")

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.run_search)

        history_btn = QPushButton("History")
        history_btn.clicked.connect(self.show_history)

        hbox.addWidget(self.keyword_edit, 1)
        hbox.addWidget(search_btn)
        hbox.addWidget(history_btn)
        vbox.addLayout(hbox)

        # results pane
        self.results = QTextEdit(readOnly=True)
        self.results.setStyleSheet("font: 12px 'Courier New';")
        vbox.addWidget(self.results, 1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        vbox.addWidget(close_btn, alignment=Qt.AlignRight)

        # ← show history immediately
        self.show_history()

    # ── helpers ──────────────────────────────────────────────────────────────
    def _format_items(self, items):
        lines = []
        for item in items:
            lines.append(f"📰  {item['TITLE']}\n"
                         f"    • Topic  : {item['TOPIC']}\n"
                         f"    • Source : {item['SOURCE']}\n"
                         f"    • Preview: {item['CONTENT'][:160]}…\n")
        return "\n".join(lines) if lines else "No stories found."

    # load most‑recent cached rows
    def show_history(self, count: int = 10):
        """
        Display the latest count successfully‑scraped stories
        from the local CSV cache.  Newest first.
        """
        try:
            if not os.path.isfile(self.db_path):
                self.results.setPlainText("No history yet.")
                return

            df = pd.read_csv(self.db_path)

            # keep only rows marked as success and having real text
            need_cols = {"title", "content", "keyword", "source", "status"}
            if not need_cols.issubset(df.columns):
                self.results.setPlainText("History file format not recognised.")
                return

            df = (
                df[df["status"] == "success"]
                .dropna(subset=["title", "content"])
                .iloc[::-1]          # reverse so newest at top
            )

            items = [
                {
                    "TITLE":   row.title,
                    "TOPIC":   row.keyword or "—",
                    "CONTENT": row.content,
                    "SOURCE":  row.source,
                }
                for _, row in df.iterrows()
            ]

            self.results.setPlainText(self._format_items(items))
        except Exception as e:
            self.results.setPlainText(f"⚠️  Failed to read history:\n{e}")


    # unchanged search logic, but uses the same formatter
    def run_search(self):
        topic = self.keyword_edit.text().strip()
        if not topic:  # If search box is empty, do nothing
            return
            
        try:
            news = self.news_manager.get_news(topic, 5)
            if isinstance(news, str):          # handles possible stringified dict
                news = ast.literal_eval(news)
            
            if not news:
                self.results.setPlainText("No stories found.")
                return

            self.results.setPlainText(self._format_items(news.values()))
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


class DailyPlanetPortal(QMainWindow):
    def __init__(self, cache_dir=".cache"):
        super().__init__()
        self.reddit = None
        self.authenticated = False
        self.loading_value = 0
        self.cache_dir = cache_dir
        self.news_database = f"{self.cache_dir}/news_database.csv"
        self.news_manager = NewsManager()

        self.messages = [
            "Initializing portal systems...",
            "Loading security protocols...",
            "Establishing connection...",
            "Verifying credentials...",
            "Preparing dashboard..."
        ]
        self.current_message = 0

        self.background_image = QImage("Newsret.jpeg")

        self.setWindowTitle("Daily Planet Reddit Portal")
        self.resize(1200, 800)
        self.setAutoFillBackground(True)

        self.init_loading_screen()

    def set_background(self, widget):
        if self.background_image:
            palette = widget.palette()
            palette.setBrush(QPalette.Window, QBrush(QPixmap.fromImage(self.background_image).scaled(
                self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
            widget.setPalette(palette)
            widget.setAutoFillBackground(True)
        else:
            widget.setStyleSheet("background-color: #0d0d0d;")

    def init_loading_screen(self):
        self.loading_widget = QWidget()
        self.setCentralWidget(self.loading_widget)
        self.set_background(self.loading_widget)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        self.logo = QLabel("DAILY PLANET")
        self.logo.setStyleSheet("""
            QLabel {
                color: #00FFFF;
                font-size: 42px;
                font-weight: bold;
                font-family: 'Arial';
                letter-spacing: 2px;
                text-shadow: 2px 2px #000000;
            }
        """)
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo)

        self.spinner = LoadingSpinner()
        layout.addWidget(self.spinner, alignment=Qt.AlignCenter)

        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("""
            QLabel {
                color: #00FFFF;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        self.percent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.percent_label)

        self.status_label = QLabel(self.messages[0])
        self.status_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 16px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.loading_widget.setLayout(layout)
        self.start_loading_animation()

    def start_loading_animation(self):
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self.update_loading_screen)
        self.message_timer.start(800)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.increment_progress)
        self.animation_timer.start(50)

    def update_loading_screen(self):
        self.current_message = (self.current_message + 1) % len(self.messages)
        self.status_label.setText(self.messages[self.current_message])

    def increment_progress(self):
        if self.loading_value >= 100:
            self.animation_timer.stop()
            self.authenticate_reddit()
        else:
            self.loading_value += 2
            self.spinner.progress += 10
            self.percent_label.setText(f"{self.loading_value}%")

    def authenticate_reddit(self):
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent=os.getenv("REDDIT_USER_AGENT"),
                username=os.getenv("REDDIT_USERNAME"),
                password=os.getenv("REDDIT_PASSWORD")
            )

            if self.reddit.user.me():
                self.authenticated = True
                self.show_main_interface()
            else:
                raise Exception("Authentication failed")
        except Exception as e:
            QMessageBox.warning(self, "Authentication Error", f"Failed to connect to Reddit: {e}")
            self.show_main_interface()

    def show_main_interface(self):
        self.message_timer.stop()
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.set_background(main_widget)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        title = QLabel("🛰️ DAILY PLANET PORTAL")
        title.setStyleSheet("""
            QLabel {
                color: #00FFFF;
                font-size: 34px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        post_button = QPushButton("📤 Post News to Reddit")
        post_button.setFixedSize(250, 60)
        post_button.setStyleSheet(self.button_style())
        post_button.clicked.connect(self.show_post_dialog)

        view_button = QPushButton("📊 View My Activity")
        view_button.setFixedSize(250, 60)
        view_button.setStyleSheet(self.button_style())
        view_button.clicked.connect(self.view_my_activity)

        browse_button = QPushButton("🔥 Browse Hot News")
        browse_button.setFixedSize(250, 60)
        browse_button.setStyleSheet(self.button_style())
        browse_button.clicked.connect(self.browse_hot_news)

        buttons_layout.addWidget(post_button)
        buttons_layout.addWidget(view_button)
        buttons_layout.addWidget(browse_button)

        layout.addLayout(buttons_layout)

        footer = QLabel("Secure Access Enabled | Daily Planet v1.2 🚀")
        footer.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 12px;
            }
        """)
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        main_widget.setLayout(layout)

    def button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                              stop:0 #00c3ff, stop:1 #ffff1c);
                color: #000000;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                border: 2px solid #00FFFF;
            }
            QPushButton:hover {
                background-color: #00FFFF;
                color: #000;
            }
        """

    def show_post_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("📤 Post News to Reddit")
        dialog.resize(400, 300)
        layout = QFormLayout()

        self.sample_titles = pd.read_csv(self.news_database, usecols=['title'])['title'].dropna().tolist()
        self.sample_titles = list(set(self.sample_titles))
        # self.sample_titles = [
        #     "Breaking: AI Model Sets New Accuracy Record",
        #     "Python 3.13 Beta Released!",
        #     "F1 2025 Season Kick-off Details",
        #     "World Leaders Convene for Climate Talks"
        # ]

        self.title_dropdown = QComboBox()
        self.title_dropdown.addItems(self.sample_titles)
        layout.addRow("Select News Title:", self.title_dropdown)

        self.comment_box = QTextEdit()
        layout.addRow("Add a comment:", self.comment_box)

        post_button = QPushButton("Post to Reddit")
        post_button.clicked.connect(self.post_news_to_reddit)
        layout.addRow(post_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def post_news_to_reddit(self):
        selected_title = self.title_dropdown.currentText()
        comment_text = self.comment_box.toPlainText()

        try:
            subreddit = self.reddit.subreddit("r/DailyPlanetPortal")
            post = subreddit.submit(title=selected_title, selftext=comment_text)
            QMessageBox.information(self, "Success", f"Posted successfully: {post.title}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to post: {str(e)}")

    def view_my_activity(self):
        try:
            user = self.reddit.user.me()
            posts = list(user.submissions.new(limit=10))

            dialog = QDialog(self)
            dialog.setWindowTitle("📊 My Recent Reddit Activity")
            dialog.resize(600, 400)
            layout = QVBoxLayout()

            self.activity_list = QComboBox()
            self.activity_data = []
            for post in posts:
                self.activity_data.append(post)
                self.activity_list.addItem(post.title)

            summary_box = QTextEdit()
            summary_box.setReadOnly(True)

            def show_post_summary():
                index = self.activity_list.currentIndex()
                if index >= 0 and index < len(self.activity_data):
                    post = self.activity_data[index]
                    summary_box.setText(f"Title: {post.title}\n\nURL: {post.url}")

            self.activity_list.currentIndexChanged.connect(show_post_summary)

            layout.addWidget(self.activity_list)
            layout.addWidget(summary_box)
            dialog.setLayout(layout)
            show_post_summary()
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def browse_hot_news(self):
        try:
            dlg = NewsBrowserDialog(self.news_manager, self)
            dlg.exec_()

            # # hot_posts = self.reddit.subreddit("worldnews+technology+python+F1+machinelearning").hot(limit=5)
            # posts_info = "\n\n".join([f"{n['TITLE']}\n{n['SOURCE']}" for n in news.values()])
            # QMessageBox.information(self, "Trending News", posts_info or "No trending news found.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def resizeEvent(self, event):
        self.set_background(self.centralWidget())
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DailyPlanetPortal()
    window.show()
    sys.exit(app.exec_())
