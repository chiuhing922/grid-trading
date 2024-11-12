import numpy as np

# Trading parameters
commission_rate = 0.00002
contract_size = 100000
fx_symbol = 'EURUSD=X'

# Run mode
run_mode = 'single'  # or 'single'

# Single run parameters
single_run_params = {
    'stop_loss_amount': 10000,
    'stop_loss_level': 4,
    'step': 0.0005
}

# Optimization parameters
optimization_params = {
    'stop_loss_amounts': range(5000, 21000, 2000),  # 5000 to 10000 in steps of 1000
    'stop_loss_levels': range(2, 8),                # 3 to 10
    #'steps': [0.0003, 0.0004, 0.0004, 0.0006, 0.0007, 0.008]      # specific step sizes to test
    'steps': np.arange(0.0002, 0.0016, 0.0001)      # 0.0002 to 0.0015 in step of 0.0001
}

# Data parameters
data_params = {
    'csv_path': '/Users/chris/dev/data-source/kaggle/eurusd_minute.csv',
    'yf_period': '1d',
    'yf_interval': '1m'
}

# Output parameters
output_dir = '~/dev/output'

# Logging parameters
enable_logging = False

# Print configuration for verification
if __name__ == "__main__":
    print("Optimization Parameters:")
    print(f"Stop Loss Amounts: {list(optimization_params['stop_loss_amounts'])}")
    print(f"Stop Loss Levels: {list(optimization_params['stop_loss_levels'])}")
    print(f"Steps: {list(optimization_params['steps'])}")