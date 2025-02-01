import sys
from datetime import datetime
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QColorDialog, QHBoxLayout, QPushButton, QLabel, QFrame

from app.ui import Ui_MainWindow
from app.util import Log, split_on_second_space, conv_html_to_pdf

class MCLogConvert(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # --- temporary measure
        self.ui.convertToHtml_checkBox.setChecked(True)
        self.ui.convertToHtml_checkBox.setEnabled(False)
        # --- TODO: rework behaviour

        self.setup_connections()

        self.selected_files = []
        self.nickname_colors = {}
        self.processed_logs = []
        
    def setup_connections(self):
        self.ui.chooseLogFiles_pushButton.clicked.connect(self.choose_files)
        self.ui.convert_pushButton.clicked.connect(self.convert_logs)
        
    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Log Files",
            "",
            "Log Files (*.log)"
        )
        if files:
            self.selected_files = files
            self.process_logs()
            
    def process_logs(self):
        # Create Log object and process files
        log_processor = Log(self.selected_files, only_chat=True)

        # Get all logs to extract nicknames
        logs = log_processor.get_logs()

        # Initialize variables for time tracking
        first_datetime = None
        last_datetime = None

        # Extract unique nicknames based on UI settings and track time range
        nicknames = set()
        self.processed_logs = []  # Clear existing processed logs

        for date, log_time, message in logs:
            # Convert date and time to datetime object
            current_datetime = datetime.strptime(f"{date} {log_time}", "%Y-%m-%d %H:%M:%S")

            # Update first and last datetime
            if first_datetime is None or current_datetime < first_datetime:
                first_datetime = current_datetime
            if last_datetime is None or current_datetime > last_datetime:
                last_datetime = current_datetime

            prefix = "[Not Secure] "
            if prefix in message:
                message = message.removeprefix(prefix)

            # Handle prefix with/without space based on radio button
            if self.ui.spacedPrefix_radioButton.isChecked():
                parts = split_on_second_space(message)
                if len(parts) > 1:
                    nickname, message = parts[0], parts[1]
                    nicknames.add(nickname)
                    self.processed_logs.append([date, log_time, nickname, message])
            elif self.ui.noPrefix_radioButton.isChecked():
                # Split without space
                parts = message.split(" ", 1)
                if len(parts) > 1:
                    nickname, message = parts[0], parts[1]
                    nicknames.add(nickname)
                    self.processed_logs.append([date, log_time, nickname, message])

        # Set the datetime fields in the UI
        if first_datetime and last_datetime:
            self.ui.start_dateTimeEdit.setDateTime(first_datetime)
            self.ui.end_dateTimeEdit.setDateTime(last_datetime)

        # Clear existing widgets in scroll area
        while self.ui.verticalLayout_3.count():
            item = self.ui.verticalLayout_3.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create color picker for each nickname
        for nickname in sorted(nicknames):
            frame = QFrame()
            layout = QHBoxLayout(frame)

            label = QLabel(nickname)
            color_button = QPushButton("Pick Color")
            color_button.nickname = nickname  # Store nickname reference
            color_button.clicked.connect(self.pick_color)

            layout.addWidget(label)
            layout.addWidget(color_button)

            self.ui.verticalLayout_3.addWidget(frame)

        # Switch to parse options page
        self.ui.stackedWidget.setCurrentIndex(1)

    def pick_color(self):
        button = self.sender()
        color = QColorDialog.getColor()
        if color.isValid():
            self.nickname_colors[button.nickname] = color
            button.setStyleSheet(f"background-color: {color.name()}")
            
    def convert_logs(self):
        # Get the time range from UI
        start_time = self.ui.start_dateTimeEdit.dateTime().toPyDateTime()
        end_time = self.ui.end_dateTimeEdit.dateTime().toPyDateTime()

        # Filter logs based on time range
        filtered_logs = []
        for date, time, nickname, message in self.processed_logs:
            log_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
            if start_time <= log_datetime <= end_time:
                filtered_logs.append((date, time, nickname, message))

        # Create HTML header content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    background-color: #1a1a1a;
                    color: #ffffff;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                }
                .chat-container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                .message {
                    margin-bottom: 10px;
                    padding: 8px;
                    border-radius: 5px;
                    background-color: #2a2a2a;
                }
                .timestamp {
                    color: #888888;
                    font-size: 0.8em;
                    margin-bottom: 4px;
                }
                .nickname {
                    font-weight: bold;
                    margin-right: 8px;
                }
                .content {
                    word-wrap: break-word;
                }
                .italicized {
                    font-style: italic;
                }
                .asterisk {
                    color: #888888;
                }
            </style>
        </head>
        <body>
            <div class="chat-container">
        """

        # Get pattern settings
        ignore_start = self.ui.ignoreLineStart_lineEdit.text()
        ignore_end = self.ui.ignoreLineEnd_lineEdit.text()
        italicize_start = self.ui.italicizeLineStart_lineEdit.text()
        italicize_end = self.ui.italicizeLineEnd_lineEdit.text()

        def format_message(date, time, nickname, message, color):
            """Helper function to format a single message"""
            should_italicize = (self.ui.italicizeLines_checkBox.isChecked() and 
                              message.startswith(italicize_start) and 
                              message.endswith(italicize_end))

            if should_italicize:
                content_class = 'content italicized'
                message = message.removeprefix(italicize_start).removesuffix(italicize_end)
                prefix = '<span class="asterisk">* </span>'
            else:
                content_class = 'content'
                prefix = ''

            return f"""
                <div class="message">
                    <div class="timestamp">{date} {time}</div>
                    <div>
                        {prefix}
                        <span class="nickname" style="color: {color}">{nickname}</span>
                        <span class="{content_class}">{message}</span>
                    </div>
                </div>
            """

        # Add messages
        for date, time, nickname, full_message in filtered_logs:
            # Skip ignored messages if checkbox is checked
            if (self.ui.ignoreLines_checkBox.isChecked() and 
                full_message.startswith(ignore_start) and 
                full_message.endswith(ignore_end)):
                continue

            # Get color for nickname
            color = self.nickname_colors.get(nickname, "#ffffff")
            if hasattr(color, 'name'):
                color = color.name()

            # Add formatted message to HTML content
            html_content += format_message(date, time, nickname, full_message, color)

        # Close HTML tags
        html_content += """
            </div>
        </body>
        </html>
        """

        # Save HTML file
        base_filename = os.path.splitext(self.selected_files[0])[0]
        html_filename = f"{base_filename}_converted.html"

        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Convert to PDF if checkbox is checked
        if self.ui.convertToPdf_checkBox.isChecked():
            pdf_filename = f"{base_filename}_converted.pdf"
            conv_html_to_pdf(html_content, pdf_filename)

        # Switch back to the first page
        self.ui.stackedWidget.setCurrentIndex(0)

def run():
    app = QApplication(sys.argv)
    window = MCLogConvert()
    window.show()
    sys.exit(app.exec())