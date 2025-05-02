import sys
import math
import os
from dotenv import load_dotenv
import praw
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QFrame,
                             QMessageBox, QTextEdit, QComboBox, QDialog, QFormLayout)
from PyQt5.QtGui import (QPixmap, QPalette, QBrush, QPainter, QColor, QFont, QImage)
from PyQt5.QtCore import (Qt, QTimer, QPropertyAnimation, QRectF, pyqtProperty)

# Load environment variables from custom file
load_dotenv(dotenv_path="DailyPlanetPortal.env")  # fixed format for explicit env file

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
        color = QColor("#00FFFF")
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

class DailyPlanetPortal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reddit = None
        self.authenticated = False
        self.loading_value = 0
        self.messages = [
            "Initializing portal systems...",
            "Loading security protocols...",
            "Establishing connection...",
            "Verifying credentials...",
            "Preparing dashboard..."
        ]
        self.current_message = 0
        self.background_image = QImage("/Users/kodan/Desktop/DailyPlanetPortal/dpgui.png")

        self.setWindowTitle("Daily Planet Reddit Portal")
        self.resize(1200, 800)
        self.setAutoFillBackground(True)

        self.init_loading_screen()

    def set_background(self, widget):
        if not self.background_image.isNull():
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
                user_agent="DailyPlanetPortal/0.1 by YOUR_USERNAME",
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

        title = QLabel("\U0001F6F0\uFE0F DAILY PLANET PORTAL")
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

        post_button = QPushButton("\U0001F4E4 Post News to Reddit")
        post_button.setFixedSize(250, 60)
        post_button.setStyleSheet(self.button_style())
        post_button.clicked.connect(self.show_post_dialog)

        view_button = QPushButton("\U0001F4CA View My Activity")
        view_button.setFixedSize(250, 60)
        view_button.setStyleSheet(self.button_style())
        view_button.clicked.connect(self.view_my_activity)

        browse_button = QPushButton("\U0001F525 Browse Hot News")
        browse_button.setFixedSize(250, 60)
        browse_button.setStyleSheet(self.button_style())
        browse_button.clicked.connect(self.browse_hot_news)

        buttons_layout.addWidget(post_button)
        buttons_layout.addWidget(view_button)
        buttons_layout.addWidget(browse_button)

        layout.addLayout(buttons_layout)

        footer = QLabel("Secure Access Enabled | Daily Planet v1.2 \U0001F680")
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
        dialog.setWindowTitle("\U0001F4E4 Post News to Reddit")
        dialog.resize(400, 300)
        layout = QFormLayout()

        self.sample_titles = [
            "Breaking: AI Model Sets New Accuracy Record",
            "Python 3.13 Beta Released!",
            "F1 2025 Season Kick-off Details",
            "World Leaders Convene for Climate Talks"
        ]

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
            subreddit = self.reddit.subreddit("test")  # use your own subreddit here
            post = subreddit.submit(title=selected_title, selftext=comment_text)
            QMessageBox.information(self, "Success", f"Posted successfully: {post.title}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to post: {str(e)}")

    # -- beginning of the file remains unchanged --

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
                    summary_box.setText(f"Title: {post.title}\n\nURL: {post.url}\n\nScore: {post.score}")

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
            posts = list(self.reddit.subreddit("worldnews+technology+python+F1+machinelearning").hot(limit=10))

            dialog = QDialog(self)
            dialog.setWindowTitle("🔥 Browse Trending News")
            dialog.resize(600, 400)
            layout = QVBoxLayout()

            self.news_list = QComboBox()
            self.news_posts = []
            for post in posts:
                self.news_posts.append(post)
                self.news_list.addItem(post.title)

            summary_box = QTextEdit()
            summary_box.setReadOnly(True)

            def show_news_summary():
                index = self.news_list.currentIndex()
                if index >= 0 and index < len(self.news_posts):
                    post = self.news_posts[index]
                    summary_box.setText(f"Title: {post.title}\n\nURL: {post.url}\n\nScore: {post.score}")

            self.news_list.currentIndexChanged.connect(show_news_summary)

            layout.addWidget(self.news_list)
            layout.addWidget(summary_box)
            dialog.setLayout(layout)
            show_news_summary()
            dialog.exec_()

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
