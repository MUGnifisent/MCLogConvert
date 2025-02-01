import os
import re
from datetime import datetime

class Log:
    def __init__(self, log_paths: str | list, only_chat: bool):
        """
        Initializes the Log object.
        Args:
            log_paths (str or list): A single log file path or a list of log file paths.
        """
        if isinstance(log_paths, str):
            log_paths = [log_paths]
        self.log_paths = log_paths
        self.logs = {}  # {date: [(time, message)]}
        self._load_logs()
        if only_chat:
            self._clear_non_chat_logs()

    def _load_logs(self):
        """Loads logs from the given file paths and organizes them by date."""
        date_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})-\d+\.log$")
        time_pattern = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\] (.*)$")
        
        for path in self.log_paths:
            filename = os.path.basename(path)
            date_match = date_pattern.match(filename)
            if not date_match:
                continue  # Skip invalid filenames
            
            log_date = date_match.group(1)
            if log_date not in self.logs:
                self.logs[log_date] = []
                
            try:
                with open(path, "r", encoding="utf-8") as file:
                    for line in file:
                        time_match = time_pattern.match(line.strip())
                        if time_match:
                            log_time, message = time_match.groups()
                            self.logs[log_date].append((log_time, message))
            except FileNotFoundError:
                print(f"File not found: {path}")

    def _clear_non_chat_logs(self):
        """Removes all non-chat logs and cleans chat messages."""
        chat_identifier = "Async Chat Thread"
        chat_pattern = re.compile(r"\[Async Chat Thread - #\d+/INFO\]: (.+)")
        
        for date in self.logs:
            self.logs[date] = [
                (time, chat_pattern.match(message).group(1))
                for time, message in self.logs[date]
                if chat_identifier in message and chat_pattern.match(message)
            ]

    def get_logs(self) -> list:
        """
        Gets all logs from given files.
        Returns:
            list: List of logs in the format (date, time, message).
        """
        result = []
        for date in sorted(self.logs.keys()):
            for log_time, message in self.logs[date]:
                result.append((date, log_time, message))
        return result

    def get_logs_by_datetime(self, start: datetime, end: datetime) -> list:
        """
        Gets logs between two datetimes.
        Args:
            start (datetime): Start datetime.
            end (datetime): End datetime.
        Returns:
            list: List of logs in the format (date, time, message).
        """
        result = []
        for date in sorted(self.logs.keys()):
            current_date = datetime.strptime(date, "%Y-%m-%d")
            if start.date() <= current_date.date() <= end.date():
                for log_time, message in self.logs[date]:
                    log_datetime = datetime.strptime(f"{date} {log_time}", "%Y-%m-%d %H:%M:%S")
                    if start <= log_datetime <= end:
                        result.append((date, log_time, message))
        return result