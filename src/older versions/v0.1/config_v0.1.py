#put all global variable here
# define global variable     
#define global variable
contract_size = 100000
stop_loss_amount = 10000
stop_loss_level=4
step=0.0005
fx_symbol=''     
commission_rate = 0.2 * 0.0001   # https://www.interactivebrokers.com.au/en/pricing/commissions-spot-currencies.php
total_commission = 0 
max_drawdown = 0
max_risk = 0
accumulated_profit = 0
accumulated_net_profit = 0
accumulated_contract = 0
position = 0
stop_loss_count = 0


win_loss_record = []
win_loss_score_n = 8   # the last n win-loss record to calculate the win_loss_score  
record_no = 0  
profit_data = []
enable_logging = False