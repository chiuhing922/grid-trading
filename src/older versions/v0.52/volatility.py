# volatility.py

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class VolatilityCache:
    """Cache for volatility calculations"""
    lookback: int
    resample_period: str
    atr_values: np.ndarray
    timestamp: pd.Timestamp  # For potential cache invalidation

class VolatilityManager:
    """Manager for volatility calculations and caching"""
    def __init__(self):
        self._cache: Dict[Tuple[int, str], VolatilityCache] = {}

    def _convert_resample_period(self, period: str) -> str:
        """Convert deprecated resample periods to new format"""
        # Convert 'H' to 'h' for hours
        if period.endswith('H'):
            return period.replace('H', 'h')
        return period
            
        
    def calculate_atr_series(
        self, 
        data: pd.DataFrame, 
        lookback: int,
        resample_period: str = '30min'
    ) -> np.ndarray:
        """
        Pre-calculate ATR for entire dataset with given lookback period
        
        Args:
            data: DataFrame with OHLC data
            lookback: Lookback period for ATR calculation
            resample_period: Timeframe to resample to ('15min', '30min', '1H', etc)
            
        Returns:
            numpy array of ATR values aligned with original data
        """
        # Check cache first using composite key
        cache_key = (lookback, resample_period)
        if cache_key in self._cache:
            cache = self._cache[cache_key]
            # Could add timestamp checking here if data might change
            return cache.atr_values
        
        # Ensure data has datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.set_index('Datetime')


        # Resample data to higher timeframe
        resampled = data.resample(resample_period).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last'
        }).dropna()

        # Calculate True Range on resampled data
        high = resampled['High'].values
        low = resampled['Low'].values
        close = np.roll(resampled['Close'].values, 1)
        close[0] = resampled['Close'].values[0]
        
        # True Range calculations
        tr1 = np.abs(high - low)
        tr2 = np.abs(high - close)
        tr3 = np.abs(low - close)
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Calculate ATR on resampled data
        resampled_atr = np.zeros(len(resampled))
        for i in range(len(resampled)):
            if i < lookback:
                resampled_atr[i] = np.mean(true_range[:i+1])
            else:
                resampled_atr[i] = np.mean(true_range[i-lookback+1:i+1])
        
        # Create a series with resampled ATR
        atr_series = pd.Series(
            resampled_atr, 
            index=resampled.index
        )

                # Create a copy of original data to align ATR values
        if isinstance(data.index, pd.DatetimeIndex):
            original_index = data.index
        else:
            original_index = pd.to_datetime(data['Datetime'])
            
        
        # Forward fill ATR values back to original data frequency
        full_atr = atr_series.reindex(
            data.index, 
            method='ffill'  # Use last known ATR until next calculation
        )
        
        # Handle any remaining NaN values using newer methods
        atr_values = full_atr.ffill().bfill().values
        
        # Cache the results
        self._cache[cache_key] = VolatilityCache(
            lookback=lookback,
            resample_period=resample_period,
            atr_values=atr_values,
            timestamp=pd.Timestamp.now()
        )
        
        return atr_values
    
    def clear_cache(self):
        """Clear the volatility cache"""
        self._cache.clear()