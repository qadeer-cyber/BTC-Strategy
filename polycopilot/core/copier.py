import uuid
import subprocess
from typing import Dict, Optional, Any
from datetime import datetime
from decimal import Decimal


class Copier:
    def __init__(self, db, logger, config: Dict):
        self.db = db
        self.logger = logger
        self.config = config
        
        self.copy_mode = config.get('copy_mode', 'fixed')
        self.fixed_amount = config.get('fixed_amount', 10.0)
        self.proportional_percent = config.get('proportional_percent', 10)
        
        self.max_daily_loss = config.get('max_daily_loss', 100.0)
        self.max_exposure = config.get('max_exposure', 500.0)
        self.max_concurrent = config.get('max_concurrent', 5)
        
        self.sell_mode = config.get('sell_mode', 'all')
        self.is_dry_run = config.get('is_dry_run', True)
        self.is_paper = config.get('is_paper', True)
        
        self.bullpen_path = config.get('bullpen_path', '/usr/local/bin/bullpen')
        self.wallet_address = config.get('wallet_address', '')

    def set_mode(self, is_dry_run: bool, is_paper: bool):
        self.is_dry_run = is_dry_run
        self.is_paper = is_paper

    def update_config(self, config: Dict):
        for key in ['copy_mode', 'fixed_amount', 'proportional_percent', 
                    'max_daily_loss', 'max_exposure', 'max_concurrent',
                    'sell_mode', 'bullpen_path', 'wallet_address']:
            if key in config:
                setattr(self, key, config[key])

    def execute_copy(self, signal: Dict) -> Dict:
        trade_id = f"copy_{uuid.uuid4().hex[:16]}"
        
        self.logger.info(
            f"Attempting to copy: {signal.get('market_question')} - "
            f"{signal.get('side')} ${signal.get('amount')}",
            'copier'
        )
        
        if self.is_dry_run:
            self.logger.info('[DRY-RUN] Would execute trade', 'copier')
            return self._record_trade(trade_id, signal, status='open', note='dry-run')

        if not self._check_risk_limits():
            return {'success': False, 'reason': 'risk_limit_exceeded'}

        if self._check_duplicate(signal):
            self.logger.warning('Duplicate trade detected', 'copier')
            return {'success': False, 'reason': 'duplicate_trade'}

        if not self._check_balance(signal):
            self.logger.warning('Insufficient balance', 'copier')
            return self._record_trade(trade_id, signal, status='skipped', 
                                     error='insufficient_balance')

        copy_result = self._execute_trade(signal)
        
        if copy_result.get('success'):
            return self._record_trade(trade_id, signal, status='open',
                                     copied_price=copy_result.get('price'))
        else:
            return self._record_trade(trade_id, signal, status='failed',
                                     error=copy_result.get('error'))

    def _check_risk_limits(self) -> bool:
        today_pnl = self._get_today_pnl()
        if today_pnl <= -self.max_daily_loss:
            self.logger.warning(f'Daily loss limit reached: ${today_pnl:.2f}', 'copier')
            return False

        open_trades = self.db.get_open_trades()
        if len(open_trades) >= self.max_concurrent:
            self.logger.warning(f'Max concurrent positions reached: {len(open_trades)}', 'copier')
            return False

        total_exposure = sum(t.get('amount', 0) for t in open_trades)
        if total_exposure >= self.max_exposure:
            self.logger.warning(f'Max exposure reached: ${total_exposure:.2f}', 'copier')
            return False

        return True

    def _check_duplicate(self, signal: Dict) -> bool:
        signal_id = signal.get('signal_id')
        if signal_id and self.db.signal_exists(signal_id):
            return True
        
        recent_trades = self.db.get_all_copied_trades(limit=50)
        for trade in recent_trades:
            if (trade.get('trader_wallet') == signal.get('trader_wallet') and
                trade.get('market_slug') == signal.get('market_slug') and
                trade.get('side') == signal.get('side') and
                abs(trade.get('amount', 0) - signal.get('amount', 0)) < 0.01):
                
                time_diff = abs(
                    datetime.now() - datetime.fromisoformat(
                        trade.get('copied_at', datetime.now().isoformat())
                    ).replace(tzinfo=None)
                ).total_seconds()
                
                if time_diff < 300:
                    return True
        
        return False

    def _check_balance(self, signal: Dict) -> bool:
        required = self._calculate_copy_amount(signal)
        
        balance = self._get_wallet_balance()
        
        if balance is None:
            self.logger.warning('Could not fetch wallet balance, assuming sufficient', 'copier')
            return True
        
        return balance >= required

    def _calculate_copy_amount(self, signal: Dict) -> float:
        source_amount = float(signal.get('amount', 0))
        
        if self.copy_mode == 'fixed':
            return self.fixed_amount
        
        elif self.copy_mode == 'proportional':
            balance = self._get_wallet_balance() or 1000
            return (self.proportional_percent / 100) * balance
        
        elif self.copy_mode == 'weighted':
            return min(source_amount * 0.5, self.fixed_amount)
        
        return self.fixed_amount

    def _get_wallet_balance(self) -> Optional[float]:
        try:
            if self.bullpen_path and self.wallet_address:
                result = subprocess.run(
                    [self.bullpen_path, 'balance'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return float(result.stdout.strip())
        except:
            pass
        
        return None

    def _execute_trade(self, signal: Dict) -> Dict:
        copy_amount = self._calculate_copy_amount(signal)
        
        market_slug = signal.get('market_slug')
        outcome = signal.get('outcome')
        side = signal.get('side')
        
        if self.is_paper:
            self.logger.info(
                f'[PAPER] Would execute: {market_slug} {side} {outcome} ${copy_amount:.2f}',
                'copier'
            )
            return {'success': True, 'price': signal.get('price', 0.5)}
        
        if not self.bullpen_path or not self.wallet_address:
            return {'success': False, 'error': 'bullpen_not_configured'}
        
        try:
            cmd = [
                self.bullpen_path, 'trade',
                '--market', market_slug,
                '--outcome', outcome,
                '--side', side,
                '--amount', str(copy_amount),
                '--wallet', self.wallet_address
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info(f'Trade executed via Bullpen: {result.stdout}', 'copier')
                return {'success': True, 'output': result.stdout}
            else:
                self.logger.error(f'Bullpen error: {result.stderr}', 'copier')
                return {'success': False, 'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _record_trade(self, trade_id: str, signal: Dict, 
                      status: str, note: str = None,
                      copied_price: float = None,
                      error: str = None) -> Dict:
        
        trade_data = {
            'trade_id': trade_id,
            'signal_id': signal.get('signal_id'),
            'trader_wallet': signal.get('trader_wallet'),
            'market_slug': signal.get('market_slug'),
            'market_question': signal.get('market_question'),
            'outcome': signal.get('outcome'),
            'side': signal.get('side'),
            'amount': signal.get('amount'),
            'price': signal.get('price'),
            'copied_price': copied_price or signal.get('price'),
            'copied_at': datetime.now().isoformat(),
            'status': status,
            'source_trade_id': signal.get('signal_id')
        }
        
        self.db.add_copied_trade(trade_data)
        
        if error:
            self.db.update_copied_trade_status(trade_id, status, 
                                               error_message=error)
        
        self.logger.info(f'Trade recorded: {trade_id[:8]}... status={status}', 'copier')
        
        return {'success': status == 'open', 'trade_id': trade_id, 'status': status}

    def _get_today_pnl(self) -> float:
        today_trades = self.db.get_today_copied_trades()
        return sum(t.get('p&l', 0) for t in today_trades)

    def execute_sell(self, position: Dict) -> Dict:
        if self.sell_mode == 'ignore':
            return {'success': False, 'reason': 'sell_ignored'}

        if self.is_dry_run:
            self.logger.info(f'[DRY-RUN] Would sell position: {position.get("trade_id")}', 'copier')
            return {'success': True}

        market_slug = position.get('market_slug')
        outcome = position.get('outcome')
        
        if self.sell_mode == 'all':
            sell_amount = position.get('amount')
        elif self.sell_mode == 'proportional':
            sell_amount = position.get('amount') * 0.5
        elif self.sell_mode == 'fixed':
            sell_amount = self.fixed_amount
        else:
            return {'success': False, 'reason': 'unknown_sell_mode'}

        self.logger.info(f'Executing sell: {market_slug} {outcome} ${sell_amount:.2f}', 'copier')

        return {'success': True, 'amount': sell_amount}