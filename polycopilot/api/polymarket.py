import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


class PolyMarketClient:
    def __init__(self, api_base: str = 'https://clob.polymarket.com'):
        self.api_base = api_base
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'PolyCopilot/1.0'
        })

    def get_leaderboard(self, limit: int = 50) -> List[Dict]:
        try:
            response = self.session.get(
                f'{self.api_base}/leaderboard',
                params={'limit': limit},
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('results', []) if isinstance(response.json(), dict) else response.json()
        except Exception as e:
            raise Exception(f'Failed to fetch leaderboard: {e}')

    def get_trader_trades(self, wallet_address: str, limit: int = 50) -> List[Dict]:
        try:
            response = self.session.get(
                f'{self.api_base}/trades',
                params={'trader': wallet_address, 'limit': limit},
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data
        except Exception as e:
            raise Exception(f'Failed to fetch trader trades: {e}')

    def get_market(self, market_slug: str) -> Optional[Dict]:
        try:
            response = self.session.get(
                f'{self.api_base}/markets/{market_slug}',
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            raise Exception(f'Failed to fetch market: {e}')

    def get_markets(self, limit: int = 50, active: bool = True) -> List[Dict]:
        try:
            params = {'limit': limit}
            if active:
                params['active'] = 'true'
            
            response = self.session.get(
                f'{self.api_base}/markets',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data
        except Exception as e:
            raise Exception(f'Failed to fetch markets: {e}')

    def get_order_book(self, market_slug: str) -> Dict:
        try:
            response = self.session.get(
                f'{self.api_base}/orderbook/{market_slug}',
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f'Failed to fetch order book: {e}')

    def get_market_price(self, market_slug: str) -> Optional[float]:
        try:
            orderbook = self.get_order_book(market_slug)
            if orderbook and 'bids' in orderbook and orderbook['bids']:
                return orderbook['bids'][0].get('price')
            return None
        except:
            return None

    def get_positions(self, wallet_address: str) -> List[Dict]:
        try:
            response = self.session.get(
                f'{self.api_base}/positions',
                params={'address': wallet_address},
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', []) if isinstance(data, dict) else data
        except Exception as e:
            raise Exception(f'Failed to fetch positions: {e}')

    def get_user_info(self, wallet_address: str) -> Optional[Dict]:
        try:
            response = self.session.get(
                f'{self.api_base}/users/{wallet_address}',
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            raise Exception(f'Failed to fetch user info: {e}')

    def test_connection(self) -> bool:
        try:
            response = self.session.get(f'{self.api_base}/health', timeout=5)
            return response.status_code == 200
        except:
            return False