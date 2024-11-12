import os
import pandas as pd
import glob
from typing import List, Tuple
import re

class ForexDataProcessor:
    def __init__(self):
        self.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
        
    def extract_year_and_symbol(self, folder_name: str) -> Tuple[str, str]:
        """Extract year and symbol from folder name"""
        pattern = r'DAT_ASCII_(\w+)_M1_(\d{4})'
        match = re.match(pattern, folder_name)
        if match:
            symbol, year = match.groups()
            return symbol, year
        raise ValueError(f"Invalid folder name format: {folder_name}")
    
    def find_csv_file(self, folder_path: str, year: str, symbol: str) -> str:
        """Find CSV file in folder with exact matching pattern"""
        expected_filename = f"DAT_ASCII_{symbol}_M1_{year}.csv"
        file_path = os.path.join(folder_path, expected_filename)
        
        if os.path.exists(file_path):
            return file_path
        return None
    
    def read_file(self, filepath: str) -> pd.DataFrame:
        """Read and process a single file"""
        try:
            print(f"Reading file: {filepath}")
            # Read CSV with semicolon delimiter and no header
            df = pd.read_csv(filepath, delimiter=';', header=None, names=self.columns)
            
            # Convert datetime
            df['Datetime'] = pd.to_datetime(df['Datetime'], format='%Y%m%d %H%M%S')
            
            # Sort by datetime
            df = df.sort_values('Datetime')
            
            print(f"Successfully read {len(df):,} rows")
            return df
            
        except Exception as e:
            print(f"Error processing file {filepath}: {str(e)}")
            return pd.DataFrame()
    
    def process_directory(self, input_dir: str, output_dir: str):
        """Process all matching folders in directory"""
        print(f"Scanning directory: {input_dir}")
        
        # Get all matching folders
        folders = [d for d in os.listdir(input_dir) 
                  if os.path.isdir(os.path.join(input_dir, d)) 
                  and d.startswith('DAT_ASCII_') 
                  and '_M1_' in d]
        
        print(f"Found {len(folders)} folders")
        
        if not folders:
            print(f"No matching folders found in {input_dir}")
            return
        
        # Group folders by symbol
        symbol_folders = {}
        for folder in folders:
            try:
                symbol, year = self.extract_year_and_symbol(folder)
                if symbol not in symbol_folders:
                    symbol_folders[symbol] = []
                symbol_folders[symbol].append((folder, year))
            except ValueError as e:
                print(f"Skipping invalid folder {folder}: {str(e)}")
                continue
        
        # Process each symbol's folders
        for symbol, folder_list in symbol_folders.items():
            self.process_symbol_folders(symbol, folder_list, input_dir, output_dir)
    
    def process_symbol_folders(self, symbol: str, folders: List[Tuple[str, str]], input_dir: str, output_dir: str):
        """Process all folders for a single symbol"""
        print(f"\nProcessing data for {symbol}")
        
        # Sort folders by year
        folders.sort(key=lambda x: x[1])  # Sort by year
        
        # Get year range
        start_year = folders[0][1]
        end_year = folders[-1][1]
        
        print(f"Processing years {start_year} to {end_year}")
        
        # Create output filename
        output_file = f"{symbol}_{start_year}-{end_year}.csv"
        output_path = os.path.join(output_dir, output_file)
        
        # Read and concatenate all files
        dfs = []
        total_folders = len(folders)
        
        for i, (folder, year) in enumerate(folders, 1):
            folder_path = os.path.join(input_dir, folder)
            print(f"\nProcessing year {year} ({i}/{total_folders})")
            
            csv_file = self.find_csv_file(folder_path, year, symbol)
            
            if csv_file:
                df = self.read_file(csv_file)
                if not df.empty:
                    dfs.append(df)
            else:
                print(f"CSV file not found in {folder}")
        
        if not dfs:
            print(f"No valid data found for {symbol}")
            return
        
        # Concatenate all dataframes
        print("\nConcatenating all data...")
        final_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates and sort
        print("Removing duplicates and sorting...")
        initial_rows = len(final_df)
        final_df = final_df.drop_duplicates(subset=['Datetime'])
        final_df = final_df.sort_values('Datetime')
        
        # Save to CSV
        print("\nSaving processed data...")
        os.makedirs(output_dir, exist_ok=True)
        final_df.to_csv(output_path, index=False)
        
        print(f"\nProcessed {symbol}:")
        print(f"Total rows: {len(final_df):,}")
        print(f"Duplicates removed: {initial_rows - len(final_df):,}")
        print(f"Date range: {final_df['Datetime'].min()} to {final_df['Datetime'].max()}")
        print(f"Output saved to: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Process and concatenate forex data files')
    parser.add_argument('--input', '-i', required=True, help='Input directory containing forex data folders')
    parser.add_argument('--output', '-o', required=True, help='Output directory for processed files')
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    input_dir = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output)
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    processor = ForexDataProcessor()
    processor.process_directory(input_dir, output_dir)

if __name__ == "__main__":
    main()