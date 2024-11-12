def calculate_atr(data, period=14):
    data['H-L'] = data['High'] - data['Low']
    data['H-Cp'] = abs(data['High'] - data['Close'].shift(1))
    data['L-Cp'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-Cp', 'L-Cp']].max(axis=1)
    data['ATR'] = data['TR'].rolling(window=period).mean()
    return data['ATR'].iloc[-1]