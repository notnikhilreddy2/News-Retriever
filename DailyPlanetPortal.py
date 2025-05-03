import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFormLayout, QComboBox
)
from PyQt5.QtGui import QFontDatabase, QPalette, QBrush, QPixmap
from PyQt5.QtCore import Qt

import praw
from news_manager import NewsManager
from news_browser_dialog import NewsBrowserDialog
from dotenv import load_dotenv

# Load secrets from .env file
load_dotenv()

class DailyPlanetPortal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daily Planet Portal")
        self.setGeometry(200, 200, 900, 700)

        self.reddit = None
        self.authenticated = False

        # Load fonts and background
        self.load_fonts()
        self.init_ui()

    # Try to load custom fonts
    def load_fonts(self):
        try:
            font_id = QFontDatabase.addApplicationFont("fonts/ShareTechMono-Regular.ttf")
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                self.setFont(families[0])
        except Exception as e:
            print(f"Font load error: {e}")

    # Set background image
    def set_background(self, widget):
        palette = QPalette()
        pixmap = QPixmap("assets/daily_planet_bg.jpg")
        palette.setBrush(QPalette.Window, QBrush(pixmap.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)

    # Build login screen first
    def init_ui(self):
        self.login_widget = QWidget()
        self.setCentralWidget(self.login_widget)
        self.set_background(self.login_widget)

        layout = QVBoxLayout(self.login_widget)
        layout.setAlignment(Qt.AlignCenter)

        # Login inputs
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Reddit Client ID")
        self.client_id_input.setText(os.getenv("REDDIT_CLIENT_ID", ""))

        self.client_secret_input = QLineEdit()
        self.client_secret_input.setPlaceholderText("Reddit Client Secret")
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        self.client_secret_input.setText(os.getenv("REDDIT_CLIENT_SECRET", ""))

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Reddit Username")
        self.username_input.setText(os.getenv("REDDIT_USERNAME", ""))

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Reddit Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setText(os.getenv("REDDIT_PASSWORD", ""))

        self.login_button = QPushButton("Log in to Reddit")
        self.login_button.clicked.connect(self.authenticate)

        self.login_status = QLabel("")
        self.login_status.setStyleSheet("color: white;")

        layout.addWidget(self.client_id_input)
        layout.addWidget(self.client_secret_input)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.login_status)

    # Reddit login
    def authenticate(self):
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id_input.text().strip(),
                client_secret=self.client_secret_input.text().strip(),
                username=self.username_input.text().strip(),
                password=self.password_input.text().strip(),
                user_agent="DailyPlanetPortal by /u/your_username"
            )
            # Try test call
            self.reddit.user.me()
            self.authenticated = True
            self.login_status.setText("✅ Login successful!")
            self.init_news_manager()
            self.show_main_interface()
        except Exception as e:
            self.login_status.setText(f"❌ Login failed: {e}")

    # Set up news fetching
    def init_news_manager(self):
        self.news_manager = NewsManager()
        self.news_manager.load_news_sources("data/news_sources.csv")

    # Show main dashboard UI
    def show_main_interface(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.set_background(self.main_widget)

        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        self.title_label = QLabel("Reddit Dashboard")
        self.title_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        # Form for posting
        form_layout = QFormLayout()
        self.subreddit_input = QLineEdit()
        self.subreddit_input.setPlaceholderText("Enter subreddit name (no /r/)")

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter post title")

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Enter post body (optional)")
        self.body_input.setFixedHeight(100)

        self.post_type_combo = QComboBox()
        self.post_type_combo.addItems(["Text", "Link"])
        self.post_type_combo.currentTextChanged.connect(self.toggle_body_input)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL (for link post)")
        self.url_input.hide()

        form_layout.addRow("Subreddit:", self.subreddit_input)
        form_layout.addRow("Title:", self.title_input)
        form_layout.addRow("Post Type:", self.post_type_combo)
        form_layout.addRow("Body:", self.body_input)
        form_layout.addRow("URL:", self.url_input)

        main_layout.addLayout(form_layout)

        # Post to Reddit button
        self.post_button = QPushButton("Post to Reddit")
        self.post_button.setStyleSheet("background-color: #00CCCC; color: black; font-weight: bold;")
        self.post_button.clicked.connect(self.submit_post)
        main_layout.addWidget(self.post_button)

        # News dialog button
        self.news_button = QPushButton("📰 Browse News")
        self.news_button.setStyleSheet("background-color: #0099FF; color: white;")
        self.news_button.clicked.connect(self.open_news_dialog)
        main_layout.addWidget(self.news_button)

        # Output text area
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setStyleSheet("background-color: #222222; color: white; font-family: 'Courier New';")
        main_layout.addWidget(self.status_output)

    # Hide/show post fields depending on type
    def toggle_body_input(self, post_type):
        if post_type == "Link":
            self.body_input.hide()
            self.url_input.show()
        else:
            self.body_input.show()
            self.url_input.hide()

    # Show news reader dialog
    def open_news_dialog(self):
        dlg = NewsBrowserDialog(self.news_manager, self)
        dlg.exec_()

    # Post to Reddit
    def submit_post(self):
        if not self.authenticated:
            self.status_output.append("⚠️ Not authenticated.")
            return

        subreddit = self.subreddit_input.text().strip()
        title = self.title_input.text().strip()
        post_type = self.post_type_combo.currentText()
        body = self.body_input.toPlainText().strip() if post_type == "Text" else ""
        url = self.url_input.text().strip() if post_type == "Link" else ""

        if not subreddit or not title:
            self.status_output.append("⚠️ Subreddit and title are required.")
            return
        if post_type == "Link" and not url:
            self.status_output.append("⚠️ URL required for link post.")
            return

        try:
            sub = self.reddit.subreddit(subreddit)
            if post_type == "Text":
                post = sub.submit(title=title, selftext=body)
            else:
                post = sub.submit(title=title, url=url)
            self.status_output.append(f"✅ Posted to r/{subreddit}: {post.title}")
        except Exception as e:
            self.status_output.append(f"❌ Failed to post: {e}")

# Run app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    portal = DailyPlanetPortal()
    portal.show()
    sys.exit(app.exec_())
