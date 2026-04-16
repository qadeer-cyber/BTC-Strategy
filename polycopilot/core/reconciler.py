from typing import Dict, List, Optional
from datetime import datetime


class Reconciler:
    def __init__(self, db, logger, config: Dict):
        self.db = db
        self.logger = logger
        self.config = config

    def reconcile_positions(self, current_positions: List[Dict]) -> Dict:
        self.logger.info('Starting position reconciliation...', 'reconciler')
        
        open_trades = self.db.get_open_trades()
        
        synced_positions = []
        discrepancies = []
        
        for local_trade in open_trades:
            local_id = local_trade.get('trade_id')
            market = local_trade.get('market_slug')
            
            matching = next(
                (p for p in current_positions if p.get('market') == market),
                None
            )
            
            if matching:
                synced_positions.append({
                    'local_id': local_id,
                    'remote_id': matching.get('position_id'),
                    'market': market,
                    'status': 'synced'
                })
            else:
                discrepancies.append({
                    'local_id': local_id,
                    'market': market,
                    'issue': 'not_found_in_remote'
                })
        
        for remote_pos in current_positions:
            market = remote_pos.get('market')
            local_match = next(
                (t for t in open_trades if t.get('market_slug') == market),
                None
            )
            
            if not local_match:
                discrepancies.append({
                    'remote_id': remote_pos.get('position_id'),
                    'market': market,
                    'issue': 'not_found_locally'
                })
        
        self.logger.info(
            f'Reconciliation: {len(synced_positions)} synced, {len(discrepancies)} discrepancies',
            'reconciler'
        )
        
        return {
            'synced': synced_positions,
            'discrepancies': discrepancies,
            'total_open': len(open_trades),
            'total_remote': len(current_positions)
        }

    def detect_resolved_markets(self) -> List[Dict]:
        resolved = []
        
        open_trades = self.db.get_open_trades()
        
        for trade in open_trades:
            market = trade.get('market_slug')
            
            if self._is_market_resolved(market):
                resolved.append({
                    'trade_id': trade.get('trade_id'),
                    'market': market,
                    'outcome': trade.get('outcome'),
                    'should_redeem': True
                })
        
        return resolved

    def _is_market_resolved(self, market_slug: str) -> bool:
        return False

    def auto_redeem_winnings(self, wallet_address: str) -> Dict:
        from ..api.bullpen import BullpenCLI
        
        results = {
            'redeemed': [],
            'failed': [],
            'skipped': []
        }
        
        resolved_markets = self.detect_resolved_markets()
        
        try:
            bullpen = BullpenCLI(self.config.get('bullpen_path', '/usr/local/bin/bullpen'))
            
            for market in resolved_markets:
                try:
                    result = bullpen.redeem_winnings(market['market'], wallet_address)
                    
                    if result.get('success'):
                        results['redeemed'].append(market)
                        self.logger.info(f'Redeemed: {market["market"]}', 'reconciler')
                    else:
                        results['failed'].append(market)
                        
                except Exception as e:
                    results['failed'].append(market)
                    self.logger.error(f'Redeem failed: {e}', 'reconciler')
                    
        except Exception as e:
            self.logger.error(f'Bullpen not available: {e}', 'reconciler')
            
        return results

    def close_stale_positions(self, max_age_days: int = 7):
        open_trades = self.db.get_open_trades()
        
        now = datetime.now()
        
        for trade in open_trades:
            opened_at = trade.get('copied_at')
            if opened_at:
                try:
                    opened = datetime.fromisoformat(opened_at)
                    age_days = (now - opened).days
                    
                    if age_days > max_age_days:
                        self.db.update_copied_trade_status(
                            trade.get('trade_id'),
                            'closed',
                            pnl=0,
                            close_reason='stale_position'
                        )
                        self.logger.info(f'Closed stale position: {trade.get("trade_id")[:8]}', 'reconciler')
                except:
                    pass