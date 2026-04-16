import time
import threading
import queue
from enum import Enum
from typing import Callable, Optional, Dict, Any
from datetime import datetime


class BotState(Enum):
    STOPPED = 'stopped'
    RUNNING = 'running'
    PAUSED = 'paused'
    STARTING = 'starting'
    STOPPING = 'stopping'


class Bot:
    def __init__(self, db, logger, config: Dict[str, Any]):
        self.db = db
        self.logger = logger
        self.config = config
        
        self._state = BotState.STOPPED
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        self._signal_queue = queue.Queue()
        self._status_callbacks = []
        
        self._poll_interval = config.get('poll_interval', 30)
        self._is_dry_run = config.get('is_dry_run', True)
        self._is_paper = config.get('is_paper', False)
        
        self._last_poll_time = None
        self._last_trade_time = None
        self._trades_today = 0
        self._today_date = datetime.now().date()
        
        self.scanner = None
        self.detector = None
        self.copier = None
        self.tracker = None

    @property
    def state(self) -> BotState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state == BotState.RUNNING

    @property
    def is_paused(self) -> bool:
        return self._state == BotState.PAUSED

    @property
    def is_dry_run(self) -> bool:
        return self._is_dry_run

    @property
    def is_paper(self) -> bool:
        return self._is_paper

    def get_status(self) -> Dict[str, Any]:
        today = datetime.now().date()
        if self._today_date != today:
            self._trades_today = 0
            self._today_date = today
        
        return {
            'state': self._state.value,
            'is_dry_run': self._is_dry_run,
            'is_paper': self._is_paper,
            'poll_interval': self._poll_interval,
            'trades_today': self._trades_today,
            'last_poll': self._last_poll_time.isoformat() if self._last_poll_time else None,
            'last_trade': self._last_trade_time.isoformat() if self._last_trade_time else None,
            'followed_count': len(self.db.get_followed_traders()),
            'open_positions': len(self.db.get_open_trades()),
            'is_running': self.is_running,
            'is_paused': self.is_paused
        }

    def on_status_change(self, callback: Callable):
        self._status_callbacks.append(callback)

    def _notify_status_change(self):
        for cb in self._status_callbacks:
            try:
                cb(self.get_status())
            except Exception as e:
                self.logger.error(f'Status callback error: {e}', 'bot')

    def set_mode(self, is_dry_run: bool, is_paper: bool):
        self._is_dry_run = is_dry_run
        self._is_paper = is_paper
        self.logger.info(f'Bot mode: dry_run={is_dry_run}, paper={is_paper}', 'bot')
        self.db.set_setting('is_dry_run', is_dry_run)
        self.db.set_setting('is_paper', is_paper)

    def start(self) -> bool:
        if self._state in [BotState.RUNNING, BotState.STARTING]:
            self.logger.warning('Bot already starting or running', 'bot')
            return False

        self.logger.info('Starting bot...', 'bot')
        self._state = BotState.STARTING
        self._notify_status_change()

        self._stop_event.clear()
        self._pause_event.set()

        try:
            if self.scanner:
                self.scanner.load_traders()
            if self.detector:
                self.detector.load_seen_trades()
            
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            
            self._state = BotState.RUNNING
            self.db.set_bot_state('bot_state', 'running')
            self.logger.info('Bot started successfully', 'bot')
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to start bot: {e}', 'bot', exc_info=True)
            self._state = BotState.STOPPED
            self._notify_status_change()
            return False

    def stop(self):
        if self._state == BotState.STOPPED:
            return

        self.logger.info('Stopping bot...', 'bot')
        self._state = BotState.STOPPING
        self._notify_status_change()

        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

        self._state = BotState.STOPPED
        self.db.set_bot_state('bot_state', 'stopped')
        self.logger.info('Bot stopped', 'bot')
        self._notify_status_change()

    def pause(self):
        if self._state != BotState.RUNNING:
            return

        self.logger.info('Pausing bot...', 'bot')
        self._pause_event.clear()
        self._state = BotState.PAUSED
        self.db.set_bot_state('bot_state', 'paused')
        self._notify_status_change()
        self.logger.info('Bot paused', 'bot')

    def resume(self):
        if self._state != BotState.PAUSED:
            return

        self.logger.info('Resuming bot...', 'bot')
        self._pause_event.set()
        self._state = BotState.RUNNING
        self.db.set_bot_state('bot_state', 'running')
        self._notify_status_change()
        self.logger.info('Bot resumed', 'bot')

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self._pause_event.wait()
                
                if self._stop_event.is_set():
                    break
                
                self._poll()
                
                for _ in range(self._poll_interval):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f'Bot loop error: {e}', 'bot', exc_info=True)
                time.sleep(5)

    def _poll(self):
        try:
            self.logger.debug('Polling for new trades...', 'bot')
            self._last_poll_time = datetime.now()
            
            if self.detector:
                signals = self.detector.poll_new_trades()
                
                for signal in signals:
                    self._handle_signal(signal)
                    
        except Exception as e:
            self.logger.error(f'Poll error: {e}', 'bot', exc_info=True)

    def _handle_signal(self, signal: Dict):
        try:
            if self.copier:
                result = self.copier.execute_copy(signal)
                
                if result.get('success'):
                    self._trades_today += 1
                    self._last_trade_time = datetime.now()
                    self.logger.info(
                        f"Trade copied: {signal.get('market_question')} - "
                        f"{signal.get('side')} {signal.get('amount')}",
                        'bot'
                    )
                else:
                    reason = result.get('reason', 'unknown')
                    self.logger.warning(f'Copy skipped: {reason}', 'bot')
                    
            self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f'Error handling signal: {e}', 'bot', exc_info=True)

    def update_config(self, config: Dict):
        self.config.update(config)
        if 'poll_interval' in config:
            self._poll_interval = config['poll_interval']
        self.logger.debug(f'Config updated: {list(config.keys())}', 'bot')

    def get_recent_signals(self, limit: int = 20):
        if self.detector:
            return self.detector.get_recent_signals(limit)
        return []

    def get_performance(self):
        if self.tracker:
            return self.tracker.get_performance_summary()
        return {}