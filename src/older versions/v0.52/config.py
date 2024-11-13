# config.py

import numpy as np
from enum import Enum
import os
from typing import Dict, Any

class DataSourceType(Enum):
    YAHOO_FINANCE = 'yahoo_finance'
    CSV = 'csv'
    HISTDATA = 'histdata'

# Account parameters
account_balance = 100000  # Starting balance in USD
risk_per_trade = 0.01    # 1% risk per trade, change to big number to disable

# Trading parameters
commission_rate = 0.00002
contract_size = 100000
fx_symbol = 'EURUSD'

# Per-trade risk management
trailing_stop = False     # send to False to disable trailing stop
trailing_stop_distance = 0.0010  # 10 pips
max_position_holding_days = 5    # Maximum days to hold a position

# Trading hours (24-hour format)
trading_hours = {
    'start': '00:00',
    'end': '23:59'
}

# Default volatility parameters
volatility_params = {
    'resample_period': '30min',     # Default resampling period
    'lookback': 20,                 # Default lookback periods
    'base_atr_multiplier': 1.0,     # Default multiplier for ATR-based step size
    'min_step': 0.02,            # Minimum step size (5 pip for FX)
    'max_step': 0.04               # Maximum step size (100 pips for FX)
}

# Data source setting
data_source = DataSourceType.CSV

# Run mode
run_mode = 'optimization'  # 'single' or 'optimization'
'''
# Single run parameters
single_run_params = {
    'stop_loss_amount': 10000,
    'stop_loss_level': 4,
    'step': volatility_params['min_step'],
    'volatility_factor': volatility_params['base_atr_multiplier'],
    'volatility_lookback': volatility_params['lookback'],
    'resample_period': volatility_params['resample_period']
}
'''

single_run_params = {
    'stop_loss_amount': 10000,
    'stop_loss_level': 4,
    'step': volatility_params['min_step'],
    'volatility_factor': volatility_params['base_atr_multiplier'],
    'volatility_lookback': volatility_params['lookback'],
    'resample_period': volatility_params['resample_period']
}

# Optimization parameter ranges
optimization_params = {
    'stop_loss_amounts': [3000, 5000, 10000, 20000],
    'stop_loss_levels': range(2,10),
    'volatility_factors': [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0],
    'volatility_lookbacks': [5, 10, 30],
    'resample_periods': ['15min', '30min', '1h', '4h', '1d']
}

# Parameter grid for optimization
param_grid = {
    'stop_loss_amount': optimization_params['stop_loss_amounts'],
    'stop_loss_level': optimization_params['stop_loss_levels'],
    'step': [volatility_params['min_step']],
    'volatility_factor': optimization_params['volatility_factors'],
    'volatility_lookback': optimization_params['volatility_lookbacks'],
    'resample_period': optimization_params['resample_periods']
}

# Cost parameters
spread_typical = {
    'EURUSD': 0.00001  # 0.1 pip typical spread
}

interest_rates = {
    'USD': 0.0525,  # 5.25% Fed rate
    'EUR': 0.0400,  # 4.00% ECB rate
}

# Data parameters
data_params = {
    'histdata': {
        'file_path': '/Users/chris/dev/data-source/histdata/eurusd/EURUSD_2005-2015.csv',
    },
    'csv': {
        'file_path': '/Users/chris/dev/data-source/kaggle/eurusd_minute_tiny.csv',
    },
    'yahoo_finance': {
        'period': '5d',
        'interval': '1m'
    }
}

# Output directory
output_dir = os.path.expanduser('~/dev/output')

# Logging parameters
enable_logging = False

# Configuration functions - MOVED BEFORE __main__
def get_trade_params() -> Dict[str, Any]:
    """Get trading parameters"""
    return {
        'account_balance': account_balance,
        'risk_per_trade': risk_per_trade,
        'trailing_stop': trailing_stop,
        'trailing_stop_distance': trailing_stop_distance,
        'max_position_holding_days': max_position_holding_days,
        'trading_hours': trading_hours,
        'volatility_lookback': volatility_params['lookback'],
        'grid_volatility_factor': volatility_params['base_atr_multiplier']
    }

def get_cost_params() -> Dict[str, Any]:
    """Get cost-related parameters"""
    return {
        'spread_typical': spread_typical,
        'interest_rates': interest_rates,
        'commission_rate': commission_rate
    }

def get_data_params() -> Dict[str, Any]:
    """Get data parameters based on configured data source"""
    source_key = data_source.value
    params = data_params.get(source_key, {}).copy()
    params['source_type'] = data_source
    params['symbol'] = fx_symbol
    
    if data_source == DataSourceType.YAHOO_FINANCE:
        params['symbol'] = f"{fx_symbol}=X"
    
    if data_source in [DataSourceType.CSV, DataSourceType.HISTDATA]:
        if 'file_path' in params:
            file_path = os.path.expanduser(params['file_path'])
            if not os.path.exists(file_path):
                print(f"Warning: Data file not found: {file_path}")
            params['file_path'] = file_path
            
    return params

def verify_configuration() -> bool:
    """Verify configuration settings"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        params = get_data_params()
        if not params:
            print("Error: Invalid data source configuration")
            return False
            
        if account_balance <= 0:
            print("Error: Invalid account balance")
            return False
            
        if risk_per_trade <= 0 or risk_per_trade > 0.1:
            print("Error: Invalid risk per trade percentage")
            return False
            
        if trailing_stop_distance <= 0:
            print("Error: Invalid trailing stop distance")
            return False
            
        return True
        
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

# Main verification block
if __name__ == "__main__":
    print("\nTrading Configuration:")
    print(f"Account Balance: ${account_balance:,}")
    print(f"Risk per Trade: {risk_per_trade*100}%")
    print(f"Run Mode: {run_mode}")
    print(f"Symbol: {fx_symbol}")
    print(f"Commission Rate: {commission_rate}")
    print(f"Contract Size: {contract_size}")
    
    print("\nRisk Management:")
    print(f"Trailing Stop: {trailing_stop}")
    print(f"Trailing Stop Distance: {trailing_stop_distance}")
    print(f"Max Position Holding Days: {max_position_holding_days}")
    
    print("\nVolatility Parameters:")
    print(f"Lookback: {volatility_params['lookback']}")
    print(f"ATR Multiplier: {volatility_params['base_atr_multiplier']}")
    print(f"Resample Period: {volatility_params['resample_period']}")
    
    print("\nData Source Configuration:")
    print(f"Data Source: {data_source.value}")
    params = get_data_params()
    print(f"Data Parameters: {params}")
    
    print("\nOptimization Parameters:")
    print(f"Stop Loss Amounts: {list(optimization_params['stop_loss_amounts'])}")
    print(f"Stop Loss Levels: {list(optimization_params['stop_loss_levels'])}")
    print(f"Volatility Factors: {list(optimization_params['volatility_factors'])}")
    
    if verify_configuration():
        print("\nConfiguration verified successfully")
    else:
        print("\nConfiguration verification failed")