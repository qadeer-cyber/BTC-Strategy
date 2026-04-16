from typing import Optional, Dict, Any
from datetime import datetime


class ConfigManager:
    DEFAULT_SETTINGS = {
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

    def __init__(self, db):
        self.db = db
        self._load_settings()

    def _load_settings(self):
        self._settings = {}
        for key, default in self.DEFAULT_SETTINGS.items():
            value = self.db.get_setting(key)
            self._settings[key] = value if value is not None else default

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self.db.set_setting(key, value)

    def get_all(self) -> Dict[str, Any]:
        return self._settings.copy()

    def update(self, config: Dict):
        for key, value in config.items():
            if key in self.DEFAULT_SETTINGS:
                self.set(key, value)

    def reset(self):
        for key, default in self.DEFAULT_SETTINGS.items():
            self.set(key, default)


class Config:
    def __init__(self, db):
        self.manager = ConfigManager(db)

    @property
    def poll_interval(self) -> int:
        return self.manager.get('poll_interval')

    @poll_interval.setter
    def poll_interval(self, value: int):
        self.manager.set('poll_interval', value)

    @property
    def is_dry_run(self) -> bool:
        return self.manager.get('is_dry_run')

    @is_dry_run.setter
    def is_dry_run(self, value: bool):
        self.manager.set('is_dry_run', value)

    @property
    def is_paper(self) -> bool:
        return self.manager.get('is_paper')

    @is_paper.setter
    def is_paper(self, value: bool):
        self.manager.set('is_paper', value)

    @property
    def copy_mode(self) -> str:
        return self.manager.get('copy_mode')

    @copy_mode.setter
    def copy_mode(self, value: str):
        self.manager.set('copy_mode', value)

    @property
    def fixed_amount(self) -> float:
        return self.manager.get('fixed_amount')

    @fixed_amount.setter
    def fixed_amount(self, value: float):
        self.manager.set('fixed_amount', value)

    @property
    def max_daily_loss(self) -> float:
        return self.manager.get('max_daily_loss')

    @max_daily_loss.setter
    def max_daily_loss(self, value: float):
        self.manager.set('max_daily_loss', value)

    @property
    def max_exposure(self) -> float:
        return self.manager.get('max_exposure')

    @max_exposure.setter
    def max_exposure(self, value: float):
        self.manager.set('max_exposure', value)

    @property
    def max_concurrent(self) -> int:
        return self.manager.get('max_concurrent')

    @max_concurrent.setter
    def max_concurrent(self, value: int):
        self.manager.set('max_concurrent', value)

    @property
    def sell_mode(self) -> str:
        return self.manager.get('sell_mode')

    @sell_mode.setter
    def sell_mode(self, value: str):
        self.manager.set('sell_mode', value)

    @property
    def trader_filters(self) -> Dict:
        return self.manager.get('trader_filters')

    @trader_filters.setter
    def trader_filters(self, value: Dict):
        self.manager.set('trader_filters', value)

    @property
    def bullpen_path(self) -> str:
        return self.manager.get('bullpen_path')

    @bullpen_path.setter
    def bullpen_path(self, value: str):
        self.manager.set('bullpen_path', value)

    @property
    def wallet_address(self) -> str:
        return self.manager.get('wallet_address')

    @wallet_address.setter
    def wallet_address(self, value: str):
        self.manager.set('wallet_address', value)

    def to_dict(self) -> Dict:
        return self.manager.get_all()

    def update_from_dict(self, config: Dict):
        self.manager.update(config)