import threading
from typing import Dict, List, Callable, Optional
from datetime import datetime
from enum import Enum


class AlertLevel(Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class Alert:
    def __init__(self, level: AlertLevel, title: str, message: str, details: str = None):
        self.level = level
        self.title = title
        self.message = message
        self.details = details
        self.timestamp = datetime.now()
        self.id = f"{self.timestamp.strftime('%Y%m%d%H%M%S')}_{id(self)}"

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class AlertManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._alerts: List[Alert] = []
        self._max_alerts = 100
        self._listeners: List[Callable] = []

    def add_alert(self, level: AlertLevel, title: str, message: str, details: str = None):
        alert = Alert(level, title, message, details)
        
        with self._lock:
            self._alerts.append(alert)
            
            if len(self._alerts) > self._max_alerts:
                self._alerts = self._alerts[-self._max_alerts:]
        
        self._notify_listeners(alert)
        
        return alert

    def info(self, title: str, message: str, details: str = None):
        return self.add_alert(AlertLevel.INFO, title, message, details)

    def warning(self, title: str, message: str, details: str = None):
        return self.add_alert(AlertLevel.WARNING, title, message, details)

    def error(self, title: str, message: str, details: str = None):
        return self.add_alert(AlertLevel.ERROR, title, message, details)

    def critical(self, title: str, message: str, details: str = None):
        return self.add_alert(AlertLevel.CRITICAL, title, message, details)

    def get_alerts(self, limit: int = 50, level: AlertLevel = None) -> List[Alert]:
        with self._lock:
            alerts = self._alerts[-limit:]
            
            if level:
                alerts = [a for a in alerts if a.level == level]
            
            return alerts

    def get_unread_count(self) -> int:
        return len(self._alerts)

    def clear_alerts(self):
        with self._lock:
            self._alerts.clear()

    def register_listener(self, callback: Callable):
        self._listeners.append(callback)

    def unregister_listener(self, callback: Callable):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, alert: Alert):
        for listener in self._listeners:
            try:
                listener(alert)
            except Exception:
                pass


def get_alert_manager() -> AlertManager:
    return AlertManager()


class StatusIndicator:
    @staticmethod
    def get_bot_state_indicator(state: str) -> str:
        indicators = {
            'running': '●',
            'paused': '◐',
            'stopped': '○',
            'starting': '◔',
            'stopping': '◔'
        }
        return indicators.get(state, '○')

    @staticmethod
    def get_connection_indicator(connected: bool) -> str:
        return '●' if connected else '○'

    @staticmethod
    def get_pnl_indicator(pnl: float) -> str:
        if pnl > 0:
            return '+'
        elif pnl < 0:
            return '-'
        return ''

    @staticmethod
    def get_trade_status_indicator(status: str) -> str:
        indicators = {
            'open': '◐',
            'closed': '●',
            'failed': '✕',
            'skipped': '○'
        }
        return indicators.get(status, '?')

    @staticmethod
    def get_level_indicator(level: AlertLevel) -> str:
        indicators = {
            AlertLevel.INFO: 'ℹ',
            AlertLevel.WARNING: '⚠',
            AlertLevel.ERROR: '✕',
            AlertLevel.CRITICAL: '⚡'
        }
        return indicators.get(level, '?')