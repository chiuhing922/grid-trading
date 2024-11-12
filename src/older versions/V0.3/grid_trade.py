from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
import pandas as pd
from datetime import datetime
import config as c

class PositionType(Enum):
    LONG = 'long'
    SHORT = 'short'

class ContractQuantity(Enum):
    SINGLE = 'single'
    ALL = 'all'    

@dataclass
class TradingState:
    """Class to hold trading state and configuration"""
    # Configuration parameters
    commission_rate: float
    contract_size: float
    stop_loss_amount: float
    stop_loss_level: int
    step: float
    enable_logging: bool = c.enable_logging
    
    # Trading state
    total_commission: float = 0
    max_drawdown: float = 0
    max_risk: float = 0
    accumulated_profit: float = 0
    accumulated_net_profit: float = 0
    accumulated_contract: int = 0
    position: int = 0
    stop_loss_count: int = 0
    record_no: int = 0
    
    # Trading records
    profit_data: List[Tuple[datetime, float, float]] = None
    win_loss_record: List[int] = None
    
    def __post_init__(self):
        self.profit_data = []
        self.win_loss_record = []
    
    def reset(self):
        """Reset all trading state variables"""
        self.total_commission = 0
        self.max_drawdown = 0
        self.max_risk = 0
        self.accumulated_profit = 0
        self.accumulated_net_profit = 0
        self.accumulated_contract = 0
        self.position = 0
        self.stop_loss_count = 0
        self.record_no = 0
        self.profit_data = []
        self.win_loss_record = []

