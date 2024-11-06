import yfinance as yf
import pandas as pd
import numpy as np 
import csv
import matplotlib.pyplot as plt
import config as c

     
def record_max_drawdown():
    #global accumulated_net_profit
    #global max_drawdown
    if c.accumulated_net_profit<0 and c.accumulated_net_profit<c.max_drawdown:
        return c.accumulated_net_profit
    else:
        return c.max_drawdown
    
def get_win_loss_score (n):
    score=0
    length = len(c.win_loss_record)
    if length<n:
        n = length  
    for i in range(length-n, length):
        score += c.win_loss_record[i]
    return score  
    
def close_all_long_position(data, long_stack, current_price):    
    commission = max(c.commission_rate * c.contract_size * current_price, 2)
    while long_stack:
        entry_price = long_stack.pop()
        profit = c.contract_size * (current_price - entry_price)
        c.accumulated_profit += profit
        c.accumulated_net_profit += profit - commission
        c.max_drawdown = record_max_drawdown()
        c.total_commission += commission
        c.accumulated_contract += 1
        c.position -=1
        #print(f"Record No: {c.record_no} Close Long Position: {c.position+1} of entry price {entry_price} at price {current_price}")
        #print(f"Accumulated Net Profit: {c.accumulated_net_profit}")
        update_profit_data(data)
    
def close_all_short_position(data, short_stack, current_price):
    commission = max(c.commission_rate * c.contract_size * current_price, 2)
    while short_stack:
        entry_price = short_stack.pop()
        profit = c.contract_size * (entry_price - current_price)
        c.accumulated_profit += profit
        c.accumulated_net_profit += profit - commission
        c.max_drawdown = record_max_drawdown()
        c.total_commission += commission
        c.accumulated_contract += 1
        c.position +=1
        #print(f"Record No: {c.record_no} Close Short Position: {c.position-1} of entry price {entry_price} at price {current_price}")
        #print(f"Accumulated Net Profit: {c.accumulated_net_profit}")
        update_profit_data(data)
        
def close_all_position(data, long_stack, short_stack, current_price):        
    # end of all backtest data, clear all remaining position

    commission = max(c.commission_rate * c.contract_size * current_price, 2)
    
    if c.position<0:
        while short_stack:
            entry_price = short_stack.pop()
            profit = c.contract_size * (entry_price - current_price)
            c.accumulated_profit += profit
            c.accumulated_net_profit += profit - commission
            c.max_drawdown = record_max_drawdown()
            c.total_commission += commission
            c.accumulated_contract += 1
            c.position +=1
            #print(f"Record No: {c.record_no} Close Short Position: {c.position-1} of entry price {entry_price} at price {current_price}")
            #print(f"Accumulated Net Profit: {c.accumulated_net_profit}")
            #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
            #profit_data.append((data.index[record_no-1], accumulated_net_profit))
            update_profit_data(data)
        #print(f"End of data: Closed all remaining short positions. Accumulated Net Profit: {c.accumulated_net_profit}")
    elif c.position>0:
        # close all outstanding contract at the end
        while long_stack:
            entry_price = long_stack.pop()
            profit = c.contract_size * (current_price - entry_price)
            c.accumulated_profit += profit
            c.accumulated_net_profit += profit - commission
            c.max_drawdown = record_max_drawdown()
            c.total_commission += commission
            c.accumulated_contract += 1
            c.position -=1
            #print(f"Record No: {c.record_no} Close Long Position: {c.position+1} of entry price {entry_price} at price {current_price}")
            #print(f"Accumulated Net Profit: {c.accumulated_net_profit}")
            #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
            #profit_data.append((data.index[record_no-1], accumulated_net_profit))
            update_profit_data(data)
        #print(f"End of data: Closed all remaining long positions. Accumulated Net Profit: {c.accumulated_net_profit}")
        
        
