# Standard library imports
import time
from typing import List, Dict, Any, Optional

# Third-party imports
import pandas as pd
import numpy as np

# Local application imports
import data_connector as dc
import reporting as re
import config as c
from grid_trade import GridTrader



def save_results(results: list, is_optimization: bool = False) -> None:
    """Save results to CSV file"""
    results_df = pd.DataFrame(results)
    
    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename_prefix = 'optimization' if is_optimization else 'backtest'
    filename = f'{c.output_dir}/backtest_results_{timestamp}.csv'
    
    # Debug: Print the actual column names in the DataFrame
    print("\nActual columns in DataFrame:", results_df.columns.tolist())
    
    # Save results
    results_df.to_csv(filename, index=False)
    print(f"\nResults saved to {filename}")
    
    # If optimization, display top results
    if is_optimization:
        try:
            # Sort using the exact column name from the DataFrame
            sorted_df = results_df.sort_values(by='net_profit', ascending=False)
            print("\nTop 10 Parameter Combinations:")
            print(sorted_df.head(10))
        except KeyError as e:
            print(f"\nError sorting results: Column not found. Available columns are: {results_df.columns.tolist()}")
            # Try alternative column name if 'net_profit' is not found
            try:
                sorted_df = results_df.sort_values(by='net profit', ascending=False)
                print("\nTop 10 Parameter Combinations:")
                print(sorted_df.head(10))
            except KeyError:
                print("Could not sort results by either 'net_profit' or 'net profit'")

def run_optimization(data: pd.DataFrame, trader: GridTrader) -> list:
    """Run parameter optimization with ranges from config"""
    results = []
    
    try:
        total_combinations = (len(c.optimization_params['stop_loss_amounts']) * 
                            len(c.optimization_params['stop_loss_levels']) * 
                            len(c.optimization_params['steps']))
    except KeyError as e:
        print(f"Error accessing optimization parameters: {e}")
        print("Please check your config.py file contains all required parameters")
        return []

    current_combination = 0
    
    for stop_loss_amount in c.optimization_params['stop_loss_amounts']:
        for stop_loss_level in c.optimization_params['stop_loss_levels']:
            for step in c.optimization_params['steps']:
                current_combination += 1
                print(f"\rProgress: {current_combination}/{total_combinations} "
                      f"({(current_combination/total_combinations*100):.1f}%)", end="")
                
                try:
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
                        'gross_profit': gross_profit,
                        'net_profit': net_profit,
                        'max_drawdown': max_drawdown,
                        'total_trade': total_trade,
                        'stop_loss_triggered': stop_loss_triggered
                    })
                except Exception as e:
                    print(f"\nError in optimization iteration: {e}")
                    continue
    
    print("\nOptimization complete!")
    return results

def main():
    start_time = time.time()
    
    try:
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
        
        # Ensure run_mode exists in config
        if not hasattr(c, 'run_mode'):
            print("run_mode not found in config, defaulting to 'single'")
            c.run_mode = 'single'
        
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

    except Exception as e:
        print(f"An error occurred in main: {e}")
        raise

if __name__ == "__main__":
    main()