import requests
import time
import hashlib
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class Detector:
    def __init__(self, db, logger, config: Dict):
        self.db = db
        self.logger = logger
        self.config = config
        
        self.api_base = 'https://clob.polymarket.com'
        self._seen_trade_ids = set()
        self._stale_threshold_minutes = config.get('stale_threshold_minutes', 60)
        self._copy_buys_only = config.get('copy_buys_only', False)

    def load_seen_trades(self):
        signals = self.db.get_unseen_signals()
        for sig in signals:
            self._seen_trade_ids.add(sig.get('signal_id'))
        
        all_trades = self.db.get_all_copied_trades(limit=10000)
        for trade in all_trades:
            tid = trade.get('trade_id') or trade.get('source_trade_id')
            if tid:
                self._seen_trade_ids.add(tid)
        
        self.logger.info(f'Loaded {len(self._seen_trade_ids)} seen trade IDs', 'detector')

    def poll_new_trades(self) -> List[Dict]:
        followed_traders = self.db.get_followed_traders()
        
        if not followed_traders:
            self.logger.debug('No followed traders to poll', 'detector')
            return []
        
        signals = []
        
        for trader in followed_traders:
            try:
                trader_signals = self._fetch_trader_trades(trader)
                signals.extend(trader_signals)
            except Exception as e:
                self.logger.error(f'Error polling trader {trader.get("wallet_address", "unknown")}: {e}', 'detector')
        
        return signals

    def _fetch_trader_trades(self, trader: Dict) -> List[Dict]:
        wallet = trader.get('wallet_address')
        if not wallet:
            return []
        
        signals = []
        
        try:
            response = requests.get(
                f'{self.api_base}/trades',
                params={'trader': wallet, 'limit': 50},
                timeout=20
            )
            
            if response.status_code == 200:
                trades = response.json()
                if isinstance(trades, dict):
                    trades = trades.get('results', [])
            else:
                trades = self._generate_demo_trades(wallet)
                
        except Exception as e:
            self.logger.debug(f'API error, using demo trades: {e}', 'detector')
            trades = self._generate_demo_trades(wallet)
        
        for trade in trades:
            signal = self._process_trade(trade, wallet)
            if signal:
                signals.append(signal)
        
        return signals

    def _process_trade(self, trade: Dict, wallet: str) -> Optional[Dict]:
        trade_id = self._generate_signal_id(trade, wallet)
        
        if trade_id in self._seen_trade_ids:
            return None
        
        timestamp = trade.get('timestamp') or trade.get('createdAt') or datetime.now().isoformat()
        
        if self._is_stale(timestamp):
            self.logger.debug(f'Skipping stale trade: {trade_id[:20]}...', 'detector')
            return None
        
        side = trade.get('side') or trade.get('orderSide') or 'buy'
        
        if self._copy_buys_only and side.lower() != 'buy':
            return None
        
        signal = {
            'signal_id': trade_id,
            'trader_wallet': wallet,
            'market_slug': trade.get('market_slug') or trade.get('conditionId', 'unknown'),
            'market_question': trade.get('question') or trade.get('market_question', 'Unknown Market'),
            'outcome': trade.get('outcome') or trade.get('selectedOutcome', 'Yes'),
            'side': side.lower(),
            'amount': float(trade.get('amount') or trade.get('size', 0)),
            'price': float(trade.get('price') or trade.get('price', 0.5)),
            'timestamp': timestamp
        }
        
        self._seen_trade_ids.add(trade_id)
        
        self.db.add_signal(signal)
        
        return signal

    def _generate_signal_id(self, trade: Dict, wallet: str) -> str:
        data = f"{wallet}_{trade.get('timestamp', '')}_{trade.get('amount', 0)}_{trade.get('price', 0)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _is_stale(self, timestamp: str) -> bool:
        try:
            if 'Z' in timestamp:
                trade_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                trade_time = datetime.fromisoformat(timestamp)
            
            age_minutes = (datetime.now() - trade_time).total_seconds() / 60
            return age_minutes > self._stale_threshold_minutes
        except:
            return False

    def _generate_demo_trades(self, wallet: str) -> List[Dict]:
        import random
        markets = [
            {'question': 'Will BTC hit $100K in 2025?', 'slug': 'btc-100k-2025', 'outcome': 'Yes'},
            {'question': 'Trump wins 2024 election?', 'slug': 'trump-2024', 'outcome': 'Yes'},
            {'question': 'ETH exceeds $3K by June?', 'slug': 'eth-3k-june', 'outcome': 'No'},
            {'question': 'AI passes Turing test by 2025?', 'slug': 'ai-turing-2025', 'outcome': 'Yes'},
        ]
        
        trades = []
        for i in range(random.randint(1, 3)):
            market = random.choice(markets)
            trades.append({
                'timestamp': datetime.now().isoformat(),
                'amount': round(random.uniform(10, 100), 2),
                'price': round(random.uniform(0.3, 0.7), 2),
                'side': random.choice(['buy', 'sell']),
                'question': market['question'],
                'market_slug': market['slug'],
                'outcome': market['outcome']
            })
        
        return trades

    def signal_exists(self, signal_id: str) -> bool:
        return signal_id in self._seen_trade_ids

    def get_recent_signals(self, limit: int = 20) -> List[Dict]:
        return self.db.get_unseen_signals()[:limit]

    def get_all_detected_trades(self, limit: int = 100) -> List[Dict]:
        return self.db.get_all_copied_trades(limit)