import yfinance as yf
import pandas as pd
import numpy as np

def fetch_YF_data(symbol, period='5d', interval='1m'):
    data = yf.download(symbol, period=period, interval=interval)
    data.columns = data.columns.droplevel('Ticker')   # added this line to drop the ticker e.g. EURUSD=X
    return data

def load_data_from_csv(file_path):
    data = pd.read_csv(file_path)
    # Combine Date and Time into a single DateTime column
    data['Datetime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'])
    data.drop(columns=['Date', 'Time'], inplace=True)

    #data.set_index('Date', inplace=True)
    columns_order = ['Datetime', 'Open', 'High', 'Low', 'Close']
    columns_rename = {
    'Datetime': 'Datetime',    
    'BO': 'Open',
    'BH': 'High',
    'BL': 'Low',
    'BC': 'Close'
    }
    # Rename columns
    data = data.rename(columns=columns_rename)
    # Reorder columns
    data = data[columns_order]
    return data

