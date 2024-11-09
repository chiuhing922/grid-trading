import yfinance as yf
import pandas as pd
import numpy as np 
import csv
import matplotlib.pyplot as plt
     
# define global variable     
#define global variable

contract_size = 100000
stop_loss_amount = 10000
stop_loss_level=4
step=0.0005
     
commission_rate = 0.2 * 0.0001   # https://www.interactivebrokers.com.au/en/pricing/commissions-spot-currencies.php
total_commission = 0 
max_drawdown = 0
accumulated_profit = 0
accumulated_net_profit = 0
accumulated_contract = 0
position = 0

win_loss_record = []
win_loss_score_n = 8   # the last n win-loss record to calculate the win_loss_score  
record_no = 0  
profit_data = []

def record_max_drawdown():
    global accumulated_net_profit
    global max_drawdown
    if accumulated_net_profit<0 and accumulated_net_profit<max_drawdown:
        return accumulated_net_profit
    else:
        return max_drawdown
    
def get_win_loss_score (n):
    score=0
    length = len(win_loss_record)
    if length<n:
        n = length  
    for i in range(length-n, length):
        score += win_loss_record[i]
    return score  
    
def close_all_long_position(data, long_stack, current_price):    
    global commission_rate
    global contract_size
    global total_commission
    global accumulated_contract
    global accumulated_profit
    global accumulated_net_profit
    global position
    global max_drawdown
    commission = max(commission_rate * contract_size * current_price, 2)
    while long_stack:
        entry_price = long_stack.pop()
        profit = contract_size * (current_price - entry_price)
        accumulated_profit += profit
        accumulated_net_profit += profit - commission
        max_drawdown = record_max_drawdown()
        total_commission += commission
        accumulated_contract += 1
        position -=1
        print(f"Record No: {record_no} Close Long Position: {position+1} of entry price {entry_price} at price {current_price}")
        print(f"Accumulated Net Profit: {accumulated_net_profit}")
        update_profit_data(data)
    
def close_all_short_position(data, short_stack, current_price):
    global commission_rate
    global contract_size
    global total_commission
    global accumulated_contract
    global accumulated_profit
    global accumulated_net_profit
    global position
    global max_drawdown
    commission = max(commission_rate * contract_size * current_price, 2)
    while short_stack:
        entry_price = short_stack.pop()
        profit = contract_size * (entry_price - current_price)
        accumulated_profit += profit
        accumulated_net_profit += profit - commission
        max_drawdown = record_max_drawdown()
        total_commission += commission
        accumulated_contract += 1
        position +=1
        print(f"Record No: {record_no} Close Short Position: {position-1} of entry price {entry_price} at price {current_price}")
        print(f"Accumulated Net Profit: {accumulated_net_profit}")
        update_profit_data(data)
        
def close_all_position(data, long_stack, short_stack, current_price):        
    # end of all backtest data, clear all remaining position
    global commission_rate
    global contract_size
    global total_commission
    global accumulated_contract
    global accumulated_profit
    global accumulated_net_profit
    global position
    global max_drawdown
    commission = max(commission_rate * contract_size * current_price, 2)
    
    if position<0:
        while short_stack:
            entry_price = short_stack.pop()
            profit = contract_size * (entry_price - current_price)
            accumulated_profit += profit
            accumulated_net_profit += profit - commission
            max_drawdown = record_max_drawdown()
            total_commission += commission
            accumulated_contract += 1
            position +=1
            print(f"Record No: {record_no} Close Short Position: {position-1} of entry price {entry_price} at price {current_price}")
            print(f"Accumulated Net Profit: {accumulated_net_profit}")
            #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
            #profit_data.append((data.index[record_no-1], accumulated_net_profit))
            update_profit_data(data)
        print(f"End of data: Closed all remaining short positions. Accumulated Net Profit: {accumulated_net_profit}")
    elif position>0:
        # close all outstanding contract at the end
        while long_stack:
            entry_price = long_stack.pop()
            profit = contract_size * (current_price - entry_price)
            accumulated_profit += profit
            accumulated_net_profit += profit - commission
            max_drawdown = record_max_drawdown()
            total_commission += commission
            accumulated_contract += 1
            position -=1
            print(f"Record No: {record_no} Close Long Position: {position+1} of entry price {entry_price} at price {current_price}")
            print(f"Accumulated Net Profit: {accumulated_net_profit}")
            #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
            #profit_data.append((data.index[record_no-1], accumulated_net_profit))
            update_profit_data(data)
        print(f"End of data: Closed all remaining long positions. Accumulated Net Profit: {accumulated_net_profit}")
        
        
def update_profit_data(data):
    global record_no
    global accumulated_net_profit
    global profit_data
    profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit, accumulated_profit))
    print(f"Profit data of record no {record_no} of value of {accumulated_net_profit} updated!")
    
    
#def grid_trade(data, symbol, contract_size, stop_loss_amount, stop_loss_level, step):
def grid_trade(data, symbol):
# Define global variables

    global contract_size
    global stop_loss_amount
    global stop_loss_level
    global step
    
    global commission_rate
    global total_commission
    global max_drawdown
    global accumulated_profit
    global accumulated_net_profit
    global accumulated_contract
    global position
    
    global win_loss_record
    global win_loss_score_n
    global record_no
    global profit_data
   
    
# Define local variables
    
    current_price = float(data['Close'].values[0])
    reference_price = current_price
    next_long_price = reference_price - step
    next_short_price = reference_price + step
    long_stack = []
    short_stack = []
    stop_loss_count=0
    profit_data = []

