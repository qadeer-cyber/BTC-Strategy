from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict


class Tracker:
    def __init__(self, db, logger, config: Dict):
        self.db = db
        self.logger = logger
        self.config = config

    def get_performance_summary(self) -> Dict[str, Any]:
        stats = self.db.get_performance_stats()
        
        total_trades = stats.get('total_trades') or 0
        closed_trades = stats.get('closed_trades') or 0
        failed_trades = stats.get('failed_trades') or 0
        skipped_trades = stats.get('skipped_trades') or 0
        
        total_pnl = stats.get('total_pnl') or 0
        total_wins = stats.get('total_wins') or 0
        total_losses = stats.get('total_losses') or 0
        
        win_rate = 0
        if closed_trades > 0:
            winners = len([t for t in self.db.get_all_copied_trades(limit=10000) 
                         if t.get('status') == 'closed' and t.get('pnl', 0) > 0])
            win_rate = (winners / closed_trades) * 100
        
        avg_win = 0
        avg_loss = 0
        if total_wins > 0:
            avg_win = total_wins / max(1, len([t for t in self.db.get_all_copied_trades(limit=10000) 
                                               if t.get('status') == 'closed' and t.get('pnl', 0) > 0]))
        if total_losses > 0:
            avg_loss = total_losses / max(1, len([t for t in self.db.get_all_copied_trades(limit=10000) 
                                                 if t.get('status') == 'closed' and t.get('pnl', 0) < 0]))
        
        expectancy = 0
        if win_rate > 0 and avg_loss > 0:
            win_decimal = win_rate / 100
            loss_decimal = 1 - win_decimal
            expectancy = (win_decimal * avg_win) - (loss_decimal * avg_loss)
        
        today_trades = self.db.get_today_copied_trades()
        today_pnl = sum(t.get('pnl', 0) for t in today_trades if t.get('pnl'))
        today_winners = len([t for t in today_trades if t.get('pnl', 0) > 0])
        today_losers = len([t for t in today_trades if t.get('pnl', 0) < 0])
        
        return {
            'total_trades': total_trades,
            'closed_trades': closed_trades,
            'open_trades': len(self.db.get_open_trades()),
            'failed_trades': failed_trades,
            'skipped_trades': skipped_trades,
            'total_pnl': total_pnl,
            'today_pnl': today_pnl,
            'today_trades': len(today_trades),
            'win_rate': round(win_rate, 2),
            'winners': today_winners,
            'losers': today_losers,
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'expectancy': round(expectancy, 2),
            'profit_factor': round(total_wins / max(0.01, total_losses), 2) if total_losses else 0,
            'largest_win': self._get_largest_win(),
            'largest_loss': self._get_largest_loss(),
            'current_exposure': self._get_current_exposure()
        }

    def _get_largest_win(self) -> float:
        trades = self.db.get_all_copied_trades(limit=1000)
        return max([t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0], default=0)

    def _get_largest_loss(self) -> float:
        trades = self.db.get_all_copied_trades(limit=1000)
        return min([t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0], default=0)

    def _get_current_exposure(self) -> float:
        open_trades = self.db.get_open_trades()
        return sum(t.get('amount', 0) for t in open_trades)

    def get_per_trader_stats(self) -> List[Dict]:
        all_trades = self.db.get_all_copied_trades(limit=10000)
        
        trader_stats = defaultdict(lambda: {
            'trades': 0,
            'closed': 0,
            'wins': 0,
            'losses': 0,
            'pnl': 0,
            'amount': 0
        })
        
        for trade in all_trades:
            wallet = trade.get('trader_wallet')
            if not wallet:
                continue
            
            stats = trader_stats[wallet]
            stats['trades'] += 1
            stats['amount'] += trade.get('amount', 0)
            
            if trade.get('status') == 'closed':
                stats['closed'] += 1
                pnl = trade.get('pnl', 0)
                stats['pnl'] += pnl
                if pnl > 0:
                    stats['wins'] += 1
                elif pnl < 0:
                    stats['losses'] += 1
        
        result = []
        for wallet, stats in trader_stats.items():
            win_rate = (stats['wins'] / stats['closed'] * 100) if stats['closed'] > 0 else 0
            result.append({
                'wallet': wallet,
                'total_trades': stats['trades'],
                'closed_trades': stats['closed'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': round(win_rate, 2),
                'pnl': round(stats['pnl'], 2),
                'total_volume': round(stats['amount'], 2)
            })
        
        return sorted(result, key=lambda x: x['pnl'], reverse=True)

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        daily_data = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            trades = [t for t in self.db.get_all_copied_trades(limit=10000) 
                      if t.get('copied_at', '').startswith(date)]
            
            pnl = sum(t.get('pnl', 0) for t in trades if t.get('pnl'))
            winners = len([t for t in trades if t.get('pnl', 0) > 0])
            losers = len([t for t in trades if t.get('pnl', 0) < 0])
            
            daily_data.append({
                'date': date,
                'trades': len(trades),
                'pnl': round(pnl, 2),
                'winners': winners,
                'losers': losers,
                'win_rate': round((winners / len(trades) * 100), 2) if trades else 0
            })
        
        return daily_data

    def get_market_stats(self) -> List[Dict]:
        all_trades = self.db.get_all_copied_trades(limit=10000)
        
        market_stats = defaultdict(lambda: {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'pnl': 0,
            'volume': 0
        })
        
        for trade in all_trades:
            market = trade.get('market_slug', 'unknown')
            stats = market_stats[market]
            stats['trades'] += 1
            stats['volume'] += trade.get('amount', 0)
            
            if trade.get('status') == 'closed':
                pnl = trade.get('pnl', 0)
                stats['pnl'] += pnl
                if pnl > 0:
                    stats['wins'] += 1
                elif pnl < 0:
                    stats['losses'] += 1
        
        result = []
        for market, stats in market_stats.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            result.append({
                'market': market,
                'trades': stats['trades'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': round(win_rate, 2),
                'pnl': round(stats['pnl'], 2),
                'volume': round(stats['volume'], 2)
            })
        
        return sorted(result, key=lambda x: x['pnl'], reverse=True)

    def calculate_pnl(self, trade: Dict, current_price: float = None) -> float:
        if trade.get('status') != 'open':
            return trade.get('pnl', 0)
        
        entry_price = trade.get('copied_price', 0)
        side = trade.get('side', '')
        
        if current_price is None:
            current_price = entry_price
        
        amount = trade.get('amount', 0)
        
        if side == 'buy':
            return (current_price - entry_price) * amount
        else:
            return (entry_price - current_price) * amount

    def close_trade(self, trade_id: str, close_price: float, reason: str = 'manual'):
        trade = self.db.get_copied_trade(trade_id)
        if not trade:
            return False
        
        pnl = self.calculate_pnl(trade, close_price)
        
        self.db.update_copied_trade_status(
            trade_id, 
            'closed', 
            pnl=pnl, 
            close_reason=reason
        )
        
        self.logger.info(f'Trade closed: {trade_id[:8]}... PnL: ${pnl:.2f}', 'tracker')
        return True

    def update_open_positions(self, prices: Dict[str, float]):
        open_trades = self.db.get_open_trades()
        
        for trade in open_trades:
            market = trade.get('market_slug')
            if market in prices:
                pnl = self.calculate_pnl(trade, prices[market])
                self.logger.debug(f'Position update: {trade.get("trade_id")[:8]}... PnL: ${pnl:.2f}', 'tracker')