def update_profit_data(data):
    c.profit_data.append((data['Datetime'].iloc[c.record_no-1], c.accumulated_net_profit, c.accumulated_profit))
    #print(f"Profit data of record no {c.record_no} of value of {c.accumulated_net_profit} updated!")
    
    
def grid_trade(data, symbol):

 # Define local variables
    current_price = float(data['Close'].values[0])
    reference_price = current_price
    next_long_price = reference_price - c.step
    next_short_price = reference_price + c.step
    long_stack = []
    short_stack = []
    
    c.stop_loss_count=0
    c.profit_data = []
    

# Simulate trading logic with historical data for backtesting
    for current_price in data['Close'].values:
        commission = max(c.commission_rate * c.contract_size * current_price, 2)
        c.record_no += 1
        current_price = float(current_price)
        
    # Close long positions: Don't buy any more if stop loss condition is triggered
        if (c.position >= c.stop_loss_level and current_price <= next_long_price):
            close_all_long_position(data, long_stack, current_price)
            #print(f"Record No: {c.record_no} Closed all long positions at price {current_price}. Accumulated Net Profit: {c.accumulated_net_profit}")
            c.position = 0
            c.stop_loss_count +=1
            if c.accumulated_net_profit < (-1 * c.stop_loss_amount):
                break        #Stop loss
        
    # Close short positions: Don't Short any more if stop loss condition is triggered
        elif (c.position <= (-1 * c.stop_loss_level) and current_price >= next_short_price):
            close_all_short_position(data, short_stack, current_price)
            #print(f"Record No: {c.record_no} Closed all short positions at price {current_price}. Accumulated Net Profit: {c.accumulated_net_profit}")
            c.position = 0
            c.stop_loss_count +=1
            if c.accumulated_net_profit < (-1 * c.stop_loss_amount):
                break        #Stop loss

    # Normal Long logic
        if current_price <= next_long_price:
            if c.position >= 0:
                c.position += 1
                long_stack.append(current_price)
                #print(f"Record No: {c.record_no} Submitted long contract. Position: {c.position} at price {current_price}")
            else:   # closing existing short contract
                c.position += 1
                entry_price = short_stack.pop()
                #print(f"Record No: {c.record_no} Close Short Position: {c.position-1} of entry price {entry_price} at price {current_price}")
                profit = (entry_price - current_price) * c.contract_size
                commission = max(c.commission_rate * c.contract_size * current_price, 2)
                c.accumulated_profit += profit
                c.accumulated_net_profit += profit - commission
                c.max_drawdown = record_max_drawdown()
                c.total_commission += commission
                c.accumulated_contract += 1
                #print(f"Accumulated Net Profit: {c.accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                #profit_data.append((data.index[record_no-1], accumulated_net_profit))
                update_profit_data(data)
            next_long_price -= c.step
            next_short_price -= c.step

    # Normal Short logic
        elif current_price >= next_short_price:
            if c.position <= 0:
                c.position -= 1
                short_stack.append(current_price)
                #print(f"Record No: {c.record_no} Submitted short contract. Position: {c.position} at price {current_price}")
            else:
                c.position -= 1
                entry_price = long_stack.pop()
                #print(f"Record No: {c.record_no} Close Long Position: {c.position+1} of entry price {entry_price} at price {current_price}")
                profit = (current_price - entry_price) * c.contract_size
                c.accumulated_profit += profit
                c.accumulated_net_profit += profit - commission
                c.total_commission += commission
                c.accumulated_contract += 1
                #print(f"Accumulated Net Profit: {c.accumulated_net_profit}")
                #profit_data.append((data['Datetime'].iloc[record_no-1], accumulated_net_profit))
                #profit_data.append((data.index[record_no-1], accumulated_net_profit))
                update_profit_data(data)
            next_short_price += c.step
            next_long_price += c.step
            
    return (c.accumulated_profit, c.accumulated_net_profit, c.max_drawdown, c.accumulated_contract,c.stop_loss_count)


