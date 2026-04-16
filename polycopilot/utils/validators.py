import re
from typing import Optional, Tuple


def validate_wallet_address(address: str) -> Tuple[bool, Optional[str]]:
    if not address:
        return False, "Wallet address cannot be empty"
    
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False, "Invalid wallet address format (expected: 0x... followed by 40 hex chars)"
    
    return True, None


def validate_positive_float(value: float, min_value: float = 0.01) -> Tuple[bool, Optional[str]]:
    try:
        val = float(value)
        if val <= 0:
            return False, f"Value must be positive"
        if val < min_value:
            return False, f"Value must be at least {min_value}"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid number format"


def validate_positive_int(value: int, min_value: int = 1) -> Tuple[bool, Optional[str]]:
    try:
        val = int(value)
        if val <= 0:
            return False, f"Value must be positive"
        if val < min_value:
            return False, f"Value must be at least {min_value}"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid integer format"


def validate_poll_interval(seconds: int) -> Tuple[bool, Optional[str]]:
    try:
        val = int(seconds)
        if val < 5:
            return False, "Poll interval must be at least 5 seconds"
        if val > 3600:
            return False, "Poll interval cannot exceed 1 hour"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid poll interval"


def validate_copy_mode(mode: str) -> Tuple[bool, Optional[str]]:
    valid_modes = ['fixed', 'proportional', 'weighted']
    if mode not in valid_modes:
        return False, f"Mode must be one of: {', '.join(valid_modes)}"
    return True, None


def validate_sell_mode(mode: str) -> Tuple[bool, Optional[str]]:
    valid_modes = ['all', 'proportional', 'fixed', 'ignore']
    if mode not in valid_modes:
        return False, f"Mode must be one of: {', '.join(valid_modes)}"
    return True, None


def validate_file_path(path: str) -> Tuple[bool, Optional[str]]:
    if not path:
        return False, "Path cannot be empty"
    
    import os
    if not os.path.exists(path):
        return False, "Path does not exist"
    
    if not os.path.isfile(path):
        return False, "Path is not a file"
    
    return True, None


def validate_percentage(value: float, max_val: float = 100.0) -> Tuple[bool, Optional[str]]:
    try:
        val = float(value)
        if val < 0:
            return False, "Percentage cannot be negative"
        if val > max_val:
            return False, f"Percentage cannot exceed {max_val}%"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid percentage format"


def validate_trader_filters(filters: dict) -> Tuple[bool, Optional[str]]:
    required_keys = ['min_volume', 'min_pnl', 'min_trades', 'max_inactivity_days']
    
    for key in required_keys:
        if key not in filters:
            return False, f"Missing filter key: {key}"
    
    if filters['min_volume'] < 0:
        return False, "min_volume cannot be negative"
    
    if filters['min_pnl'] < 0:
        return False, "min_pnl cannot be negative"
    
    if filters['min_trades'] < 0:
        return False, "min_trades cannot be negative"
    
    if filters['max_inactivity_days'] < 1:
        return False, "max_inactivity_days must be at least 1"
    
    return True, None


def sanitize_log_message(message: str, max_length: int = 1000) -> str:
    if not message:
        return ""
    
    message = message[:max_length]
    
    dangerous_patterns = ['<script>', 'javascript:', 'onerror=', 'onclick=']
    for pattern in dangerous_patterns:
        message = message.replace(pattern, '')
    
    return message.strip()