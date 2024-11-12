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
    HISTDATA = 'histdata'

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
        """Get data from specified source"""
        if source == DataSource.YAHOO_FINANCE:
            if not symbol:
                raise ValueError("Symbol is required for Yahoo Finance data")
            data = self._fetch_yahoo_finance(symbol, period, interval)
        elif source == DataSource.CSV:
            if not file_path:
                raise ValueError("File path is required for CSV data")
            data = self._load_csv(file_path)
        elif source == DataSource.HISTDATA:
            if not file_path or not symbol:
                raise ValueError("File path and symbol are required for HistData")
            data = self._load_histdata(file_path, symbol)
        else:
            raise ValueError(f"Unsupported data source: {source}")
            
        return self._validate_data(data)
    
    def _fetch_yahoo_finance(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Fetch data from Yahoo Finance"""
        try:
            data = yf.download(symbol, period=period, interval=interval)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel('Ticker')
            
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
            
            if 'Date' in data.columns and 'Time' in data.columns:
                data['Datetime'] = pd.to_datetime(data['Date'] + ' ' + data['Time'])
                data.drop(columns=['Date', 'Time'], inplace=True)
            
            column_mapping = {
                'BO': 'Open',
                'BH': 'High',
                'BL': 'Low',
                'BC': 'Close',
            }
            
            data = data.rename(columns=column_mapping)
            return data
            
        except Exception as e:
            raise Exception(f"Error loading CSV file: {str(e)}")
    
    def _load_histdata(self, file_path: str, symbol: str) -> pd.DataFrame:
        """
        Load data from HistData format file
        
        Args:
            file_path: Path to CSV file with format:
                    Datetime,Open,High,Low,Close,Volume
                    YYYY-MM-DD HH:mm:SS,x.xxxx,x.xxxx,x.xxxx,x.xxxx,n
            symbol: Currency pair symbol (e.g., 'EURUSD')
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            print(f"Processing {file_path}")
            
            # Read CSV file with standard format (it has headers)
            df = pd.read_csv(file_path)
            
            # Ensure expected columns exist
            expected_columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")
            
            # Convert datetime (already in correct format 'YYYY-MM-DD HH:mm:SS')
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            
            # Clean up
            df = df.drop_duplicates(subset=['Datetime'])
            df = df.sort_values('Datetime')
            
            print(f"Successfully loaded {len(df):,} rows of data")
            print(f"Date range: {df['Datetime'].min()} to {df['Datetime'].max()}")
            
            # Optional: drop Volume column if not needed
            if 'Volume' in df.columns:
                df = df.drop('Volume', axis=1)
            
            return df
            
        except Exception as e:
            print(f"Error details: {str(e)}")
            raise Exception(f"Error loading HistData file: {str(e)}")    
    def _validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and standardize data format"""
        if data.empty:
            raise ValueError("Empty dataset received")
            
        missing_cols = [col for col in self.required_columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        # Validate numeric columns
        numeric_cols = ['Open', 'High', 'Low', 'Close']
        for col in numeric_cols:
            if not pd.to_numeric(data[col], errors='coerce').notnull().all():
                raise ValueError(f"Column {col} contains non-numeric values")
                
        if not pd.api.types.is_datetime64_any_dtype(data['Datetime']):
            data['Datetime'] = pd.to_datetime(data['Datetime'])
        
        data = data.sort_values('Datetime')
        data = data[self.required_columns]
        
        return data

# Convenience functions for backward compatibility
def fetch_YF_data(symbol: str, period: str = '5d', interval: str = '1m') -> pd.DataFrame:
    """Fetch data from Yahoo Finance"""
    connector = DataConnector()
    return connector.get_data(
        source=DataSource.YAHOO_FINANCE,
        symbol=symbol,
        period=period,
        interval=interval
    )

def load_data_from_csv(file_path: str) -> pd.DataFrame:
    """Load data from CSV file"""
    connector = DataConnector()
    return connector.get_data(
        source=DataSource.CSV,
        file_path=file_path
    )

def load_histdata(file_path: str, symbol: str) -> pd.DataFrame:
    """Load data from HistData format file"""
    connector = DataConnector()
    return connector.get_data(
        source=DataSource.HISTDATA,
        file_path=file_path,
        symbol=symbol
    )