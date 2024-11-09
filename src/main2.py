import time
import data_connector as dc
import reporting2 as re
import pandas as pd
import numpy as np
import config as c
from grid_trade2 import GridTrader  # Import the new GridTrader class

def run_backtest(data: pd.DataFrame, commission_rate: float = 0.00002, contract_size: float = 100000):
    # Initialize an empty list to store results
    results = []
    symbol = 'EURUSD=X'
    
    # Initialize the GridTrader
    trader = GridTrader(commission_rate=commission_rate, contract_size=contract_size)
    
    # Single run example
    result = trader.grid_trade(
        data=data,
        symbol=symbol,
        stop_loss_amount=10000,
        stop_loss_level=4,
        step=0.0005
    )

    
    # Unpack results
    gross_profit, net_profit, max_drawdown, total_trade, stop_loss_triggered = result
    
    results.append({
        'stop_loss_amount': 10000,
        'stop_loss_level': 4,
        'step': 0.0005,
        'gross profit': gross_profit,
        'net profit': net_profit,
        'max_drawdown': max_drawdown,
        'total trade': total_trade,
        'stop loss triggered': stop_loss_triggered
    })
    
    return results

def run_parameter_optimization(data: pd.DataFrame, commission_rate: float = 0.00002, contract_size: float = 100000):
    results = []
    symbol = 'EURUSD=X'
    
    # Initialize the GridTrader
    trader = GridTrader(commission_rate=commission_rate, contract_size=contract_size)
    
    for stop_loss_amount in range(1000, 11000, 1000):
        for stop_loss_level in range(3, 11, 1):
            for step in np.arange(0.0005, 0.0105, 0.0005):
                result = trader.grid_trade(
                    data=data,
                    symbol=symbol,
                    stop_loss_amount=stop_loss_amount,
                    stop_loss_level=stop_loss_level,
                    step=step
                )
                
                gross_profit, net_profit, max_drawdown, total_trade, stop_loss_triggered = result
                
                results.append({
                    'stop_loss_amount': stop_loss_amount,
                    'stop_loss_level': stop_loss_level,
                    'step': step,
                    'gross profit': gross_profit,
                    'net profit': net_profit,
                    'max_drawdown': max_drawdown,
                    'total trade': total_trade,
                    'stop loss triggered': stop_loss_triggered
                })
    
    return results

def main():
    start_time = time.time()
    
    # Load data
    data = dc.load_data_from_csv('~/dev/data-source/kaggle/eurusd_minute.csv')
    
    # Initialize trader
    trader = GridTrader(commission_rate=c.commission_rate, contract_size=c.contract_size)
    
    # Run backtest
    result = trader.grid_trade(
        data=data,
        symbol='EURUSD=X',
        stop_loss_amount=10000,
        stop_loss_level=4,
        step=0.0005
    )
    
    # Unpack results
    gross_profit, net_profit, max_drawdown, total_trade, stop_loss_triggered = result
    
    results = [{
        'stop_loss_amount': 10000,
        'stop_loss_level': 4,
        'step': 0.0005,
        'gross profit': gross_profit,
        'net profit': net_profit,
        'max_drawdown': max_drawdown,
        'total trade': total_trade,
        'stop loss triggered': stop_loss_triggered
    }]
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    print(results_df)
    
    # Save results with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f'~/dev/output/backtest_results_{timestamp}.csv'
    results_df.to_csv(filename, index=False)
    print(f"Results saved to '{filename}'.")
    
    # Generate report with trader's state
    re.gen_report(trader.state, symbol='EURUSD=X')
    
    # Print execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Backtest execution time: {execution_time:.4f} seconds")

if __name__ == "__main__":
    main()