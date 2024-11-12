import pandas as pd
import plotly.graph_objects as go

# Load data
file_path = 'd:/dev/quant/data-source/kaggle/eurusd_hour.csv'  # Update with your file path
data = pd.read_csv(file_path)

# Combine Date and Time into a single DateTime column
data['DateTime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'])

# Set DateTime as index (optional, for easier plotting)
data.set_index('DateTime', inplace=True)

# Filter columns for bid prices or ask prices
# Uncomment one set depending on whether you want to plot bid or ask prices
# For Bid prices
candlestick_data = data[['BO', 'BH', 'BL', 'BC']].rename(columns={'BO': 'Open', 'BH': 'High', 'BL': 'Low', 'BC': 'Close'})

# # For Ask prices
# candlestick_data = data[['AO', 'AH', 'AL', 'AC']].rename(columns={'AO': 'Open', 'AH': 'High', 'AL': 'Low', 'AC': 'Close'})

# Plotting the candlestick chart
fig = go.Figure(data=[go.Candlestick(
    x=candlestick_data.index,
    open=candlestick_data['Open'],
    high=candlestick_data['High'],
    low=candlestick_data['Low'],
    close=candlestick_data['Close']
)])

fig.update_layout(
    title='EUR/USD Candlestick Chart',
    xaxis_title='DateTime',
    yaxis_title='Price (EUR/USD)',
    xaxis_rangeslider_visible=False,
    yaxis=dict(
        dtick=0.005  # Sets grid line interval for y-axis to 0.005
    )
)

fig.show()