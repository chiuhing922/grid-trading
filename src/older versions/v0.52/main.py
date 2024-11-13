# Standard library imports
import time
from typing import List, Dict, Dict, Any

# Third-party imports
import pandas as pd
import matplotlib.pyplot as plt

# Local application imports
import config as c
import data_connector as dc
import reporting as re
from grid_trade import GridTrader
from grid_optimizer import run_optimized_grid_search


def save_results(results: list, is_optimization: bool = False) -> None:
    """Save results to CSV file"""
    if not results:
        print("No results to save")
        return
        
    results_df = pd.DataFrame(results)
    
    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename_prefix = 'optimization' if is_optimization else 'backtest'
    filename = f'{c.output_dir}/{filename_prefix}_results_{timestamp}.csv'
    
    # Save results
    results_df.to_csv(filename, index=False)
    print(f"\nResults saved to {filename}")
    

def run_optimization(data: pd.DataFrame, trader: GridTrader) -> list:
    """Run parameter optimization with improved scalability"""
    try:
        # Calculate total combinations from param_grid instead of optimization_params
        total_combinations = 1
        for values in c.param_grid.values():
            total_combinations *= len(values)
            
        print(f"\nTotal parameter combinations to evaluate: {total_combinations}")
        
        # Run optimization using param_grid from config
        results_df = run_optimized_grid_search(data, trader)
        
        # Convert results to list of dictionaries for compatibility
        results = results_df.to_dict('records')
        print("\nOptimization complete!")
        return results
        
    except Exception as e:
        print(f"\nError in optimization: {e}")
        import traceback
        traceback.print_exc()
        return []

def run_single_backtest(data: pd.DataFrame, trader: GridTrader) -> list:
    """Run a single backtest with parameters from config"""
    print("\nRunning single backtest with parameters:")
    print(f"Stop Loss Amount: ${c.single_run_params['stop_loss_amount']:,}")
    print(f"Stop Loss Level: {c.single_run_params['stop_loss_level']}")
    print(f"Base Step Size: {c.single_run_params['step']}")
    print(f"Volatility Factor: {c.single_run_params['volatility_factor']}")
    print(f"Volatility Lookback: {c.single_run_params['volatility_lookback']}")
    
    try:
        result = trader.grid_trade(
            data=data,
            symbol=c.fx_symbol,
            **c.single_run_params
        )
        
        # Unpack results
        gross_profit, net_profit, max_drawdown, total_trade, stop_loss_count = result
        
        # Create results list with single dictionary
        results = [{
            'stop_loss_amount': c.single_run_params['stop_loss_amount'],
            'stop_loss_level': c.single_run_params['stop_loss_level'],
            'step': c.single_run_params['step'],
            'volatility_factor': c.single_run_params['volatility_factor'],
            'volatility_lookback': c.single_run_params['volatility_lookback'],
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'max_drawdown': max_drawdown,
            'total_trade': total_trade,
            'stop_loss_count': stop_loss_count
        }]
        
        print("\nBacktest completed successfully")
        return results
        
    except Exception as e:
        print(f"Error in single backtest: {e}")
        raise

def plot_trading_results(df: pd.DataFrame, symbol: str) -> None:
    """Plot trading results"""
    
    plt.figure(figsize=(12, 6))
    
    # Plot profits over time using DateTime
    plt.plot(df['DateTime'], df['Profit'].cumsum(), label='Gross Profit')
    plt.plot(df['DateTime'], df['NetProfit'].cumsum(), label='Net Profit')
    
    plt.title(f'Trading Results for {symbol}')
    plt.xlabel('Date/Time')
    plt.ylabel('Profit')
    plt.legend()
    plt.grid(True)
    
    # Save plot
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    plt.savefig(f'{c.output_dir}/trading_results_{timestamp}.png')

def main():
    start_time = time.time()
    
    try:
        # Initialize trader
        trader = GridTrader()
        
        # Get data source parameters
        data_params = c.get_data_params()
        
        # Load data based on configured source
        try:
            data = None
            print(f"\nLoading data from {data_params['source_type'].value}")
            
            if data_params['source_type'] == c.DataSourceType.YAHOO_FINANCE:
                data = dc.fetch_YF_data(
                    symbol=data_params['symbol'],
                    period=data_params.get('period', '5d'),
                    interval=data_params.get('interval', '1m')
                )
            elif data_params['source_type'] == c.DataSourceType.HISTDATA:
                # Verify required parameters exist
                if 'file_path' not in data_params:
                    raise ValueError("file_path is required for HistData source")
                if 'symbol' not in data_params:
                    raise ValueError("symbol is required for HistData source")
                    
                data = dc.load_histdata(
                    file_path=data_params['file_path'],
                    symbol=data_params['symbol']
                )
            else:  # CSV
                if 'file_path' not in data_params:
                    raise ValueError("file_path is required for CSV source")
                data = dc.load_data_from_csv(data_params['file_path'])
            
            if data is not None:
                print(f"Data loaded successfully")
                print(f"Data shape: {data.shape}")
                print(f"Date range: {data['Datetime'].min()} to {data['Datetime'].max()}")
                
                # Add test line here 
                #data = data.head(100)  # Test with first 100 records only
                #print(f"Testing with reduced data shape: {data.shape}")


            else:
                raise ValueError("No data loaded")
                
        except Exception as e:
            print(f"Failed to load data: {e}")
            raise
        
      
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()