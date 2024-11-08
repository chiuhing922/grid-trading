import yfinance as yf
import pandas as pd
import numpy as np 
import csv
import matplotlib.pyplot as plt
import config as c


from enum import Enum
from typing import List, Tuple, Optional
import pandas as pd

class PositionType(Enum):
    LONG = 'long'
    SHORT = 'short'

class ContractQuantity(Enum):
    SINGLE = 'single'
    ALL = 'all'    

def close_positions(
    data: pd.DataFrame,
    position_stack: List[float],
    current_price: float,
    position_type: PositionType,
    contract_quantity: ContractQuantity,
    is_final_close: bool = False
) -> None:
    """
    Unified function to close trading positions.
    
    Args:
        data: DataFrame containing trading data
        position_stack: List of entry prices for positions to be closed
        current_price: Current market price
        position_type: Enum indicating if positions are LONG or SHORT
        is_final_close: Boolean indicating if this is final closing at end of backtest
    """
    if not position_stack:
        return
            
    commission = max(c.commission_rate * c.contract_size * current_price, 2)
    # Closing Single contract
    if contract_quantity == ContractQuantity.SINGLE:
        entry_price = position_stack.pop()
        # Calculate profit based on position type
        if position_type == PositionType.LONG:
            profit = c.contract_size * (current_price - entry_price)
            c.position -= 1
        else:  # SHORT
            profit = c.contract_size * (entry_price - current_price)
            c.position += 1
            
        # Update trading statistics
        c.accumulated_profit += profit
        c.accumulated_net_profit += profit - commission
        c.max_drawdown = record_max_drawdown()
        c.total_commission += commission
        c.accumulated_contract += 1
        
        # Record profit data
        update_profit_data(data)
        
        if not is_final_close:
            log_trade(data, position_type, entry_price, current_price, profit) 
            
    elif contract_quantity == ContractQuantity.ALL:
    # Closing ALL contracts    
        while position_stack:
            entry_price = position_stack.pop()
        
            # Calculate profit based on position type
            if position_type == PositionType.LONG:
                profit = c.contract_size * (current_price - entry_price)
                c.position -= 1
            else:  # SHORT
                profit = c.contract_size * (entry_price - current_price)
                c.position += 1
        
             # Update trading statistics
            c.accumulated_profit += profit
            c.accumulated_net_profit += profit - commission
            c.max_drawdown = record_max_drawdown()
            c.total_commission += commission
            c.accumulated_contract += 1
        
            # Record profit data
            update_profit_data(data)
        
            if not is_final_close:
                log_trade(data, position_type, entry_price, current_price, profit)

def close_all_positions(
    data: pd.DataFrame,
    long_stack: List[float],
    short_stack: List[float],
    current_price: float
) -> None:
    """
    Close all outstanding positions during end of backtest or emergency situations.
    
    Args:
        data: DataFrame containing trading data
        long_stack: List of entry prices for long positions
        short_stack: List of entry prices for short positions
        current_price: Current market price
    """
    # Close short positions first if they exist
    if c.position < 0:
        close_positions(data, short_stack, current_price, PositionType.SHORT, ContractQuantity.ALL, True)
    
    # Close long positions if they exist
    elif c.position > 0:
        close_positions(data, long_stack, current_price, PositionType.LONG, ContractQuantity.ALL, True)

def log_trade(
    data: pd.DataFrame,
    position_type: PositionType,
    entry_price: float,
    exit_price: float,
    profit: float
) -> None:
    """
    Log trading activity for analysis and debugging.
    
    Args:
        data: DataFrame containing trading data
        position_type: Type of position being closed
        entry_price: Entry price of the position
        exit_price: Exit price of the position
        profit: Profit/loss from the trade
    """
    position_str = f"{position_type.value.capitalize()} Position: {c.position}"
    if position_type == PositionType.LONG:
        position_str = f"{position_str}+1"
    else:
        position_str = f"{position_str}-1"
        
    if c.enable_logging:
        print(f"Record No: {c.record_no} Close {position_type.value.capitalize()} "
              f"Position: {position_str} of entry price {entry_price:.2f} "
              f"at price {exit_price:.2f}")
        print(f"Trade Profit: {profit:.2f}, Accumulated Net Profit: {c.accumulated_net_profit:.2f}")

