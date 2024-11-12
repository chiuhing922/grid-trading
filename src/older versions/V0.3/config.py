import numpy as np
from enum import Enum
import os
from typing import Dict, Any

class DataSourceType(Enum):
    YAHOO_FINANCE = 'yahoo_finance'
    CSV = 'csv'
    HISTDATA = 'histdata'

# Trading parameters
commission_rate = 0.00002
contract_size = 100000
fx_symbol = 'EURUSD'  # Base symbol without =X suffix

# Data source setting
data_source = DataSourceType.CSV # Set your desired data source

# Run mode
run_mode = 'single'  # 'single' or 'optimization'

# Single run parameters
single_run_params = {
    'stop_loss_amount': 10000,
    'stop_loss_level': 4,
    'step': 0.0005
}

# Optimization parameters
optimization_params = {
    'stop_loss_amounts': range(5000, 11000, 5000),
    'stop_loss_levels': range(2, 5),
    'steps': [0.0003, 0.0004, 0.0006]
}

# Data parameters for different sources
data_params = {
    # HistData configuration
    'histdata': {
        'file_path': '/Users/chris/dev/data-source/histdata/eurusd/EURUSD_2005-2015.csv',
    },
    
    # CSV configuration
    'csv': {
        'file_path': '/Users/chris/dev/data-source/kaggle/eurusd_minute-2005-2015.csv',
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

def get_data_params() -> Dict[str, Any]:
    """
    Get data parameters based on configured data source
    
    Returns:
        Dict containing source type, symbol, and source-specific parameters
    """
    source_key = data_source.value
    params = data_params.get(source_key, {}).copy()  # Make a copy to avoid modifying original
    params['source_type'] = data_source
    params['symbol'] = fx_symbol
    
    # Add =X suffix for Yahoo Finance
    if data_source == DataSourceType.YAHOO_FINANCE:
        params['symbol'] = f"{fx_symbol}=X"
    
    # Verify file paths exist for file-based sources
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
            
        return True
        
    except Exception as e:
        print(f"Configuration error: {e}")
        return False

# Print configuration for verification
if __name__ == "__main__":
    print("\nTrading Configuration:")
    print(f"Run Mode: {run_mode}")
    print(f"Symbol: {fx_symbol}")
    print(f"Commission Rate: {commission_rate}")
    print(f"Contract Size: {contract_size}")
    
    print("\nData Source Configuration:")
    print(f"Data Source: {data_source.value}")
    params = get_data_params()
    print(f"Data Parameters: {params}")
    
    print("\nOptimization Parameters:")
    print(f"Stop Loss Amounts: {list(optimization_params['stop_loss_amounts'])}")
    print(f"Stop Loss Levels: {list(optimization_params['stop_loss_levels'])}")
    print(f"Steps: {list(optimization_params['steps'])}")
    
    # Verify configuration
    if verify_configuration():
        print("\nConfiguration verified successfully")
    else:
        print("\nConfiguration verification failed")