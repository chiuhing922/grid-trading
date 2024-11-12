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
max_position_holding_days = 5    # Maximum days to hold a position, default = 5, set to large number to disable

# Trading hours (24-hour format)
trading_hours = {
    'start': '00:00',  # Trading session start time
    'end': '23:59'     # Trading session end time
}

# Volatility parameters for dynamic grid sizing
volatility_lookback = 20        # Default value, Periods for volatility calculation  (ATR of period n)
grid_volatility_factor = 0    # Default Value, Adjust grid size based on volatility  (default = 0.5)  0 to turn off effect

# Data source setting
data_source = DataSourceType.CSV

# Run mode
run_mode =  'optimization'  # 'single' or 'optimization'

# Single run parameters
single_run_params = {
    'stop_loss_amount': 10000,  # Global stop loss amount
    'stop_loss_level': 4,       # Maximum positions in one direction
    'step': 0.0005,             # Base grid step size
    'lookback_period': 60  # Default to 1 hour
}

# Optimization parameters
optimization_params = {
    'stop_loss_amounts': [5000, 10000],
    'stop_loss_levels': [3, 4, 5],
    'steps': np.arange(0.0150, 0.0400, 0.0010),
    # Add new parameters to optimize, not yet used in the code
    #'trailing_stop_distances': [0.0008, 0.0010, 0.0012],
    #'risk_per_trade_values': [0.005, 0.01, 0.015],
    'volatility_factors': [50, 100, 150, 200, 250],
    'volatility_lookbacks': [14, 30, 60, 120, 240]  # In minutes
}

# Cost parameters
spread_typical = {
    'EURUSD': 0.00001  # 0.1 pip typical spread
    #'EURUSD': 0.00000  # to disable spread
}

interest_rates = {
    #'USD': 0.00,  # to disable interest rate
    #'EUR': 0.00,  # to disable interest rate
    'USD': 0.0525,  # 5.25% Fed rate
    'EUR': 0.0400,  # 4.00% ECB rate
}

# Data parameters for different sources
data_params = {
    # HistData configuration
    'histdata': {
        'file_path': '/Users/chris/dev/data-source/histdata/eurusd/EURUSD_2005-2015.csv',
    },
    
    # CSV configuration
    'csv': {
        'file_path': '/Users/chris/dev/data-source/kaggle/eurusd_minute.csv',
    },
    
    # Yahoo Finance configuration
    'yahoo_finance': {
        'period': '5d',
        'interval': '1m'
    }
}

# Output directory with home directory expansion
output_dir = os.path.expanduser('~/dev/output')

# Logging parameters
enable_logging = False

# Get configuration functions
def get_trade_params() -> Dict[str, Any]:
    """Get trading parameters"""
    return {
        'account_balance': account_balance,
        'risk_per_trade': risk_per_trade,
        'trailing_stop': trailing_stop,
        'trailing_stop_distance': trailing_stop_distance,
        'max_position_holding_days': max_position_holding_days,
        'trading_hours': trading_hours,
        'volatility_lookback': volatility_lookback,
        'grid_volatility_factor': grid_volatility_factor
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
        # Verify output directory exists or create it
        os.makedirs(output_dir, exist_ok=True)
        
        # Verify data parameters
        params = get_data_params()
        if not params:
            print("Error: Invalid data source configuration")
            return False
            
        # Verify trading parameters
        if account_balance <= 0:
            print("Error: Invalid account balance")
            return False
            
        if risk_per_trade <= 0 or risk_per_trade > 0.1:  # Max 10% risk per trade
            print("Error: Invalid risk per trade percentage")
            return False
            
        if trailing_stop_distance <= 0:
            print("Error: Invalid trailing stop distance")
            return False
            
        return True
        
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

# Print configuration for verification
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
    
    print("\nData Source Configuration:")
    print(f"Data Source: {data_source.value}")
    params = get_data_params()
    print(f"Data Parameters: {params}")
    
    print("\nOptimization Parameters:")
    print(f"Stop Loss Amounts: {list(optimization_params['stop_loss_amounts'])}")
    print(f"Stop Loss Levels: {list(optimization_params['stop_loss_levels'])}")
    print(f"Steps: {optimization_params['steps']}")
    
    # Verify configuration
    if verify_configuration():
        print("\nConfiguration verified successfully")
    else:
        print("\nConfiguration verification failed")