# Simulate trading logic with historical data for backtesting
    for current_price in data['Close'].values:
        commission = max(commission_rate * contract_size * current_price, 2)
        record_no += 1
        current_price = float(current_price)
        
    # Close long positions: Don't buy any more if stop loss condition is triggered
        if (position >= stop_loss_level and current_price <= next_long_price):
            close_all_long_position(data, long_stack, current_price)
            print(f"Record No: {record_no} Closed all long positions at price {current_price}. Accumulated Net Profit: {accumulated_net_profit}")
            position = 0
            stop_loss_count +=1
            if accumulated_net_profit < (-1 * stop_loss_amount):
                break        #Stop loss
        
    # Close short positions: Don't Short any more if stop loss condition is triggered
        elif (position <= (-1 * stop_loss_level) and current_price >= next_short_price):
            close_all_short_position(data, short_stack, current_price)
            print(f"Record No: {record_no} Closed all short positions at price {current_price}. Accumulated Net Profit: {accumulated_net_profit}")
            position = 0
            stop_loss_count +=1
            if accumulated_net_profit < (-1 * stop_loss_amount):
                break        #Stop loss

    # Normal Long logic
        if current_price <= next_long_price:
            if position >= 0:
                position += 1
                long_stack.append(current_price)
                print(f"Record No: {record_no} Submitted long contract. Position: {position} at price {current_price}")
            else:   # closing existing short contract
                position += 1
                entry_price = short_stack.pop()
                print(f"Record No: {record_no} Close Short Position: {position-1} of entry price {entry_price} at price {current_price}")
                profit = (entry_price - current_price) * contract_size
                commission = max(commission_rate * contract_size * current_price, 2)
                accumulated_profit += profit
                accumulated_net_profit += profit - commission
                max_drawdown = record_max_drawdown()
                total_commission += commission
                accumulated_contract += 1
                print(f"Accumulated Net Profit: {accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                #profit_data.append((data.index[record_no-1], accumulated_net_profit))
                update_profit_data(data)
            next_long_price -= step
            next_short_price -= step

    # Normal Short logic
        elif current_price >= next_short_price:
            if position <= 0:
                position -= 1
                short_stack.append(current_price)
                print(f"Record No: {record_no} Submitted short contract. Position: {position} at price {current_price}")
            else:
                position -= 1
                entry_price = long_stack.pop()
                print(f"Record No: {record_no} Close Long Position: {position+1} of entry price {entry_price} at price {current_price}")
                profit = (current_price - entry_price) * contract_size
                accumulated_profit += profit
                accumulated_net_profit += profit - commission
                total_commission += commission
                accumulated_contract += 1
                print(f"Accumulated Net Profit: {accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                #profit_data.append((data.index[record_no-1], accumulated_net_profit))
                update_profit_data(data)
            next_short_price += step
            next_long_price += step

'''
#    max_risk = contract_size * step * stop_loss_level * (stop_loss_level + 1) / 2
    max_risk = stop_loss_amount

    print(f"\n\n============================== BACKTEST REPORT ======================================")
    print(f"Currency Traded: {symbol}")
    print(f"Contract size: ${contract_size:,}")
    print(f"Maximum Loss Allowed: ${stop_loss_amount:,}")  
    print(f"Step size: {step}")
    print(f"Stop loss level: {stop_loss_level}")
    print(f"Maximum risk: ${max_risk:,}")
    print(f"Total times of stop loss triggered: {stop_loss_count:,}\n")   
    print(f"Final Accumulated Commission Fee: ${total_commission:,.2f}")
    print(f"Final Accumulated Contract: {accumulated_contract:,}")
    print(f"Gross Profit: ${accumulated_profit:,.2f}")
    print(f"Final Profit: ${accumulated_net_profit:,.2f}")
    print(f"Maximium Drawdown: ${max_drawdown:,.2f}")
    print(f"Return to Risk Ratio (the higher the better): {accumulated_net_profit/max_risk:.3f}")
    print(f"=============================== End REPORT ==========================================\n\n")
    
   # Save profit_data to CSV
    
    with open('d:/dev/quant/output/profit_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['DateTime', 'AccumulatedNetProfit', 'AccumulatedProfit'])
        writer.writerows(profit_data)
    print("Data exported to profit_data.csv")
    
  
    # Convert list to DataFrame
    df = pd.DataFrame(profit_data, columns=['DateTime', 'AccumulatedNetProfit', 'AccumulatedProfit'])
    # Convert 'DateTime' to datetime format for plotting
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    # Plotting the data
    plt.figure(figsize=(10, 6))
    plt.plot(df['DateTime'], df['AccumulatedNetProfit'], marker='o', linestyle='-', label='Accumulated Net Profit')
    plt.plot(df['DateTime'], df['AccumulatedProfit'], marker='x', linestyle='-', label='Accumulated Profit')
    plt.xlabel('DateTime')
    plt.ylabel('Accumulated Net Profit')
    plt.title('Accumulated Net Profit Over Time')
    plt.xticks(rotation=45)  # Rotate x-axis labels for readability
    plt.grid(True)
    plt.tight_layout()  # Adjust layout to prevent clipping of labels
    plt.show()
'''

# Example call for testing
#grid_trade('AUDNZD=X', contract_size=100000, stop_loss_level=10, step=0.0008)
