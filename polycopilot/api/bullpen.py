import subprocess
import os
import json
from typing import Optional, Dict, List, Any
from datetime import datetime


class BullpenCLI:
    def __init__(self, cli_path: str = '/usr/local/bin/bullpen'):
        self.cli_path = cli_path
        self._verify_installation()

    def _verify_installation(self):
        if not os.path.exists(self.cli_path):
            raise Exception(f'Bullpen CLI not found at {self.cli_path}')

    def _run_command(self, args: List[str], timeout: int = 30) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                [self.cli_path] + args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'timeout',
                'stderr': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_balance(self, wallet_address: str) -> Optional[float]:
        result = self._run_command(['balance', '--wallet', wallet_address])
        if result['success']:
            try:
                return float(result['stdout'].strip())
            except ValueError:
                return None
        return None

    def execute_trade(self, market: str, outcome: str, side: str, 
                      amount: float, wallet: str) -> Dict:
        args = [
            'trade',
            '--market', market,
            '--outcome', outcome,
            '--side', side,
            '--amount', str(amount),
            '--wallet', wallet
        ]
        
        result = self._run_command(args)
        
        if result['success']:
            return {
                'success': True,
                'output': result['stdout']
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr', 'Unknown error')
            }

    def get_positions(self, wallet_address: str) -> List[Dict]:
        result = self._run_command(['positions', '--wallet', wallet_address])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                return []
        return []

    def get_orders(self, wallet_address: str) -> List[Dict]:
        result = self._run_command(['orders', '--wallet', wallet_address])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                return []
        return []

    def cancel_order(self, order_id: str, wallet_address: str) -> Dict:
        result = self._run_command([
            'cancel',
            '--order', order_id,
            '--wallet', wallet_address
        ])
        
        return {'success': result['success']}

    def redeem_winnings(self, market: str, wallet_address: str) -> Dict:
        result = self._run_command([
            'redeem',
            '--market', market,
            '--wallet', wallet_address
        ])
        
        if result['success']:
            return {
                'success': True,
                'output': result['stdout']
            }
        else:
            return {
                'success': False,
                'error': result.get('stderr')
            }

    def get_wallet_info(self, wallet_address: str) -> Optional[Dict]:
        result = self._run_command(['info', '--wallet', wallet_address])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                return None
        return None

    def is_available(self) -> bool:
        return os.path.exists(self.cli_path)

    def get_version(self) -> Optional[str]:
        result = self._run_command(['--version'], timeout=5)
        if result['success']:
            return result['stdout'].strip()
        return None