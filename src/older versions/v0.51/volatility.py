# volatility.py

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class VolatilityCache:
    """Cache for volatility calculations"""
    lookback: int
    atr_values: np.ndarray
    timestamp: pd.Timestamp  # For potential cache invalidation

class VolatilityManager:
    """Manager for volatility calculations and caching"""
    def __init__(self):
        self._cache: Dict[int, VolatilityCache] = {}
        
    def calculate_atr_series(self, data: pd.DataFrame, lookback: int) -> np.ndarray:
        """
        Pre-calculate ATR for entire dataset with given lookback period
        
        Args:
            data: DataFrame with OHLC data
            lookback: Lookback period for ATR calculation
            
        Returns:
            numpy array of ATR values
        """
        # Check cache first
        cache_key = lookback
        if cache_key in self._cache:
            cache = self._cache[cache_key]
            # Could add timestamp checking here if data might change
            return cache.atr_values
            
        # Calculate True Range
        high = data['High'].values
        low = data['Low'].values
        close = np.roll(data['Close'].values, 1)
        close[0] = data['Close'].values[0]
        
        # True Range calculations
        tr1 = np.abs(high - low)
        tr2 = np.abs(high - close)
        tr3 = np.abs(low - close)
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Calculate rolling ATR
        atr_values = np.zeros(len(data))
        for i in range(len(data)):
            if i < lookback:
                atr_values[i] = np.mean(true_range[:i+1])
            else:
                atr_values[i] = np.mean(true_range[i-lookback+1:i+1])
        
        # Cache the results
        self._cache[cache_key] = VolatilityCache(
            lookback=lookback,
            atr_values=atr_values,
            timestamp=pd.Timestamp.now()
        )
        
        return atr_values
    
    def clear_cache(self):
        """Clear the volatility cache"""
        self._cache.clear()