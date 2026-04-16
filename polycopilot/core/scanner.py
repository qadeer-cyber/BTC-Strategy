import requests
import time
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .bot import Bot


class Scanner:
    def __init__(self, db, logger, config: Dict):
        self.db = db
        self.logger = logger
        self.config = config
        
        self.api_base = 'https://clob.polymarket.com'
        self._cached_traders = []
        self._last_fetch = None

    def load_traders(self):
        followed = self.db.get_followed_traders()
        self.logger.info(f'Loaded {len(followed)} followed traders', 'scanner')

    def fetch_leaderboard(self, limit: int = 50) -> List[Dict]:
        self.logger.info(f'Fetching top {limit} traders from leaderboard...', 'scanner')
        
        try:
            response = requests.get(
                f'{self.api_base}/leaderboard',
                params={'limit': limit},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                traders = data.get('results', []) if isinstance(data, dict) else data
                
                for trader in traders:
                    self._process_trader_data(trader)
                
                self._cached_traders = traders
                self._last_fetch = datetime.now()
                self.logger.info(f'Fetched {len(traders)} traders from leaderboard', 'scanner')
                return traders
            else:
                self.logger.error(f'Leaderboard fetch failed: {response.status_code}', 'scanner')
                return self._get_demo_traders()
                
        except Exception as e:
            self.logger.error(f'Error fetching leaderboard: {e}', 'scanner', exc_info=True)
            return self._get_demo_traders()

    def _process_trader_data(self, trader: Dict):
        wallet = trader.get('address') or trader.get('wallet') or trader.get(' trader_id')
        if not wallet:
            return
            
        display_name = trader.get('username') or trader.get('display_name') or wallet[:10]
        volume = trader.get('volume') or trader.get('total_volume') or 0
        pnl = trader.get('pnl') or trader.get('profit') or 0
        trades = trader.get('trade_count') or trader.get('trades') or 0
        last_active = trader.get('last_active') or trader.get('lastActive')
        
        self.db.add_trader(
            wallet_address=wallet,
            display_name=display_name,
            total_volume=volume,
            total_pnl=pnl,
            trade_count=trades,
            last_active=last_active
        )

    def filter_traders(self, traders: List[Dict]) -> List[Dict]:
        filters = self.config.get('trader_filters', {})
        min_volume = filters.get('min_volume', 0)
        min_pnl = filters.get('min_pnl', 0)
        min_trades = filters.get('min_trades', 0)
        max_inactivity_days = filters.get('max_inactivity_days', 30)
        
        filtered = []
        
        for trader in traders:
            volume = trader.get('total_volume', 0)
            pnl = trader.get('total_pnl', 0)
            trades = trader.get('trade_count', 0)
            
            last_active = trader.get('last_active')
            if last_active and max_inactivity_days:
                try:
                    last_date = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    if (datetime.now() - last_date).days > max_inactivity_days:
                        continue
                except:
                    pass
            
            if volume >= min_volume and pnl >= min_pnl and trades >= min_trades:
                filtered.append(trader)
        
        self.logger.info(f'Filtered to {len(filtered)} traders', 'scanner')
        return filtered

    def get_all_traders(self) -> List[Dict]:
        return self.db.get_all_traders()

    def get_followed_traders(self) -> List[Dict]:
        return self.db.get_followed_traders()

    def follow_trader(self, wallet_address: str):
        self.db.update_trader_follow_status(wallet_address, True)
        self.logger.info(f'Following trader: {wallet_address[:10]}...', 'scanner')

    def unfollow_trader(self, wallet_address: str):
        self.db.update_trader_follow_status(wallet_address, False)
        self.logger.info(f'Unfollowed trader: {wallet_address[:10]}...', 'scanner')

    def blacklist_trader(self, wallet_address: str):
        self.db.update_blacklist_status(wallet_address, True)
        self.logger.info(f'Blacklisted trader: {wallet_address[:10]}...', 'scanner')

    def unblacklist_trader(self, wallet_address: str):
        self.db.update_blacklist_status(wallet_address, False)
        self.logger.info(f'Removed from blacklist: {wallet_address[:10]}...', 'scanner')

    def get_blacklist(self) -> List[str]:
        return self.db.get_blacklist()

    def refresh_leaderboard(self) -> List[Dict]:
        return self.fetch_leaderboard(self.config.get('top_n', 50))

    def _get_demo_traders(self) -> List[Dict]:
        return [
            {
                'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
                'username': 'TraderAlpha',
                'volume': 125000,
                'pnl': 8500,
                'trade_count': 45,
                'last_active': datetime.now().isoformat()
            },
            {
                'address': '0x9B3aD3D84dFa4D8aB9d3b3e4f5A7C8D9e0F1B2a3',
                'username': 'CryptoWhale',
                'volume': 89000,
                'pnl': 6200,
                'trade_count': 32,
                'last_active': datetime.now().isoformat()
            },
            {
                'address': '0xAb5801a7D398351b8bE11C439e05C5B3259aEC9B',
                'username': 'BetMaster',
                'volume': 156000,
                'pnl': 12300,
                'trade_count': 67,
                'last_active': datetime.now().isoformat()
            }
        ]