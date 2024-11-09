import time
import data_connector as dc
import reporting as re
import pandas as pd
import numpy as np
import config as c
from grid_trade import GridTrader

def run_single_backtest(data: pd.DataFrame, trader: GridTrader) -> list:
    """Run a single backtest with parameters from config"""
    result = trader.grid_trade(
        data=data,
        symbol=c.fx_symbol,
        **c.single_run_params  # Unpack parameters from config
    )
    
    # Unpack results
    gross_profit, net_profit, max_drawdown, total_trade, stop_loss_triggered = result
    
    # Create results dictionary
    results = [{
        'stop_loss_amount': c.single_run_params['stop_loss_amount'],
        'stop_loss_level': c.single_run_params['stop_loss_level'],
        'step': c.single_run_params['step'],
        'gross profit': gross_profit,
        'net profit': net_profit,
        'max_drawdown': max_drawdown,
        'total trade': total_trade,
        'stop loss triggered': stop_loss_triggered
    }]
    
    return results

def run_optimization(data: pd.DataFrame, trader: GridTrader) -> list:
    """Run parameter optimization with ranges from config"""
    results = []
    
    # Calculate total combinations for progress tracking
    total_combinations = (len(c.optimization_params['stop_loss_amounts']) * 
                        len(c.optimization_params['stop_loss_levels']) * 
                        len(c.optimization_params['steps']))
    current_combination = 0
    
    for stop_loss_amount in c.optimization_params['stop_loss_amounts']:
        for stop_loss_level in c.optimization_params['stop_loss_levels']:
            for step in c.optimization_params['steps']:
                current_combination += 1
                print(f"\rProgress: {current_combination}/{total_combinations} "
                      f"({(current_combination/total_combinations*100):.1f}%)", end="")
                
                result = trader.grid_trade(
                    data=data,
                    symbol=c.fx_symbol,
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
    
    print("\nOptimization complete!")
    return results

def save_results(results: list, is_optimization: bool = False) -> None:
    """Save results to CSV file"""
    results_df = pd.DataFrame(results)
    
    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename_prefix = 'optimization' if is_optimization else 'backtest'
    filename = f'{c.output_dir}/{filename_prefix}_results_{timestamp}.csv'
    
    # Save results
    results_df.to_csv(filename, index=False)
    print(f"\nResults saved to {filename}")
    
    # If optimization, display top results
    if is_optimization:
        print("\nTop 10 Parameter Combinations:")
        print(results_df.sort_values(by='net profit', ascending=False).head(10))

def main():
    start_time = time.time()
    
    # Initialize trader
    trader = GridTrader(
        commission_rate=c.commission_rate,
        contract_size=c.contract_size
    )
    
    # Load data from CSV or Yahoo Finance
    try:
        data = dc.load_data_from_csv(c.data_params['csv_path'])
    except Exception as e:
        print(f"Failed to load CSV data: {e}")
        print("Attempting to fetch data from Yahoo Finance...")
        data = dc.fetch_YF_data(
            c.fx_symbol,
            period=c.data_params['yf_period'],
            interval=c.data_params['yf_interval']
        )
    
    # Run selected mode based on config
    if c.run_mode == 'optimization':
        results = run_optimization(data, trader)
        save_results(results, is_optimization=True)
    else:
        results = run_single_backtest(data, trader)
        save_results(results, is_optimization=False)
        # Generate report for single run
        re.gen_report(trader.state, symbol=c.fx_symbol)
    
    # Print execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"\nExecution time: {execution_time:.4f} seconds")

if __name__ == "__main__":
    main()