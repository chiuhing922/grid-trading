# optimizer.py

from itertools import product
import multiprocessing as mp
from typing import Dict, List, Any, Callable
import pandas as pd
from tqdm import tqdm
import numpy as np
from dataclasses import dataclass
from functools import partial
import config as c
import copy

@dataclass
class OptimizationResult:
    parameters: Dict[str, Any]
    metrics: Dict[str, float]

class GridOptimizer:
    def __init__(self, param_grid: Dict[str, List[Any]], evaluate_func: Callable,
                 n_jobs: int = -1, use_parallel: bool = True):
        """
        Initialize the grid optimizer
        
        Args:
            param_grid: Dictionary of parameters and their possible values
            evaluate_func: Function that takes parameters and returns metrics
            n_jobs: Number of parallel jobs (-1 for all cores)
            use_parallel: Whether to use parallel processing
        """
        self.param_grid = param_grid
        self.evaluate_func = evaluate_func
        self.n_jobs = n_jobs if n_jobs > 0 else mp.cpu_count()
        self.use_parallel = use_parallel
        
        # Set up multiprocessing for macOS
        try:
            mp.set_start_method('fork', force=True)
        except RuntimeError:
            # If 'fork' fails, use 'spawn' (macOS default)
            try:
                mp.set_start_method('spawn', force=True)
            except RuntimeError:
                # Method was already set, that's okay
                pass
        
    def _evaluate_parameter_set(self, params_with_index: tuple) -> OptimizationResult:
        """Evaluate a single parameter set"""
        index, params = params_with_index
        total_combinations = self.total_combinations
        
        try:
            # Print progress in original format
            print(f"\rProgress: {index+1}/{total_combinations} "
                  f"({((index+1)/total_combinations*100):.1f}%)", end="")
            
            metrics = self.evaluate_func(**params)
            return OptimizationResult(parameters=params, metrics=metrics)
        except Exception as e:
            print(f"\nError evaluating parameters {params}: {str(e)}")
            return None
            
    def optimize(self) -> List[OptimizationResult]:
        """Run the optimization process"""
        # Generate all parameter combinations
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        param_combinations = list(product(*param_values))
        
        # Create list of parameter dictionaries
        param_dicts = [
            dict(zip(param_names, combo))
            for combo in param_combinations
        ]
        
        self.total_combinations = len(param_combinations)
        print(f"\nTotal parameter combinations to evaluate: {self.total_combinations}")
        
        results = []
        
        try:
            if self.use_parallel and self.total_combinations > 100:
                # Add index to parameters for progress tracking
                indexed_params = list(enumerate(param_dicts))
                
                # Create process pool with maxtasksperchild to prevent memory issues
                with mp.Pool(processes=self.n_jobs, maxtasksperchild=100) as pool:
                    results = list(pool.imap(self._evaluate_parameter_set, indexed_params))
            else:
                # Sequential processing with original progress format
                for i, params in enumerate(param_dicts):
                    result = self._evaluate_parameter_set((i, params))
                    if result is not None:
                        results.append(result)
                        
        except Exception as e:
            print(f"\nError during optimization: {str(e)}")
            if results:  # Save partial results if we have any
                print("Saving partial results...")
            else:
                print("No results to save")
                
        # Remove None results from failed evaluations
        results = [r for r in results if r is not None]
        print("\nOptimization process completed!")
        return results
    

    # printing on screen and outputting to a file
    def get_best_parameters(self, results: List[OptimizationResult],
                          metric: str = 'net_profit',
                          n_best: int = 1000) -> pd.DataFrame:
        """Get the best parameter combinations based on specified metric"""
        # Convert results to DataFrame
        records = []
        for result in results:
            record = {**result.parameters, **result.metrics}
            records.append(record)
            
        df = pd.DataFrame(records)
        
        # Sort by metric
        df_sorted = df.sort_values(by=metric, ascending=False)
        
        # Print top results in original format
        print("\nTop Parameter Combinations:")
        print(df_sorted.head(10))
        
        return df_sorted.head(n_best)

def evaluate_grid_trading(data: pd.DataFrame, trader, **params) -> Dict[str, float]:
    """
    Evaluate grid trading with given parameters
    Returns dict of evaluation metrics
    """
    # Create a fresh trader instance for each evaluation
    trader = copy.deepcopy(trader)
    
    try:
        result = trader.grid_trade(
            data=data.copy(),  # Use a copy of the data
            symbol='EURUSD',
            **params
        )
        
        gross_profit, net_profit, max_drawdown, total_trade, stop_loss_count = result
        
        return {
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'max_drawdown': max_drawdown,
            'total_trade': total_trade,
            'stop_loss_count': stop_loss_count,
            'profit_drawdown_ratio': abs(net_profit / max_drawdown) if max_drawdown != 0 else float('inf')
        }
    except Exception as e:
        print(f"\nError in grid trading evaluation: {str(e)}")
        # Return a result with all zeros to indicate failure
        return {
            'gross_profit': 0,
            'net_profit': 0,
            'max_drawdown': 0,
            'total_trade': 0,
            'stop_loss_count': 0,
            'profit_drawdown_ratio': 0
        }

def run_optimized_grid_search(data: pd.DataFrame, trader) -> pd.DataFrame:
    """
    Run optimized grid search with parameters from config
    
    Args:
        data: Trading data
        trader: GridTrader instance
        
    Returns:
        DataFrame with optimization results
    """
    import config as c  # Import here to avoid circular imports
    
    # Create evaluation function with fixed data and trader
    eval_func = partial(evaluate_grid_trading, 
                       data=data.copy(),  # Use a copy of the data
                       trader=copy.deepcopy(trader))  # Use a copy of the trader
    
    # Initialize optimizer
    optimizer = GridOptimizer(
        param_grid=c.param_grid,
        evaluate_func=eval_func,
        n_jobs=-1,  # Use all CPU cores
        use_parallel=True
    )
    
    # Run optimization
    results = optimizer.optimize()
    
    # Get best results
    best_results = optimizer.get_best_parameters(
        results,
        metric='net_profit',
        n_best=1000
    )
    
    return best_results