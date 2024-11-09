import yfinance as yf
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from enum import Enum
import os

class DataSource(Enum):
    YAHOO_FINANCE = 'yahoo_finance'
    CSV = 'csv'

class DataConnector:
    """
    A class to handle different data sources for trading data
    """
    
    def __init__(self):
        self.required_columns = ['Datetime', 'Open', 'High', 'Low', 'Close']
        
    def get_data(self, 
                 source: DataSource,
                 symbol: Optional[str] = None,
                 period: str = '5d',
                 interval: str = '1m',
                 file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Get data from specified source
        
        Args:
            source: Source of data (YAHOO_FINANCE or CSV)
            symbol: Trading symbol (required for YAHOO_FINANCE)
            period: Time period for data (for YAHOO_FINANCE)
            interval: Time interval for data (for YAHOO_FINANCE)
            file_path: Path to CSV file (required for CSV)
            
        Returns:
            DataFrame with standardized format
        """
        if source == DataSource.YAHOO_FINANCE:
            if not symbol:
                raise ValueError("Symbol is required for Yahoo Finance data")
            data = self._fetch_yahoo_finance(symbol, period, interval)
        elif source == DataSource.CSV:
            if not file_path:
                raise ValueError("File path is required for CSV data")
            data = self._load_csv(file_path)
        else:
            raise ValueError(f"Unsupported data source: {source}")
            
        return self._validate_data(data)
    
    def _fetch_yahoo_finance(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Fetch data from Yahoo Finance"""
        try:
            data = yf.download(symbol, period=period, interval=interval)
            # Handle multi-level columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel('Ticker')
            
            # Ensure datetime index is converted to column
            data = data.reset_index()
            data = data.rename(columns={'Date': 'Datetime', 'Datetime': 'Datetime'})
            
            return data
            
        except Exception as e:
            raise Exception(f"Error fetching data from Yahoo Finance: {str(e)}")
    
    def _load_csv(self, file_path: str) -> pd.DataFrame:
        """Load data from CSV file"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"CSV file not found: {file_path}")
                
            data = pd.read_csv(file_path)
            
            # Handle different CSV formats
            if 'Date' in data.columns and 'Time' in data.columns:
                # Combine Date and Time into Datetime
                data['Datetime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'])
                data.drop(columns=['Date', 'Time'], inplace=True)
            
            # Standard column mapping
            column_mapping = {
                'BO': 'Open',
                'BH': 'High',
                'BL': 'Low',
                'BC': 'Close',
            }
            
            # Apply column mapping if needed
            data = data.rename(columns=column_mapping)
            
            return data
            
        except Exception as e:
            raise Exception(f"Error loading CSV file: {str(e)}")
    
    def _validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and standardize data format"""
        # Check required columns
        missing_cols = [col for col in self.required_columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Ensure datetime is in correct format
        if not pd.api.types.is_datetime64_any_dtype(data['Datetime']):
            data['Datetime'] = pd.to_datetime(data['Datetime'])
        
        # Sort by datetime
        data = data.sort_values('Datetime')
        
        # Select and order required columns
        data = data[self.required_columns]
        
        return data
    
    def save_data(self, data: pd.DataFrame, file_path: str) -> None:
        """Save data to CSV file"""
        try:
            data.to_csv(file_path, index=False)
            print(f"Data saved successfully to {file_path}")
        except Exception as e:
            raise Exception(f"Error saving data: {str(e)}")

# Example usage functions for backward compatibility
def fetch_YF_data(symbol: str, period: str = '5d', interval: str = '1m') -> pd.DataFrame:
    """Backward compatible function for fetching Yahoo Finance data"""
    connector = DataConnector()
    return connector.get_data(
        source=DataSource.YAHOO_FINANCE,
        symbol=symbol,
        period=period,
        interval=interval
    )

def load_data_from_csv(file_path: str) -> pd.DataFrame:
    """Backward compatible function for loading CSV data"""
    connector = DataConnector()
    return connector.get_data(
        source=DataSource.CSV,
        file_path=file_path
    )