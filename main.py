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
data = dc.load_data_from_csv('d:/dev/quant/data-source/kaggle/eurusd_minute.csv')
#grid_trade(data=data, symbol='EURUSD=X', contract_size=100000, stop_loss_amount=3000, stop_loss_level=4, step=0.002)

result = grid_trade.grid_trade(data=data, symbol=symbol, stop_loss_amount=10000, stop_loss_level=4, step=0.0005 )


'''
for stop_loss_amount in range(1000, 11000, 1000):  # Example: 1000 to 10000 in steps of 1000
    for stop_loss_level in range(3, 11, 1):            # Example: 3 to 10 in steps of 1
        for step in np.arange(0.0005, 0.0105, 0.0005):  # Example: 0.001 to 0.01 in steps of 0.001
            # Run the function and capture 4 data points
            
            result = grid_trade.grid_trade(data=data, symbol=symbol, stop_loss_amount=stop_loss_amount, stop_loss_level=stop_loss_level, step=step )
            
            # Assuming `grid_trade.grid_trade()` returns the 4 data points, you can unpack them
            # Example: (profit, max_drawdown, total_commission, final_position)
            gross_profit, net_profit, max_drawdown, total_trade, stop_loss_triggered = result
            
            # Append the data points along with the parameters to results
            results.append({
                'stop_loss_amount': stop_loss_amount,
                'stop_loss_level': stop_loss_level,
                'step': step,
                'gross profit': gross_profit,
                'net profit': net_profit,
                'max_drawdown': max_drawdown,
                'total trade': total_trade,
                'stop loss triggered': stop_loss_triggered
            })


'''
# Convert results to DataFrame for easy viewing (optional)
import pandas as pd
results_df = pd.DataFrame(results)
print(results_df) 

# Generate a unique filename with a timestamp
timestamp = time.strftime("%Y%m%d_%H%M%S")
filename = f'd:/dev/quant/output/backtest_results_{timestamp}.csv'

# Save results to CSV file
# Save results to CSV file with the unique timestamped filename
results_df.to_csv(filename, index=False)
print(f"Results saved to '{filename}'.")


re.gen_report()
end_time = time.time()
execution_time = end_time - start_time
print(f"Backtest execution time: {execution_time:.4f} seconds")
 
 
 