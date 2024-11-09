import pandas as pd
import numpy as np 
import csv
import time
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

def dollar_formatter(x, pos):
    return f"${x:,.0f}"

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
    print(f"Final Accumulated Commission Fee: ${trader_state.total_commission:,.2f}")
    print(f"Final Accumulated Contract: {trader_state.accumulated_contract:,}")
    print(f"Gross Profit: ${trader_state.accumulated_profit:,.2f}")
    print(f"Final Profit: ${trader_state.accumulated_net_profit:,.2f}")
    print(f"Maximium Drawdown: ${trader_state.max_drawdown:,.2f}")
    
    # Calculate return to risk ratio with zero protection
    if max_risk != 0:
        risk_ratio = trader_state.accumulated_net_profit/max_risk
        print(f"Return to Risk Ratio (the higher the better): {risk_ratio:.3f}")
    else:
        print("Return to Risk Ratio: N/A (max risk is 0)")
    
    print(f"=============================== End REPORT ==========================================\n\n")
    
    # Only proceed with plotting if there's data
    if trader_state.profit_data:
        # Save profit_data to CSV
        filename = os.path.expanduser('~/dev/output/')
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'{filename}profit_data_{timestamp}.csv'

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['DateTime', 'AccumulatedNetProfit', 'AccumulatedProfit'])
            writer.writerows(trader_state.profit_data)
        print(f"Data exported to {filename}")
        
        # Convert list to DataFrame
        df = pd.DataFrame(trader_state.profit_data, columns=['DateTime', 'AccumulatedNetProfit', 'AccumulatedProfit'])
        # Convert 'DateTime' to datetime format for plotting
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        
        # Plotting the data
        plt.figure(figsize=(10, 6))
        plt.plot(df['DateTime'], df['AccumulatedNetProfit'], marker='o', linestyle='-', label='Accumulated Net Profit')
        plt.plot(df['DateTime'], df['AccumulatedProfit'], marker='x', linestyle='-', label='Accumulated Profit')
        plt.xlabel('Date/Date-Time')
        plt.ylabel('Accumulated Profits')
        plt.title('Simulated FX Trading Backtest Result')
        plt.xticks(rotation=45)  # Rotate x-axis labels for readability
        plt.grid(True)
        
        # Apply the dollar formatter to the y-axis
        plt.gca().yaxis.set_major_formatter(FuncFormatter(dollar_formatter))
        plt.legend()
        plt.tight_layout()  # Adjust layout to prevent clipping of labels
        plt.show()
    else:
        print("No profit data available for plotting")