import yfinance as yf
import pandas as pd
import numpy as np

# Define the currency pair and fetch historical data
def fetch_data(symbol, period='5d', interval='1m'):
    data = yf.download(symbol, period=period, interval=interval)
    return data


# Fetch historical data from Yahoo Finance
#data = fetch_data('EURUSD=X', period='5d', interval='1m')
data = fetch_data('AUDNZD=X', period='5d', interval='1m')
data['Close'] = data['Adj Close']  # Ensure adjusted close is used if needed


# Define trading logic
contract_size = 100000  #amount of EURO to purchase
factor = 0.005# You can adjust this factor
#step = atr * factor
step = 0.0008
stop_loss_level=10

commission_rate = 0.2 * 0.000001

# Get the initial market price and set reference prices
#reference_price = data['Close'].iloc[-1]
current_price = float(data['Close'].values[0])
reference_price = current_price
next_long_price = reference_price - step
next_short_price = reference_price + step
position = 0

# Initialize stacks and accumulated profit
long_stack = []
short_stack = []
accumulated_profit = 0.0
accumulated_contract=0
record_no=0


# Check data types
print(f"Data type of reference_price: {type(reference_price)}")
print(f"Data type of step: {type(step)}")
print(f"Data type of next_long_price {type(next_long_price)}")
print(f"Data type of next_short_price: {type(next_short_price)}")
print(f"Data type of position: {type(position)}")

print(f"Initial Reference Price: {reference_price}")

# Simulate trading logic with historical data for backtesting
for current_price in data['Close'].values:
    record_no += 1
    current_price = float(current_price)
    '''
    print(f"=============================================================================")
    print(f"Current Price: {current_price}")
    print(f"Next Long Price: {next_long_price}")
    print(f"Next Short Price: {next_short_price}")
  '''
    # Close long positions
    if (position >= stop_loss_level and current_price <= next_long_price):
        while long_stack:
            entry_price = long_stack.pop()
            profit = current_price - entry_price
            accumulated_profit += profit * contract_size 
            accumulated_contract += 1
        print(f"Record No: {record_no} Closed all long positions at price {current_price}. Accumulated Profit: {accumulated_profit}")
        position = 0
        break

    # Close short positions
    elif (position <= (-1 * stop_loss_level) and current_price >= next_short_price):
        while short_stack:
            entry_price = short_stack.pop()
            profit = entry_price - current_price
            accumulated_profit += profit * contract_size
            accumulated_contract += 1
        print(f"Record No: {record_no} Closed all short positions at price {current_price}. Accumulated Profit: {accumulated_profit}")
        position = 0
        break
  
    
    # Long logic
    if current_price <= next_long_price:
        if position >=0:        # add long contract
            position += 1
            long_stack.append(current_price)
            print(f"Record No: {record_no} Submitted long contract. Position: {position} at price {current_price}")
        else:    # clear short contract    
            position += 1
            entry_price=short_stack.pop()
            print(f"Record No: {record_no} Close Short Position: {position} at price {current_price}")
            profit = entry_price - current_price
            accumulated_profit += profit * contract_size  
            accumulated_contract += 1
        next_long_price -= step
        next_short_price -= step

    # Short logic
    elif current_price >= next_short_price:
        if position <= 0:     # add short contract
            position -= 1
            short_stack.append(current_price)
            print(f"Record No: {record_no} Submitted short contract. Position: {position} at price {current_price}")
            
        else:  # close long contract
            position -= 1
            entry_price=long_stack.pop()
            print(f"Record No: {record_no} Close Long Position: {position} at price {current_price}")
            profit = current_price - entry_price
            accumulated_profit += profit * contract_size   
            accumulated_contract += 1         
        next_short_price += step
        next_long_price += step

        


print(f"***************************************")
print(f"Step size: {step}")
print(f"Stop loss level: {stop_loss_level}")
max_risk = contract_size * step * stop_loss_level * (stop_loss_level + 1 )/2
commission = commission_rate * contract_size * accumulated_contract  # commission fee is 0.2 basis point of total contract value
if commission < accumulated_contract * 2 * current_price:   # minimum fee of per contract is 2 USD
    commission = accumulated_contract * 2 * current_price
    
print(f"Maximum risk: {max_risk}")
print(f"Final Accumulated Profit: {accumulated_profit}")
print(f"Final Accumulated Commission Fee: {commission}")
net_profit = accumulated_profit - commission
print(f"Final Accumulated Contract: {accumulated_contract}")
print(f"***********************************************************************")
print(f"Net Profit: {net_profit}")
print(f"Return to Risk Ratio (the higher the better): {net_profit/max_risk}")
print(f"***********************************************************************")