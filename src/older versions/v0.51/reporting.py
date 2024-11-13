import pandas as pd
import numpy as np 
import csv
import time
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Local application imports
import config as c

def dollar_formatter(x, pos):
    return f"${x:+,.0f}" if x else "$0"  # Handle zero and add + sign for positive numbers

def gen_report(trader_state, symbol: str = 'EURUSD=X'):    
    """
    Generate trading report and visualizations based on trader state
    
    Args:
        trader_state: TradingState object containing all trading metrics
        symbol: Trading symbol/pair
    """
    max_risk = trader_state.stop_loss_amount
    
    print(f"\n\n============================== BACKTEST REPORT ======================================")
    print(f"Currency Traded: {symbol}")
    print(f"Contract size: ${trader_state.contract_size:,}")
    print(f"Maximum Loss Allowed: ${trader_state.stop_loss_amount:,}")  
    print(f"Step size: {trader_state.step}")
    print(f"Stop loss level: {trader_state.stop_loss_level}")
    print(f"Maximum risk: ${max_risk:,}")
    print(f"Total times of stop loss triggered: {trader_state.stop_loss_count:,}\n")   
    
    # Cost breakdown
    print(f"Trading Costs Breakdown:")
    print(f"Commission Fees: ${trader_state.total_commission:,.2f}")
    print(f"Spread Costs: ${trader_state.total_spread_cost:,.2f}")
    print(f"Rollover: ${trader_state.total_rollover:,.2f}")
    print(f"Total Costs: ${trader_state.total_costs:,.2f}\n")
    
    print(f"Final Accumulated Contract: {trader_state.accumulated_contract:,}")
    print(f"Gross Profit: ${trader_state.accumulated_profit:,.2f}")
    print(f"Final Net Profit: ${trader_state.accumulated_net_profit:,.2f}")
    print(f"Maximum Drawdown: ${trader_state.max_drawdown:,.2f}")
    
    # Calculate return to risk ratio with zero protection
    if max_risk != 0:
        risk_ratio = trader_state.accumulated_net_profit/max_risk
        print(f"Return to Risk Ratio (the higher the better): {risk_ratio:.3f}")
    else:
        print("Return to Risk Ratio: N/A (max risk is 0)")
    
    print(f"=============================== End REPORT ==========================================\n\n")
    
    # Only proceed with plotting if there's data
    if trader_state.profit_data:
        # Use config output directory
        filename = os.path.join(c.output_dir, f'profit_data_{time.strftime("%Y%m%d_%H%M%S")}.csv')
        
        # Create DataFrame with correct column names for all data
        df = pd.DataFrame(trader_state.profit_data, 
                         columns=['DateTime', 'Profit', 'NetProfit', 'EntryTime', 'ExitTime'])
        
        # Save all data to CSV
        df.to_csv(filename, index=False)
        print(f"Data exported to {filename}")
        
        # Create plot
        plt.figure(figsize=(12, 8))
        
        # Plot cumulative profits
        plt.subplot(2, 1, 1)
        plt.plot(df['DateTime'], df['NetProfit'].cumsum(), 
                marker='o', linestyle='-', label='Cumulative Net Profit')
        plt.plot(df['DateTime'], df['Profit'].cumsum(), 
                marker='x', linestyle='-', label='Cumulative Gross Profit')
        plt.xlabel('Date/Time')
        plt.ylabel('Cumulative Profit ($)')
        plt.title('Cumulative Trading Profits')
        plt.grid(True)
        plt.legend()
        
        # Plot trade durations
        plt.subplot(2, 1, 2)
        trade_durations = (pd.to_datetime(df['ExitTime']) - 
                          pd.to_datetime(df['EntryTime'])).dt.total_seconds() / 3600  # Convert to hours
        plt.hist(trade_durations, bins=50)
        plt.xlabel('Trade Duration (hours)')
        plt.ylabel('Number of Trades')
        plt.title('Distribution of Trade Durations')
        plt.grid(True)
        
        # Adjust layout and display
        plt.tight_layout()
        
        # Save plot
        plot_filename = os.path.join(c.output_dir, f'trading_results_{time.strftime("%Y%m%d_%H%M%S")}.png')
        plt.savefig(plot_filename)
        print(f"Plot saved to {plot_filename}")
        
        # Show plot
        plt.show()
        
        # Print trade duration statistics
        print("\nTrade Duration Statistics (hours):")
        print(f"Average: {trade_durations.mean():.2f}")
        print(f"Median: {trade_durations.median():.2f}")
        print(f"Min: {trade_durations.min():.2f}")
        print(f"Max: {trade_durations.max():.2f}")
    else:
        print("No profit data available for plotting")