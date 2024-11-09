# Trading parameters
commission_rate = 0.00002
contract_size = 100000
fx_symbol = 'EURUSD=X'

# Single run parameters
single_run_params = {
    'stop_loss_amount': 10000,
    'stop_loss_level': 4,
    'step': 0.0005
}

# Optimization parameters
optimization_params = {
    'stop_loss_amounts': range(5000, 20001, 5000),  # 5000 to 20000 in steps of 5000
    'stop_loss_levels': range(3, 8),                # 3 to 7
    'steps': [0.0003, 0.0005, 0.0007, 0.0010]      # specific step sizes to test
}

# Data parameters
data_params = {
    'csv_path': '~/dev/data-source/kaggle/eurusd_minute.csv',
    'yf_period': '5d',
    'yf_interval': '1m'
}

# Output parameters
output_dir = '~/dev/output'

# Logging parameters
enable_logging = True