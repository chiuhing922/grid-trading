import time
import grid_trade
import data_connector as dc
import reporting as re
import config as c
import numpy as np
symbol = 'EURUSD=X'
# Initialize an empty list to store results
results = []

start_time = time.time()
#data = dc.fetch_YF_data(symbol, '5d', '1m')
#data.reset_index(inplace=True)   # only needed if using YF data source
data = dc.load_data_from_csv('d:/dev/quant/data-source/kaggle/eurusd_minute_short.csv')
#grid_trade(data=data, symbol='EURUSD=X', contract_size=100000, stop_loss_amount=3000, stop_loss_level=4, step=0.002)

for c.stop_loss_amount in range(1000, 11000, 5000):  # Example: 1000 to 10000 in steps of 1000
    for c.stop_loss_level in range(3, 11, 2):            # Example: 3 to 10 in steps of 1
        for c.step in np.arange(0.001, 0.011, 0.005):  # Example: 0.001 to 0.01 in steps of 0.001
            # Run the function and capture 4 data points
            result = grid_trade.grid_trade(data=data, symbol=symbol)
            
            # Assuming `grid_trade.grid_trade()` returns the 4 data points, you can unpack them
            # Example: (profit, max_drawdown, total_commission, final_position)
            gross_profit, net_profit, max_drawdown, total_trade, stop_loss_triggered = result
            
            # Append the data points along with the parameters to results
            results.append({
                'stop_loss_amount': c.stop_loss_amount,
                'stop_loss_level': c.stop_loss_level,
                'step': c.step,
                'gross profit': gross_profit,
                'net profit': net_profit,
                'max_drawdown': max_drawdown,
                'total trade': total_trade,
                'stop loss triggered': stop_loss_triggered
            })

# Convert results to DataFrame for easy viewing (optional)
import pandas as pd
results_df = pd.DataFrame(results)
print(results_df) 


#re.gen_report()
end_time = time.time()
execution_time = end_time - start_time
print(f"Backtest execution time: {execution_time:.4f} seconds")
 
 
 