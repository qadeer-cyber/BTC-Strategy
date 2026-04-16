import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading


class Logger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name: str = 'PolyCopilot', log_dir: str = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.name = name
        self.log_dir = log_dir or self._get_default_log_dir()
        self._ensure_log_dir()
        
        self.log_file = os.path.join(self.log_dir, f'polycopilot_{datetime.now().strftime("%Y%m%d")}.log')
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            self._setup_handlers()

    def _get_default_log_dir(self) -> str:
        home = os.path.expanduser('~')
        return os.path.join(home, 'Library', 'Logs', 'PolyCopilot')

    def _ensure_log_dir(self):
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)

    def _setup_handlers(self):
        self.logger.handlers = []
        
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str, category: str = 'general'):
        self.logger.debug(f'[{category}] {message}')

    def info(self, message: str, category: str = 'general'):
        self.logger.info(f'[{category}] {message}')

    def warning(self, message: str, category: str = 'general'):
        self.logger.warning(f'[{category}] {message}')

    def error(self, message: str, category: str = 'general', exc_info: bool = False):
        self.logger.error(f'[{category}] {message}', exc_info=exc_info)

    def critical(self, message: str, category: str = 'general'):
        self.logger.critical(f'[{category}] {message}')

    def log_to_db(self, db, level: str, category: str, message: str, details: str = None):
        if db:
            try:
                db.add_log(level.lower(), category, message, details)
            except Exception as e:
                self.error(f'Failed to log to database: {e}', category='logger')

    def rotate_log(self):
        if self.log_file and os.path.exists(self.log_file):
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_name = self.log_file.replace('.log', f'_{date_str}.log')
            try:
                os.rename(self.log_file, new_name)
                self._setup_handlers()
            except Exception as e:
                self.error(f'Failed to rotate log: {e}', category='logger')

    def get_log_path(self) -> str:
        return self.log_file


def get_logger(name: str = 'PolyCopilot', log_dir: str = None) -> Logger:
    return Logger(name, log_dir)