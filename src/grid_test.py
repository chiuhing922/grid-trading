import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta

# Download the EUR/USD data for the last 59 days with a 5-minute interval
dataF = yf.download("EURUSD=X", start=pd.Timestamp.today() - pd.DateOffset(days=59), end=pd.Timestamp.today(), interval='5m')

grid_distance = 0.005
midprice = 1.065

def generate_grid(midprice, grid_distance, grid_range):
    return np.arange(midprice - grid_range, midprice + grid_range, grid_distance)

grid = generate_grid(midprice=midprice, grid_distance=grid_distance, grid_range=0.1)


signal = [0] * len(dataF)
i = 0
for index, row in dataF.iterrows():
    for p in grid:
        if min(row.Low, row.High) < p and max(row.Low, row.High) > p:
            signal[i] = 1
    i += 1
dataF["signal"] = signal
dataF[dataF["signal"] == 1]


dfpl = dataF[:].copy()

def SIGNAL():
    return dfpl.signal

dfpl['ATR'] = ta.atr(high=dfpl.High, low=dfpl.Low, close=dfpl.Close, length=16)
dfpl.dropna(inplace=True)


from backtesting import Strategy
from backtesting import Backtest
import backtesting

class MyStrat(Strategy):
    mysize = 50
    
    def init(self):
        super().init()
        self.signal1 = self.I(SIGNAL)

    def next(self):
        super().next()
        slatr = 1.5 * grid_distance  # Stop loss distance
        TPSLRatio = 0.5  # Take profit to stop loss ratio

        if self.signal1 == 1 and len(self.trades) <= 10000:
            # Sell position
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=self.mysize)

            # Buy position
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=self.mysize)

# Running the backtest
bt = Backtest(dfpl, MyStrat, cash=50, margin=1/100, hedging=True, exclusive_orders=False)
stat = bt.run()
stat
