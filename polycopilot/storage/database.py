import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traders (
                    wallet_address TEXT PRIMARY KEY,
                    display_name TEXT,
                    total_volume REAL DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    trade_count INTEGER DEFAULT 0,
                    last_active TEXT,
                    is_followed INTEGER DEFAULT 0,
                    is_whitelisted INTEGER DEFAULT 0,
                    is_blacklisted INTEGER DEFAULT 0,
                    last_seen_trade TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_signals (
                    signal_id TEXT PRIMARY KEY,
                    trader_wallet TEXT,
                    market_slug TEXT,
                    market_question TEXT,
                    outcome TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    timestamp TEXT,
                    detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    seen INTEGER DEFAULT 0,
                    FOREIGN KEY (trader_wallet) REFERENCES traders(wallet_address)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS copied_trades (
                    trade_id TEXT PRIMARY KEY,
                    signal_id TEXT,
                    trader_wallet TEXT,
                    market_slug TEXT,
                    market_question TEXT,
                    outcome TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    copied_price REAL,
                    copied_at TEXT,
                    status TEXT DEFAULT 'pending',
                    closed_at TEXT,
                    pnl REAL,
                    close_reason TEXT,
                    error_message TEXT,
                    source_trade_id TEXT,
                    FOREIGN KEY (trader_wallet) REFERENCES traders(wallet_address)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT,
                    market_slug TEXT,
                    outcome TEXT,
                    side TEXT,
                    amount REAL,
                    entry_price REAL,
                    current_price REAL,
                    opened_at TEXT,
                    status TEXT DEFAULT 'open',
                    FOREIGN KEY (trade_id) REFERENCES copied_trades(trade_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    category TEXT,
                    message TEXT,
                    details TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row['value'])
                except:
                    return row['value']
            return default

    def set_setting(self, key: str, value: Any):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            json_value = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                (key, json_value)
            )
            conn.commit()

    def get_all_settings(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM settings')
            result = {}
            for row in cursor.fetchall():
                try:
                    result[row['key']] = json.loads(row['value'])
                except:
                    result[row['key']] = row['value']
            return result

    def add_trader(self, wallet_address: str, display_name: str = None, 
                   total_volume: float = 0, total_pnl: float = 0, 
                   trade_count: int = 0, last_active: str = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO traders 
                (wallet_address, display_name, total_volume, total_pnl, 
                 trade_count, last_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (wallet_address, display_name, total_volume, total_pnl,
                  trade_count, last_active, datetime.now().isoformat()))
            conn.commit()

    def get_trader(self, wallet_address: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM traders WHERE wallet_address = ?',
                (wallet_address,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_followed_traders(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM traders WHERE is_followed = 1 ORDER BY display_name'
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_trader_follow_status(self, wallet_address: str, followed: bool):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE traders SET is_followed = ?, updated_at = ? WHERE wallet_address = ?',
                (1 if followed else 0, datetime.now().isoformat(), wallet_address)
            )
            conn.commit()

    def add_signal(self, signal: Dict):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO trade_signals 
                (signal_id, trader_wallet, market_slug, market_question, 
                 outcome, side, amount, price, timestamp, seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (signal.get('signal_id'), signal.get('trader_wallet'),
                  signal.get('market_slug'), signal.get('market_question'),
                  signal.get('outcome'), signal.get('side'),
                  signal.get('amount'), signal.get('price'),
                  signal.get('timestamp'), 0))
            conn.commit()

    def get_unseen_signals(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM trade_signals WHERE seen = 0 ORDER BY timestamp DESC'
            )
            return [dict(row) for row in cursor.fetchall()]

    def mark_signal_seen(self, signal_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE trade_signals SET seen = 1 WHERE signal_id = ?',
                (signal_id,)
            )
            conn.commit()

    def signal_exists(self, signal_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM trade_signals WHERE signal_id = ?',
                (signal_id,)
            )
            return cursor.fetchone() is not None

    def add_copied_trade(self, trade: Dict):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO copied_trades 
                (trade_id, signal_id, trader_wallet, market_slug, market_question,
                 outcome, side, amount, price, copied_price, copied_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trade.get('trade_id'), trade.get('signal_id'),
                  trade.get('trader_wallet'), trade.get('market_slug'),
                  trade.get('market_question'), trade.get('outcome'),
                  trade.get('side'), trade.get('amount'), trade.get('price'),
                  trade.get('copied_price'), trade.get('copied_at'),
                  trade.get('status', 'open')))
            conn.commit()

    def update_copied_trade_status(self, trade_id: str, status: str,
                                   pnl: float = None, close_reason: str = None,
                                   error_message: str = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            if status in ['closed', 'failed', 'skipped']:
                cursor.execute('''
                    UPDATE copied_trades 
                    SET status = ?, closed_at = ?, pnl = ?, close_reason = ?, 
                        error_message = ?
                    WHERE trade_id = ?
                ''', (status, now, pnl, close_reason, error_message, trade_id))
            else:
                cursor.execute('''
                    UPDATE copied_trades 
                    SET status = ? WHERE trade_id = ?
                ''', (status, trade_id))
            conn.commit()

    def get_copied_trade(self, trade_id: str) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM copied_trades WHERE trade_id = ?',
                (trade_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_open_trades(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM copied_trades WHERE status = 'open' ORDER BY copied_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_copied_trades(self, limit: int = 100) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM copied_trades ORDER BY copied_at DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_today_copied_trades(self) -> List[Dict]:
        today = datetime.now().strftime('%Y-%m-%d')
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM copied_trades WHERE copied_at LIKE ? ORDER BY copied_at DESC",
                (f'{today}%',)
            )
            return [dict(row) for row in cursor.fetchall()]

    def trade_exists(self, trade_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM copied_trades WHERE trade_id = ?',
                (trade_id,)
            )
            return cursor.fetchone() is not None

    def get_performance_stats(self) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_trades,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_trades,
                    SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped_trades,
                    SUM(CASE WHEN status = 'closed' AND pnl > 0 THEN pnl ELSE 0 END) as total_wins,
                    SUM(CASE WHEN status = 'closed' AND pnl < 0 THEN ABS(pnl) ELSE 0 END) as total_losses,
                    SUM(CASE WHEN status = 'closed' THEN pnl ELSE 0 END) as total_pnl
                FROM copied_trades
            ''')
            row = cursor.fetchone()
            
            stats = dict(row) if row else {}
            
            cursor.execute('''
                SELECT COUNT(*) as count FROM copied_trades 
                WHERE copied_at LIKE ?
            ''', (f'{datetime.now().strftime("%Y-%m-%d")}%',))
            today_row = cursor.fetchone()
            stats['today_trades'] = today_row['count'] if today_row else 0
            
            return stats

    def add_log(self, level: str, category: str, message: str, details: str = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO logs (level, category, message, details)
                VALUES (?, ?, ?, ?)
            ''', (level, category, message, details))
            conn.commit()

    def get_logs(self, limit: int = 500, level: str = None) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if level:
                cursor.execute(
                    'SELECT * FROM logs WHERE level = ? ORDER BY timestamp DESC LIMIT ?',
                    (level, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?',
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def clear_old_logs(self, days: int = 30):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM logs 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            conn.commit()

    def set_bot_state(self, key: str, value: Any):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            json_value = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute('''
                INSERT OR REPLACE INTO bot_state (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, json_value, datetime.now().isoformat()))
            conn.commit()

    def get_bot_state(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT value FROM bot_state WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row['value'])
                except:
                    return row['value']
            return default

    def get_all_traders(self, limit: int = 100) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM traders ORDER BY total_volume DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_blacklist(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT wallet_address FROM traders WHERE is_blacklisted = 1'
            )
            return [row['wallet_address'] for row in cursor.fetchall()]

    def get_whitelist(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT wallet_address FROM traders WHERE is_whitelisted = 1'
            )
            return [row['wallet_address'] for row in cursor.fetchall()]

    def update_blacklist_status(self, wallet_address: str, blacklisted: bool):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE traders SET is_blacklisted = ?, updated_at = ? WHERE wallet_address = ?',
                (1 if blacklisted else 0, datetime.now().isoformat(), wallet_address)
            )
            conn.commit()

    def update_whitelist_status(self, wallet_address: str, whitelisted: bool):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE traders SET is_whitelisted = ?, updated_at = ? WHERE wallet_address = ?',
                (1 if whitelisted else 0, datetime.now().isoformat(), wallet_address)
            )
            conn.commit()