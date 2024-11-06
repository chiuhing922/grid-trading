import yfinance as yf
import pandas as pd
import numpy as np 
import csv
import matplotlib.pyplot as plt
     

def grid_trade(data, symbol, contract_size, stop_loss_amount, stop_loss_level, step):

    current_price = float(data['Close'].values[0])
    reference_price = current_price
    next_long_price = reference_price - step
    next_short_price = reference_price + step
    position = 0
    long_stack = []
    short_stack = []
    accumulated_net_profit = 0.0
    accumulated_contract = 0
    stop_loss_count=0
    record_no = 0
    commission_rate = 0.2 * 0.0001   # https://www.interactivebrokers.com.au/en/pricing/commissions-spot-currencies.php
    commission = commission_rate * contract_size * current_price
    total_commission = 0
    
    if commission < 2:
        commission = 2

    # Initialize profit chart data list
    profit_data = []


# Simulate trading logic with historical data for backtesting
    for current_price in data['Close'].values:
        record_no += 1
        current_price = float(current_price)
        
    # Close long positions
        if (position >= stop_loss_level and current_price <= next_long_price):
            while long_stack:
                entry_price = long_stack.pop()
                profit = current_price - entry_price
                accumulated_net_profit += profit * contract_size - commission
                accumulated_contract += 1
                position -=1
                print(f"Record No: {record_no} Close Long Position: {position+1} of entry price {entry_price} at price {current_price}")
                print(f"Accumulated Net Profit: {accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                profit_data.append((data.index[record_no-1], accumulated_net_profit))
            print(f"Record No: {record_no} Closed all long positions at price {current_price}. Accumulated Net Profit: {accumulated_net_profit}")
            position = 0
            stop_loss_count +=1
            if accumulated_net_profit < (-1 * stop_loss_amount):
                break        #Stop loss
        
    # Close short positions
        elif (position <= (-1 * stop_loss_level) and current_price >= next_short_price):
            while short_stack:
                entry_price = short_stack.pop()
                profit = entry_price - current_price
                accumulated_net_profit += profit * contract_size - commission
                accumulated_contract += 1
                position +=1
                print(f"Record No: {record_no} Close Short Position: {position-1} of entry price {entry_price} at price {current_price}")
                print(f"Accumulated Net Profit: {accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                profit_data.append((data.index[record_no-1], accumulated_net_profit))
            print(f"Record No: {record_no} Closed all short positions at price {current_price}. Accumulated Net Profit: {accumulated_net_profit}")
            position = 0
            stop_loss_count +=1
            if accumulated_net_profit < (-1 * stop_loss_amount):
                break        #Stop loss

    # Long logic
        if current_price <= next_long_price:
            if position >= 0:
                position += 1
                long_stack.append(current_price)
                print(f"Record No: {record_no} Submitted long contract. Position: {position} at price {current_price}")
            else:
                position += 1
                entry_price = short_stack.pop()
                print(f"Record No: {record_no} Close Short Position: {position-1} of entry price {entry_price} at price {current_price}")
                profit = entry_price - current_price
                accumulated_net_profit += profit * contract_size - commission
                accumulated_contract += 1
                print(f"Accumulated Net Profit: {accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                profit_data.append((data.index[record_no-1], accumulated_net_profit))
            next_long_price -= step
            next_short_price -= step

    # Short logic
        elif current_price >= next_short_price:
            if position <= 0:
                position -= 1
                short_stack.append(current_price)
                print(f"Record No: {record_no} Submitted short contract. Position: {position} at price {current_price}")
            else:
                position -= 1
                entry_price = long_stack.pop()
                print(f"Record No: {record_no} Close Long Position: {position+1} of entry price {entry_price} at price {current_price}")
                profit = current_price - entry_price
                accumulated_net_profit += profit * contract_size - commission
                accumulated_contract += 1
                print(f"Accumulated Net Profit: {accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                profit_data.append((data.index[record_no-1], accumulated_net_profit))
            next_short_price += step
            next_long_price += step

 
    
    # end of all backtest data, clear all remaining position
    if position<0:
        while short_stack:
            entry_price = short_stack.pop()
            profit = entry_price - current_price
            accumulated_net_profit += profit * contract_size - commission
            accumulated_contract += 1
            position +=1
            print(f"Record No: {record_no} Close Short Position: {position-1} of entry price {entry_price} at price {current_price}")
            print(f"Accumulated Net Profit: {accumulated_net_profit}")
            #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
            profit_data.append((data.index[record_no-1], accumulated_net_profit))
        print(f"End of data: Closed all remaining short positions. Accumulated Net Profit: {accumulated_net_profit}")
    elif position>0:
        # close all outstanding contract at the end
        while long_stack:
            entry_price = long_stack.pop()
            profit = current_price - entry_price
            accumulated_net_profit += profit * contract_size - commission
            accumulated_contract += 1
            position -=1
            print(f"Record No: {record_no} Close Long Position: {position+1} of entry price {entry_price} at price {current_price}")
            print(f"Accumulated Net Profit: {accumulated_net_profit}")
            #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
            profit_data.append((data.index[record_no-1], accumulated_net_profit))
        print(f"End of data: Closed all remaining long positions. Accumulated Net Profit: {accumulated_net_profit}")
        

#    max_risk = contract_size * step * stop_loss_level * (stop_loss_level + 1) / 2
    max_risk = stop_loss_amount
    total_commission = commission * accumulated_contract

    print(f"\n\n============================== BACKTEST REPORT ======================================")
    print(f"Currency Traded: {symbol}")
    print(f"Contract size: {contract_size}")
    print(f"Maximum Loss Allowed: {stop_loss_amount}")  
    print(f"Step size: {step}")
    print(f"Stop loss level: {stop_loss_level}")
    print(f"Maximum risk: {max_risk}")
    print(f"Total times of stop loss triggered: {stop_loss_count}\n")   
    print(f"Final Accumulated Commission Fee: {total_commission}")
    print(f"Final Accumulated Contract: {accumulated_contract}")
    print(f"Final Profit: {accumulated_net_profit}")
    print(f"Return to Risk Ratio (the higher the better): {accumulated_net_profit/max_risk}")
    print(f"=============================== End REPORT ==========================================\n\n")
    
   # Save profit_data to CSV
    '''
    with open('d:/dev/quant/output/profit_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['DateTime', 'AccumulatedProfit'])
        writer.writerows(profit_data)
    print("Data exported to profit_data.csv")
    ''' 
    # Convert list to DataFrame
    df = pd.DataFrame(profit_data, columns=['DateTime', 'AccumulatedProfit'])

    # Convert 'DateTime' to datetime format for plotting
    df['DateTime'] = pd.to_datetime(df['DateTime'])

    # Plotting the data
    plt.figure(figsize=(10, 6))
    plt.plot(df['DateTime'], df['AccumulatedProfit'], marker='o', linestyle='-')
    plt.xlabel('DateTime')
    plt.ylabel('Accumulated Net Profit')
    plt.title('Accumulated Net Profit Over Time')
    plt.xticks(rotation=45)  # Rotate x-axis labels for readability
    plt.grid(True)
    plt.tight_layout()  # Adjust layout to prevent clipping of labels
    plt.show()

# Example call for testing
#grid_trade('AUDNZD=X', contract_size=100000, stop_loss_level=10, step=0.0008)