class GridTrader:
    def __init__(self, commission_rate: float, contract_size: float):
        self.state = TradingState(
            commission_rate=commission_rate,
            contract_size=contract_size,
            stop_loss_amount=0,
            stop_loss_level=0,
            step=0
        )

    def record_max_drawdown(self) -> float:
        if (self.state.accumulated_net_profit < 0 and 
            self.state.accumulated_net_profit < self.state.max_drawdown):
            return self.state.accumulated_net_profit
        return self.state.max_drawdown

    def update_profit_data(self, data: pd.DataFrame) -> None:
        self.state.profit_data.append((
            data['Datetime'].iloc[self.state.record_no-1],
            self.state.accumulated_net_profit,
            self.state.accumulated_profit
        ))

    def log_trade(
        self,
        position_type: PositionType,
        entry_price: float,
        exit_price: float,
        profit: float
    ) -> None:
        if position_type == PositionType.SHORT:
            position_str = f"{position_type.value.capitalize()} contract position: {self.state.position-1}"
        else:
            position_str = f"{position_type.value.capitalize()} contract position: {self.state.position+1}"
            
        if self.state.enable_logging:
            print(f"Record No: {self.state.record_no} Close "
                  f"{position_str} of entry price {entry_price:.5f} "
                  f"at price {exit_price:.5f}")
            print(f"\t\tTrade Profit: {profit:.2f}, "
                  f"Accumulated Net Profit: {self.state.accumulated_net_profit:.2f}")

    def close_positions(
        self,
        data: pd.DataFrame,
        position_stack: List[float],
        current_price: float,
        position_type: PositionType,
        contract_quantity: ContractQuantity,
        is_final_close: bool = False
    ) -> None:
        if not position_stack:
            return
            
        commission = max(self.state.commission_rate * self.state.contract_size * current_price, 2)
        
        if contract_quantity == ContractQuantity.SINGLE:
            self._close_single_position(data, position_stack, current_price, 
                                      position_type, commission)
        else:
            self._close_all_positions(data, position_stack, current_price, 
                                    position_type, commission)

    def _close_single_position(
        self,
        data: pd.DataFrame,
        position_stack: List[float],
        current_price: float,
        position_type: PositionType,
        commission: float
    ) -> None:
        entry_price = position_stack.pop()
        profit = self._calculate_profit(current_price, entry_price, position_type)
        self._update_position_and_stats(profit, commission, position_type)
        self.update_profit_data(data)
        self.log_trade(position_type, entry_price, current_price, profit)

    def _close_all_positions(
        self,
        data: pd.DataFrame,
        position_stack: List[float],
        current_price: float,
        position_type: PositionType,
        commission: float
    ) -> None:
        while position_stack:
            self._close_single_position(data, position_stack, current_price, 
                                      position_type, commission)

    def _calculate_profit(
        self,
        current_price: float,
        entry_price: float,
        position_type: PositionType
    ) -> float:
        if position_type == PositionType.LONG:
            return self.state.contract_size * (current_price - entry_price)
        return self.state.contract_size * (entry_price - current_price)

    def _update_position_and_stats(
        self,
        profit: float,
        commission: float,
        position_type: PositionType
    ) -> None:
        if position_type == PositionType.LONG:
            self.state.position -= 1
        else:
            self.state.position += 1
            
        self.state.accumulated_profit += profit
        self.state.accumulated_net_profit += profit - commission
        self.state.max_drawdown = self.record_max_drawdown()
        self.state.total_commission += commission
        self.state.accumulated_contract += 1

    def grid_trade(
        self,
        data: pd.DataFrame,
        symbol: str,
        stop_loss_amount: float,
        stop_loss_level: int,
        step: float
    ) -> Tuple[float, float, float, int, int]:
        # Initialize trading state
        self.state.reset()
        self.state.stop_loss_amount = stop_loss_amount
        self.state.stop_loss_level = stop_loss_level
        self.state.step = step

        # Initialize trading variables
        current_price = float(data['Close'].values[0])
        reference_price = current_price
        next_long_price = reference_price - step
        next_short_price = reference_price + step

        
        long_stack: List[float] = []
        short_stack: List[float] = []

        # Main trading loop
        for current_price in data['Close'].values:
            if self.state.enable_logging:
                print(f"next_long_price / next_short_price: {next_long_price:,.5f} / {next_short_price:.5f}")

            self.state.record_no += 1
            current_price = float(current_price)
            
            # Handle stop loss conditions
            if self._handle_stop_loss(data, long_stack, short_stack, current_price,
                                    next_long_price, next_short_price):
                stop_loss_triggered +=1
                break

            # Handle normal trading conditions
            if current_price <= next_long_price:
                next_long_price, next_short_price = self._handle_long_entry(
                    data, long_stack, short_stack, current_price, next_long_price,
                    next_short_price)
            elif current_price >= next_short_price:
                next_long_price, next_short_price = self._handle_short_entry(
                    data, long_stack, short_stack, current_price, next_long_price,
                    next_short_price)

        # Close remaining positions
        self._close_remaining_positions(data, long_stack, short_stack, current_price)
        
        return (self.state.accumulated_profit, self.state.accumulated_net_profit,
                self.state.max_drawdown, self.state.accumulated_contract,
                self.state.stop_loss_count)

    def _handle_stop_loss(
        self,
        data: pd.DataFrame,
        long_stack: List[float],
        short_stack: List[float],
        current_price: float,
        next_long_price: float,
        next_short_price: float
    ) -> bool:
        if (self.state.position >= self.state.stop_loss_level and 
            current_price <= next_long_price):
            self.close_positions(data, long_stack, current_price, 
                               PositionType.LONG, ContractQuantity.ALL)
            self.state.stop_loss_count +=1
            return self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount)
            
        elif (self.state.position <= (-1 * self.state.stop_loss_level) and 
              current_price >= next_short_price):
            self.close_positions(data, short_stack, current_price,
                               PositionType.SHORT, ContractQuantity.ALL)
            self.state.stop_loss_count +=1
            return self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount)
            
        return False

    def _handle_long_entry(
        self,
        data: pd.DataFrame,
        long_stack: List[float],
        short_stack: List[float],
        current_price: float,
        next_long_price: float,
        next_short_price: float
    ) -> Tuple[float, float]:
        if self.state.position >= 0:
            self.state.position += 1
            long_stack.append(current_price)
            if self.state.enable_logging:
                print(f"Record No: {self.state.record_no} Open new LONG contract "
                      f"position {self.state.position} of entry price: {current_price}")
        else:
            self.close_positions(data, short_stack, current_price,
                               PositionType.SHORT, ContractQuantity.SINGLE)
        return next_long_price - self.state.step, next_short_price - self.state.step

    def _handle_short_entry(
        self,
        data: pd.DataFrame,
        long_stack: List[float],
        short_stack: List[float],
        current_price: float,
        next_long_price: float,
        next_short_price: float
    ) -> Tuple[float, float]:
        if self.state.position <= 0:
            self.state.position -= 1
            short_stack.append(current_price)
            if self.state.enable_logging:
                print(f"Record No: {self.state.record_no} Open new SHORT contract "
                      f"position {self.state.position} of entry price: {current_price}")
        else:
            self.close_positions(data, long_stack, current_price,
                               PositionType.LONG, ContractQuantity.SINGLE)
        return next_long_price + self.state.step, next_short_price + self.state.step

    def _close_remaining_positions(
        self,
        data: pd.DataFrame,
        long_stack: List[float],
        short_stack: List[float],
        current_price: float
    ) -> None:
        if self.state.position < 0:
            self.close_positions(data, short_stack, current_price,
                               PositionType.SHORT, ContractQuantity.ALL, True)
        elif self.state.position > 0:
            self.close_positions(data, long_stack, current_price,
                               PositionType.LONG, ContractQuantity.ALL, True)

# Example usage:
"""
trader = GridTrader(commission_rate=0.0001, contract_size=100)
results = trader.grid_trade(
    data=your_data,
    symbol="BTC",
    stop_loss_amount=1000,
    stop_loss_level=5,
    step=100
)
"""