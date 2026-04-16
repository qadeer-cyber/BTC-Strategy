#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path


def get_db_path():
    home = os.path.expanduser('~')
    app_data = os.path.join(home, 'Library', 'Application Support', 'PolyCopilot')
    os.makedirs(app_data, exist_ok=True)
    return os.path.join(app_data, 'polycopilot.db')


def get_log_dir():
    home = os.path.expanduser('~')
    log_dir = os.path.join(home, 'Library', 'Logs', 'PolyCopilot')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def load_config(db):
    defaults = {
        'poll_interval': 30,
        'top_n': 50,
        'copy_mode': 'fixed',
        'fixed_amount': 10.0,
        'proportional_percent': 10,
        'max_daily_loss': 100.0,
        'max_exposure': 500.0,
        'max_concurrent': 5,
        'sell_mode': 'all',
        'is_dry_run': True,
        'is_paper': True,
        'copy_buys_only': True,
        'stale_threshold_minutes': 60,
        'trader_filters': {
            'min_volume': 0,
            'min_pnl': 0,
            'min_trades': 0,
            'max_inactivity_days': 30
        },
        'bullpen_path': '/usr/local/bin/bullpen',
        'wallet_address': ''
    }
    
    for key, value in defaults.items():
        if db.get_setting(key) is None:
            db.set_setting(key, value)
    
    return db.get_all_settings()


def main():
    from storage.database import Database
    from utils.logger import get_logger
    from core.bot import Bot
    from core.scanner import Scanner
    from core.detector import Detector
    from core.copier import Copier
    from core.tracker import Tracker
    from app import App
    
    db_path = get_db_path()
    log_dir = get_log_dir()
    
    logger = get_logger('PolyCopilot', log_dir)
    logger.info('Starting PolyCopilot...', 'main')
    
    try:
        db = Database(db_path)
        logger.info(f'Database initialized at {db_path}', 'main')
    except Exception as e:
        logger.error(f'Failed to initialize database: {e}', 'main', exc_info=True)
        print(f'Error: Failed to initialize database: {e}')
        sys.exit(1)
    
    config = load_config(db)
    logger.info('Configuration loaded', 'main')
    
    bot = Bot(db, logger, config)
    
    scanner = Scanner(db, logger, config)
    detector = Detector(db, logger, config)
    copier = Copier(db, logger, config)
    tracker = Tracker(db, logger, config)
    
    bot.scanner = scanner
    bot.detector = detector
    bot.copier = copier
    bot.tracker = tracker
    
    saved_state = db.get_bot_state('bot_state', 'stopped')
    if saved_state == 'running':
        logger.info('Bot was running, resuming...', 'main')
        bot.start()
    elif saved_state == 'paused':
        logger.info('Bot was paused, ready to resume', 'main')
    
    logger.info('Launching UI...', 'main')
    
    try:
        app = App(db, logger, bot)
        app.run()
    except Exception as e:
        logger.error(f'UI error: {e}', 'main', exc_info=True)
        print(f'Error: {e}')
        sys.exit(1)
    
    logger.info('PolyCopilot shutting down...', 'main')
    bot.stop()


if __name__ == '__main__':
    main()