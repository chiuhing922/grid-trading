import pandas as pd
import numpy as np 
import csv
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import config as c


# Define a formatter function for dollar values with thousands separator
def dollar_formatter(x, pos):
    return f"${x:,.0f}"

def gen_report():    
    c.max_risk = c.stop_loss_amount
    print(f"\n\n============================== BACKTEST REPORT ======================================")
    print(f"Currency Traded: {c.fx_symbol}")
    print(f"Contract size: ${c.contract_size:,}")
    print(f"Maximum Loss Allowed: ${c.stop_loss_amount:,}")  
    print(f"Step size: {c.step}")
    print(f"Stop loss level: {c.stop_loss_level}")
    print(f"Maximum risk: ${c.max_risk:,}")
    print(f"Total times of stop loss triggered: {c.stop_loss_count:,}\n")   
    print(f"Final Accumulated Commission Fee: ${c.total_commission:,.2f}")
    print(f"Final Accumulated Contract: {c.accumulated_contract:,}")
    print(f"Gross Profit: ${c.accumulated_profit:,.2f}")
    print(f"Final Profit: ${c.accumulated_net_profit:,.2f}")
    print(f"Maximium Drawdown: ${c.max_drawdown:,.2f}")
    print(f"Return to Risk Ratio (the higher the better): {c.accumulated_net_profit/c.max_risk:.3f}")
    print(f"=============================== End REPORT ==========================================\n\n")
    
   # Save profit_data to CSV
    
    with open('d:/dev/quant/output/profit_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['DateTime', 'AccumulatedNetProfit', 'AccumulatedProfit'])
        writer.writerows(c.profit_data)
    print("Data exported to profit_data.csv")
    
  
    # Convert list to DataFrame
    df = pd.DataFrame(c.profit_data, columns=['DateTime', 'AccumulatedNetProfit', 'AccumulatedProfit'])
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


# Example call for testing
#grid_trade('AUDNZD=X', contract_size=100000, stop_loss_level=10, step=0.0008)