# Example usage in grid_trade function:
"""
# Replace existing close position calls with:

# For closing long positions:
close_positions(data, long_stack, current_price, PositionType.LONG)

# For closing short positions:
close_positions(data, short_stack, current_price, PositionType.SHORT)

# For closing all positions at end of backtest:
close_all_positions(data, long_stack, short_stack, current_price)



"""

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
    

def update_profit_data(data):
    c.profit_data.append((data['Datetime'].iloc[c.record_no-1], c.accumulated_net_profit, c.accumulated_profit))
    #print(f"Profit data of record no {c.record_no} of value of {c.accumulated_net_profit} updated!")
    
    
def grid_trade(data, symbol, stop_loss_amount, stop_loss_level, step):

 # Define local variables
    current_price = float(data['Close'].values[0])
    reference_price = current_price
    next_long_price = reference_price - c.step
    next_short_price = reference_price + c.step
    long_stack = []
    short_stack = []
    
    c.stop_loss_count=0
    c.profit_data = []
    
# reset all parameters for each simulation
    c.total_commission = 0 
    c.max_drawdown = 0
    c.max_risk = 0
    c.accumulated_profit = 0
    c.accumulated_net_profit = 0
    c.accumulated_contract = 0
    c.position = 0
    c.stop_loss_count = 0
    c.win_loss_record = []
    c.record_no = 0  
    c.profit_data = []
    
  # Get paramenter from argument
    c.stop_loss_amount = stop_loss_amount
    c.stop_loss_level = stop_loss_level
    c.step = step  


# Simulate trading logic with historical data for backtesting
    for current_price in data['Close'].values:
        commission = max(c.commission_rate * c.contract_size * current_price, 2)
        c.record_no += 1
        current_price = float(current_price)
        
    # Close long positions: Don't buy any more if stop loss condition is triggered
        if (c.position >= c.stop_loss_level and current_price <= next_long_price):
            #close_all_long_position(data, long_stack, current_price)
            close_positions(data, long_stack, current_price, PositionType.LONG, ContractQuantity.ALL)
            """
            #close_all_positions(data, long_stack, short_stack, current_price)
            #print(f"Record No: {c.record_no} Closed all long positions at price {current_price}. Accumulated Net Profit: {c.accumulated_net_profit}")
            c.position = 0
            c.stop_loss_count +=1
            """
            if c.accumulated_net_profit < (-1 * c.stop_loss_amount):   
                break        #Stop loss
        
    # Close short positions: Don't Short any more if stop loss condition is triggered
        elif (c.position <= (-1 * c.stop_loss_level) and current_price >= next_short_price):
            #close_all_short_position(data, short_stack, current_price)
            #close_all_positions(data, long_stack, short_stack, current_price)
            close_positions(data, short_stack, current_price, PositionType.SHORT, ContractQuantity.ALL)
            """
            #print(f"Record No: {c.record_no} Closed all short positions at price {current_price}. Accumulated Net Profit: {c.accumulated_net_profit}")
            c.position = 0
            c.stop_loss_count +=1
            """
            if c.accumulated_net_profit < (-1 * c.stop_loss_amount):
                break        #Stop loss

    # Normal Long logic
        if current_price <= next_long_price:
            if c.position >= 0:
                c.position += 1
                long_stack.append(current_price)
                #print(f"Record No: {c.record_no} Submitted long contract. Position: {c.position} at price {current_price}")
            else:   # closing existing short contract
                close_positions(data, short_stack, current_price, PositionType.SHORT, ContractQuantity.SINGLE)
                '''
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
                '''
            next_long_price -= c.step
            next_short_price -= c.step

    # Normal Short logic
        elif current_price >= next_short_price:
            if c.position <= 0:
                c.position -= 1
                short_stack.append(current_price)
                #print(f"Record No: {c.record_no} Submitted short contract. Position: {c.position} at price {current_price}")
            else:
                close_positions(data, long_stack, current_price, PositionType.LONG, ContractQuantity.SINGLE)
                ''' 
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
                '''
            next_short_price += c.step
            next_long_price += c.step
            
    return (c.accumulated_profit, c.accumulated_net_profit, c.max_drawdown, c.accumulated_contract,c.stop_loss_count)


