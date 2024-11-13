from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Dict
import pandas as pd
from datetime import datetime
import config as c
import numpy as np
from volatility import VolatilityManager

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


    # Add volatility parameters
    volatility_lookback: int = c.volatility_lookback
    grid_volatility_factor: float = c.grid_volatility_factor
    
    # Add grid tracking
    current_grid_step: float = 0.0

    # New configuration fields
    account_balance: float = c.account_balance
    risk_per_trade: float = c.risk_per_trade
    trailing_stop: bool = c.trailing_stop
    trailing_stop_distance: float = c.trailing_stop_distance
    max_position_holding_days: int = c.max_position_holding_days 
    
    # Trading state
    total_commission: float = 0
    total_spread_cost: float = 0  # Added spread cost tracking
    total_rollover: float = 0
    max_drawdown: float = 0
    max_risk: float = 0
    accumulated_profit: float = 0
    accumulated_net_profit: float = 0
    accumulated_contract: int = 0
    position: int = 0
    stop_loss_count: int = 0
    record_no: int = 0
    
    # Trading records - initialize using field with default_factory
    profit_data: List[Tuple[datetime, float, float, datetime, datetime]] = field(default_factory=list)
    win_loss_record: List[int] = field(default_factory=list)
    open_positions_time: Dict[float, datetime] = field(default_factory=dict)
    highest_highs: Dict[float, float] = field(default_factory=dict)
    lowest_lows: Dict[float, float] = field(default_factory=dict)

    # Calculate max loss per trade based on account balance and risk percentage
    @property
    def max_loss_per_trade(self) -> float:
        """Maximum loss allowed per trade based on risk percentage"""
        return self.account_balance * self.risk_per_trade
    
    @property
    def total_costs(self) -> float:
        """Calculate total trading costs including commission, spread, and rollover"""
        return self.total_commission + self.total_spread_cost + self.total_rollover  # rollover express in cost format, -ve means credit or offset the trade_costs
    

    def __post_init__(self):
        self.profit_data = []
        self.win_loss_record = []
        self.open_positions_time = {}
        self.highest_highs = {}
        self.lowest_lows = {}
    
    def reset(self):
        """Reset all trading state variables"""
        self.total_commission = 0
        self.total_spread_cost = 0  # Reset spread cost
        self.total_rollover = 0     # Reset rollover
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
        self.open_positions_time.clear()
        self.highest_highs.clear()
        self.lowest_lows.clear()

    def log_costs(self) -> None:
        """Log all trading costs"""
        if self.enable_logging:
            print(f"\nTrading Costs Summary:")
            print(f"Commission: ${self.total_commission:,.2f}")
            print(f"Spread Cost: ${self.total_spread_cost:,.2f}")
            print(f"Rollover: ${self.total_rollover:,.2f}")
            print(f"Total Costs: ${self.total_costs:,.2f}")

class TradingCosts:
    def __init__(self, spread_config: Dict[str, float] = None):
        """
        Initialize trading costs calculator
        
        Args:
            spread_config: Dictionary of currency pairs and their typical spreads
                         e.g., {'EURUSD': 0.00001}
        """
        self.spread_typical = spread_config if spread_config else {
            'EURUSD': 0.00001  # Default 0.1 pip typical spread
        }
    
    def calculate_spread_cost(self, symbol: str, contract_size: float, position_type: str) -> float:
        spread = self.spread_typical.get(symbol, 0.00002)  # Default 0.2 pips if unknown
        spread_cost = spread * contract_size
        return spread_cost
        
        # For long positions: Buy at ask (higher), sell at bid (lower)
        # For short positions: Sell at bid (lower), buy at ask (higher)
        return spread_cost

    
class RolloverCosts:
    def __init__(self, rates: Dict[str, float] = None):
        """
        Initialize rollover costs calculator
        
        Args:
            rates: Dictionary of currencies and their interest rates
                  e.g., {'USD': 0.0525, 'EUR': 0.0400}
        """
        # Use passed rates or get from config, or use defaults
        self.rates = rates if rates else (
            c.interest_rates if hasattr(c, 'interest_rates') else {
                'USD': 0.0525,  # Default 5.25% Fed rate
                'EUR': 0.0400,  # Default 4.00% ECB rate
            }
        )

    def calculate_rollover(self, 
                          symbol: str,
                          position_type: str,
                          contract_size: float,
                          entry_price: float,
                          holding_days: int) -> float:
        base_curr = symbol[:3]
        quote_curr = symbol[3:]
        
        base_rate = self.rates.get(base_curr, 0)
        quote_rate = self.rates.get(quote_curr, 0)
        
        if position_type == 'long':
            rate_diff = quote_rate - base_rate
        else:
            rate_diff = base_rate - quote_rate
            
        daily_rate = rate_diff / 365
        position_value = contract_size * entry_price
        rollover = position_value * daily_rate * holding_days
        
        weekend_multiplier = holding_days // 7 * 2
        if holding_days == 0:
            rollover = 0
        else:
            rollover *= (holding_days + weekend_multiplier) / holding_days
        
        return rollover   # return of rollover cost, if it's -ve then it's a credit

class GridTrader:
    def __init__(self):
        """Initialize GridTrader with configuration from config.py"""
        # Get parameters from config
        trade_params = c.get_trade_params()
        cost_params = c.get_cost_params()
        
        self.state = TradingState(
            commission_rate=cost_params['commission_rate'],
            contract_size=c.contract_size,
            stop_loss_amount=0,
            stop_loss_level=0,
            step=0,
            account_balance=trade_params['account_balance'],
            risk_per_trade=trade_params['risk_per_trade'],
            trailing_stop=trade_params['trailing_stop'],
            trailing_stop_distance=trade_params['trailing_stop_distance'],
            max_position_holding_days=trade_params['max_position_holding_days']
        )
        
        # Initialize cost calculators with parameters from config
        self.costs = TradingCosts(spread_config=cost_params['spread_typical'])
        self.rollover = RolloverCosts(rates=cost_params['interest_rates'])

        # Initialize volatility management
        self.volatility_manager = VolatilityManager()
        self._cached_atr: Optional[np.ndarray] = None
        self._current_lookback: Optional[int] = None
    def calculate_volatility(self, data: pd.DataFrame, lookback: int = None) -> float:
        """
        Get volatility (ATR) for current position using cached values
        """
        if lookback is None:
            lookback = self.state.volatility_lookback
            
        if self.state.record_no < 2:
            return 0.0
            
        # Check if we need to recalculate ATR series
        if self._cached_atr is None or self._current_lookback != lookback:
            self._cached_atr = self.volatility_manager.calculate_atr_series(data, lookback)
            self._current_lookback = lookback
            
        # Return ATR for current position
        return self._cached_atr[self.state.record_no - 1]

    def calculate_dynamic_step(self, data: pd.DataFrame) -> float:
        """
        Calculate dynamic grid step size based on cached volatility
        """
        # Get base step from state
        base_step = self.state.step
        
        # Get volatility from cache
        volatility = self.calculate_volatility(data)
        
        if volatility == 0:
            return base_step
            
        # Get current price
        current_price = float(data['Close'].iloc[self.state.record_no-1])
        
        # Calculate volatility ratio (volatility as percentage of price)
        volatility_ratio = volatility / current_price
        
        # Adjust step size based on volatility
        volatility_factor = self.state.grid_volatility_factor
        adjusted_step = base_step * (1 + volatility_ratio * volatility_factor)
        
        # Apply limits to prevent extreme step sizes
        min_step = base_step * 0.5
        max_step = base_step * 2.0
        
        # Round to 5 decimal places (for FX)
        adjusted_step = round(np.clip(adjusted_step, min_step, max_step), 5)
        
        if self.state.enable_logging:
            print(f"\nDynamic Grid Calculation:")
            print(f"Base Step: {base_step:.5f}")
            print(f"Volatility: {volatility:.5f}")
            print(f"Volatility Ratio: {volatility_ratio:.5f}")
            print(f"Adjusted Step: {adjusted_step:.5f}")
            
        return adjusted_step        

    def _check_position_stops(
        self,
        data: pd.DataFrame,
        long_stack: List[float],
        short_stack: List[float],
        current_price: float
    ) -> bool:
        positions_to_close = []
        
        # Check long positions
        for entry_price in long_stack:
            unrealized_loss = (current_price - entry_price) * self.state.contract_size
            
            # Regular stop loss check using property
            max_loss = -self.state.max_loss_per_trade    # Negative because we're checking for loss
            # Only check for stop loss if we're actually losing money
            if unrealized_loss < max_loss:  # Remove abs() and compare directly
                if self.state.enable_logging:
                    print(f"Long position stop loss triggered:"
                        f"\nEntry price: {entry_price:.5f}"
                        f"\nCurrent price: {current_price:.5f}"
                        f"\nUnrealized loss: ${unrealized_loss:.2f}"
                        f"\nMax loss allowed: ${-max_loss:.2f}")
                positions_to_close.append(('long', entry_price))
                continue

            # Add trailing stop check for longs
            if self.state.trailing_stop:
                if entry_price not in self.state.highest_highs:
                    self.state.highest_highs[entry_price] = current_price
                elif current_price > self.state.highest_highs[entry_price]:
                    self.state.highest_highs[entry_price] = current_price
                elif (self.state.highest_highs[entry_price] - current_price 
                      >= self.state.trailing_stop_distance):
                    if self.state.enable_logging:
                        print(f"Long position trailing stop triggered:"
                              f"\nEntry price: {entry_price:.5f}"
                              f"\nCurrent price: {current_price:.5f}"
                              f"\nHighest price: ${self.state.highest_highs[entry_price]:.5f}"
                              f"\nTrailing distance: ${self.state.trailing_stop_distance:.5f}")
                    positions_to_close.append(('long', entry_price))

        # Check short positions - UNINDENTED to be at same level as long positions loop
        for entry_price in short_stack:
            unrealized_loss = (entry_price - current_price) * self.state.contract_size
            max_loss = -self.state.max_loss_per_trade  # Negative because we're checking for loss
            
            # Only check for stop loss if we're actually losing money
            if unrealized_loss < max_loss:  # Remove abs() and compare directly
                if self.state.enable_logging:
                    print(f"Short position stop loss triggered:"
                        f"\nEntry price: {entry_price:.5f}"
                        f"\nCurrent price: {current_price:.5f}"
                        f"\nUnrealized loss: ${unrealized_loss:.2f}"
                        f"\nMax loss allowed: ${-max_loss:.2f}")
                positions_to_close.append(('short', entry_price))
                continue
            
            # Trailing stop check for shorts
            if self.state.trailing_stop:
                if entry_price not in self.state.lowest_lows:
                    self.state.lowest_lows[entry_price] = current_price
                elif current_price < self.state.lowest_lows[entry_price]:
                    self.state.lowest_lows[entry_price] = current_price
                elif (current_price - self.state.lowest_lows[entry_price] 
                    >= self.state.trailing_stop_distance):
                    positions_to_close.append(('short', entry_price))
        
        # Close positions that hit stops - UNINDENTED to be outside both loops
        for position_type, entry_price in positions_to_close:
            if position_type == 'long':
                self.close_positions(
                    data=data,
                    position_stack=[entry_price],
                    current_price=current_price,
                    position_type=PositionType.LONG,
                    contract_quantity=ContractQuantity.SINGLE
                )
                long_stack.remove(entry_price)
                if entry_price in self.state.highest_highs:
                    del self.state.highest_highs[entry_price]
            else:
                self.close_positions(
                    data=data,
                    position_stack=[entry_price],
                    current_price=current_price,
                    position_type=PositionType.SHORT,
                    contract_quantity=ContractQuantity.SINGLE
                )
                short_stack.remove(entry_price)
                if entry_price in self.state.lowest_lows:
                    del self.state.lowest_lows[entry_price]
        
        return len(positions_to_close) > 0  # UNINDENTED to be at end of function


    def record_max_drawdown(self) -> float:
        if (self.state.accumulated_net_profit < 0 and 
            self.state.accumulated_net_profit < self.state.max_drawdown):
            return self.state.accumulated_net_profit
        return self.state.max_drawdown
    '''
    def update_profit_data(self, data: pd.DataFrame) -> None:
        self.state.profit_data.append((
            data['Datetime'].iloc[self.state.record_no-1],
            self.state.accumulated_net_profit,
            self.state.accumulated_profit
        ))
    '''
    def update_profit_data(self, data: pd.DataFrame, profit: float, net_profit: float,
                        entry_time: datetime, exit_time: datetime) -> None:
        """Update profit tracking data"""
        self.state.profit_data.append((
            exit_time,
            profit,
            net_profit,
            entry_time,
            exit_time
        ))        
        
    def log_grid_prices(self, data: pd.DataFrame, current_price: float, next_long_price: float, next_short_price: float) -> None:
        """Log grid prices with timestamp"""
        if self.state.enable_logging:
            current_time = data['Datetime'].iloc[self.state.record_no-1]
            print(f"Current Price: {current_price:.5f}:  Dynamic Step Size: {self.state.current_grid_step:.5f}")
            print(f"[{current_time}] Grid Prices - Next Long: {next_long_price:.5f} / Next Short: {next_short_price:.5f}")

    def log_position_open(self, data: pd.DataFrame, position: int, entry_price: float, position_type: str) -> None:
        """Log position opening with timestamp"""
        if self.state.enable_logging:
            current_time = data['Datetime'].iloc[self.state.record_no-1]
            print(f"[{current_time}] Record No: {self.state.record_no} "
                  f"Open new {position_type.upper()} contract position {position} "
                  f"of entry price: {entry_price:.5f}")
            
    def log_trade(self, data: pd.DataFrame, position_type: PositionType, 
                  entry_price: float, exit_price: float, profit: float) -> None:
        """Log trade details with timestamp"""
        if self.state.enable_logging:
            current_time = data['Datetime'].iloc[self.state.record_no-1]
            if position_type == PositionType.SHORT:
                position_str = f"{position_type.value.capitalize()} contract position: {self.state.position-1}"
            else:
                position_str = f"{position_type.value.capitalize()} contract position: {self.state.position+1}"
            
            print(f"[{current_time}] Record No: {self.state.record_no} Close "
                  f"{position_str} of entry price {entry_price:.5f} "
                  f"at price {exit_price:.5f}")
            print(f"[{current_time}]\t\tTrade Profit: ${profit:.2f}, "
                  f"Accumulated Net Profit: ${self.state.accumulated_net_profit:.2f}")

    def close_positions(
        self,
        data: pd.DataFrame,
        position_stack: List[float],
        current_price: float,
        position_type: PositionType,
        contract_quantity: ContractQuantity,
        next_long_price: float = None,
        next_short_price: float = None,
        is_final_close: bool = False
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Close positions with grid adjustment tracking
        Returns final grid levels after all closures
        """
        if not position_stack:
            return next_long_price, next_short_price
                
        commission = max(self.state.commission_rate * self.state.contract_size * current_price, 2)
        final_grid_levels = (next_long_price, next_short_price)
        
        if contract_quantity == ContractQuantity.SINGLE:
            final_grid_levels = self._close_single_position(
                data=data,
                position_stack=position_stack,
                current_price=current_price,
                position_type=position_type,
                commission=commission,
                next_long_price=next_long_price,
                next_short_price=next_short_price
            )
        else:
            while position_stack:
                final_grid_levels = self._close_single_position(
                    data=data,
                    position_stack=position_stack,
                    current_price=current_price,
                    position_type=position_type,
                    commission=commission,
                    next_long_price=next_long_price,
                    next_short_price=next_short_price
                )
                # Update grid levels for next iteration
                if final_grid_levels[0] is not None:
                    next_long_price, next_short_price = final_grid_levels
        
        return final_grid_levels

    def _close_single_position(
        self,
        data: pd.DataFrame,
        position_stack: List[float],
        current_price: float,
        position_type: PositionType,
        commission: float,
        next_long_price: float = None,
        next_short_price: float = None
    ) -> Tuple[Optional[float], Optional[float]]:
            """
            Close a single position with dynamic grid adjustment
            Returns new grid levels if provided with current levels
            """
            # Calculate dynamic step for grid adjustment
            dynamic_step = self.calculate_dynamic_step(data)
            self.state.current_grid_step = dynamic_step

            # get position detail
            entry_price = position_stack.pop()
            entry_time = self.state.open_positions_time.pop(entry_price, None)
            exit_time = data['Datetime'].iloc[self.state.record_no-1]  # Get position exit time

            # Calculate base profit
            profit = self._calculate_profit(current_price, entry_price, position_type)  

            # Protect against None entry_time
            holding_days = 0
            if entry_time is not None:
                holding_days = (exit_time - entry_time).days

            # Calculate spread cost
            spread_cost = self.costs.calculate_spread_cost(
                symbol='EURUSD',  # You might want to make this configurable
                contract_size=self.state.contract_size,
                position_type=position_type.value
            )


            # Calculate rollover
            rollover = self.rollover.calculate_rollover(
                symbol='EURUSD',
                position_type=position_type.value,
                contract_size=self.state.contract_size,
                entry_price=entry_price,
                holding_days=max(holding_days, 0)  # Ensure non-negative
            )


            # Calculate net profit for this trade
            trade_costs = commission + spread_cost - rollover
            net_profit = profit - trade_costs

            # Record accumulated profit data
            self._update_position_and_stats(
                profit=profit,
                commission=commission,
                spread_cost=spread_cost,
                rollover=rollover,
                position_type=position_type
            )

            # Update profit data with this trade's results
            self.update_profit_data(
                data=data,
                profit=profit,
                net_profit=net_profit,
                entry_time=entry_time,
                exit_time=exit_time
            )
            self.log_trade(data, position_type, entry_price, current_price, profit)  # Added 'data' parameter
            
            # Use dynamic step for grid adjustment

            # Handle grid level adjustments if grid levels are provided
            new_grid_levels = None
            if next_long_price is not None and next_short_price is not None:
                if position_type == PositionType.LONG:
                    # Closing long position should move grid up (like opening short)
                    new_grid_levels = (
                        next_long_price + dynamic_step,
                        next_short_price + dynamic_step
                    )
                else:
                    # Closing short position should move grid down (like opening long)
                    new_grid_levels = (
                        next_long_price - dynamic_step,
                        next_short_price - dynamic_step
                    )

            # Enhanced logging
            if self.state.enable_logging:
                print(f"\nPosition Close Details:")
                print(f"Type: {position_type.value.upper()}")
                print(f"Entry Price: {entry_price:.5f}")
                print(f"Exit Price: {current_price:.5f}")
                print(f"Dynamic Step: {dynamic_step:.5f}")
                print(f"Profit: ${profit:.2f}")
                print(f"Net Profit: ${net_profit:.2f}")
                if new_grid_levels:
                    print(f"Previous Grid Levels:")
                    print(f"  Long Entry: {next_long_price:.5f}")
                    print(f"  Short Entry: {next_short_price:.5f}")
                    print(f"New Grid Levels:")
                    print(f"  Long Entry: {new_grid_levels[0]:.5f}")
                    print(f"  Short Entry: {new_grid_levels[1]:.5f}")

            # Return new grid levels if they were calculated
            return new_grid_levels if new_grid_levels else (None, None)


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
        spread_cost: float,
        rollover: float,
        position_type: PositionType
    ) -> None:
        """Update position and profit statistics"""
    # Update position count
        if position_type == PositionType.LONG:
            self.state.position -= 1
        else:
            self.state.position += 1
        
        self.state.total_commission += commission
        self.state.total_spread_cost += spread_cost
        self.state.total_rollover += rollover

        # Calculate net profit for this trade
        trade_costs = commission + spread_cost + rollover    # rollover is already in cost format, -ve means credit or offset the trade_costs
        net_profit = profit - trade_costs

        # Calculate net profit once using the property
        self.state.accumulated_profit += profit
        self.state.accumulated_net_profit += net_profit

        self.state.max_drawdown = self.record_max_drawdown()
        self.state.accumulated_contract += 1
    

    def grid_trade(
        self,
        data: pd.DataFrame,
        symbol: str,
        stop_loss_amount: float,
        stop_loss_level: int,
        step: float,
        volatility_factor: float = None,  # Add new parameter with default
        volatility_lookback: int = None
    ) -> Tuple[float, float, float, int, int]:
        # Initialize trading state
        self.state.reset()
        self.state.stop_loss_amount = stop_loss_amount
        self.state.stop_loss_level = stop_loss_level
        self.state.step = step

        # Set volatility parameters if provided
        if volatility_factor is not None:
            self.state.grid_volatility_factor = volatility_factor
        if volatility_lookback is not None:
            self.state.volatility_lookback = volatility_lookback

        # Pre-calculate volatility series if using dynamic grid
        if self.state.grid_volatility_factor > 0:
            self._cached_atr = self.volatility_manager.calculate_atr_series(
                data, self.state.volatility_lookback
            )
            self._current_lookback = self.state.volatility_lookback

        # Initialize trading variables
        current_price = float(data['Close'].values[0])
        reference_price = current_price
        next_long_price = reference_price - step
        next_short_price = reference_price + step

        long_stack: List[float] = []
        short_stack: List[float] = []

        if self.state.enable_logging:
            print(f"\nInitial Grid Levels:")
            print(f"Reference Price: {reference_price:.5f}")
            print(f"Next Long Price: {next_long_price:.5f}")
            print(f"Next Short Price: {next_short_price:.5f}")


        # Main trading loop
        for current_price in data['Close'].values:
            self.state.record_no += 1
            current_price = float(current_price)

            # Log grid prices with timestamp
            self.log_grid_prices(data, current_price, next_long_price, next_short_price)
            
            # Check per-trade stops before regular grid logic
            stops_triggered = self._check_position_stops(
                data, long_stack, short_stack, current_price
            )

            # Handle global stop loss conditions
            if self._handle_stop_loss(data, long_stack, short_stack, current_price,
                                    next_long_price, next_short_price):
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
        """
        Handle stop loss conditions for the trading system.
        Returns True if trading should stop due to hitting loss limit.
        """
        # First check if we've already exceeded our maximum loss limit
        if self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount):
            if self.state.enable_logging:
                print(f"\nStop Loss Limit Exceeded:")
                print(f"Current Loss: ${self.state.accumulated_net_profit:,.2f}")
                print(f"Stop Loss Limit: ${self.state.stop_loss_amount:,.2f}")
            return True

        # Check long positions stop loss condition
        if (self.state.position >= self.state.stop_loss_level and 
            current_price <= next_long_price):
            if self.state.enable_logging:
                print(f"\nClosing long positions due to stop loss level:")
                print(f"Current Position: {self.state.position}")
                print(f"Stop Loss Level: {self.state.stop_loss_level}")
                
            # Close positions
            self.close_positions(
                data=data,
                position_stack=long_stack,
                current_price=current_price,
                position_type=PositionType.LONG,
                contract_quantity=ContractQuantity.ALL
            )
            self.state.stop_loss_count += 1
            
            # Check if closing positions caused us to exceed loss limit
            return self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount)

        # Check short positions stop loss condition
        elif (self.state.position <= (-1 * self.state.stop_loss_level) and 
            current_price >= next_short_price):
            if self.state.enable_logging:
                print(f"\nClosing short positions due to stop loss level:")
                print(f"Current Position: {self.state.position}")
                print(f"Stop Loss Level: {self.state.stop_loss_level}")
                
            # Close positions
            self.close_positions(
                data=data,
                position_stack=short_stack,
                current_price=current_price,
                position_type=PositionType.SHORT,
                contract_quantity=ContractQuantity.ALL
            )
            self.state.stop_loss_count += 1
            
            # Check if closing positions caused us to exceed loss limit
            return self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount)

        # No stop loss conditions met
        return False

    def _handle_stop_loss(
        self,
        data: pd.DataFrame,
        long_stack: List[float],
        short_stack: List[float],
        current_price: float,
        next_long_price: float,
        next_short_price: float
    ) -> bool:
        """
        Handle stop loss conditions for the trading system.
        Returns True if trading should stop due to hitting loss limit.
        """
        # First check if we've already exceeded our maximum loss limit
        if self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount):
            if self.state.enable_logging:
                print(f"\nStop Loss Limit Exceeded:")
                print(f"Current Loss: ${self.state.accumulated_net_profit:,.2f}")
                print(f"Stop Loss Limit: ${self.state.stop_loss_amount:,.2f}")
            return True

        # Check long positions stop loss condition
        if (self.state.position >= self.state.stop_loss_level and 
            current_price <= next_long_price):
            if self.state.enable_logging:
                print(f"\nClosing long positions due to stop loss level:")
                print(f"Current Position: {self.state.position}")
                print(f"Stop Loss Level: {self.state.stop_loss_level}")
                
            # Close positions
            self.close_positions(
                data=data,
                position_stack=long_stack,
                current_price=current_price,
                position_type=PositionType.LONG,
                contract_quantity=ContractQuantity.ALL
            )
            self.state.stop_loss_count += 1
            
            # Check if closing positions caused us to exceed loss limit
            return self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount)

        # Check short positions stop loss condition
        elif (self.state.position <= (-1 * self.state.stop_loss_level) and 
            current_price >= next_short_price):
            if self.state.enable_logging:
                print(f"\nClosing short positions due to stop loss level:")
                print(f"Current Position: {self.state.position}")
                print(f"Stop Loss Level: {self.state.stop_loss_level}")
                
            # Close positions
            self.close_positions(
                data=data,
                position_stack=short_stack,
                current_price=current_price,
                position_type=PositionType.SHORT,
                contract_quantity=ContractQuantity.ALL
            )
            self.state.stop_loss_count += 1
            
            # Check if closing positions caused us to exceed loss limit
            return self.state.accumulated_net_profit < (-1 * self.state.stop_loss_amount)

        # No stop loss conditions met
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
        dynamic_step = self.calculate_dynamic_step(data)
        self.state.current_grid_step = dynamic_step

        if self.state.position >= 0:
            # Opening new long position
            self.state.position += 1
            long_stack.append(current_price)
            entry_time = data.iloc[self.state.record_no]['Datetime']
            self.state.open_positions_time[current_price] = entry_time
            
            if self.state.enable_logging:
                print(f"\nOpening Long Position:")
                print(f"Record No: {self.state.record_no}")
                print(f"Position Count: {self.state.position}")
                print(f"Entry Price: {current_price:.5f}")
                print(f"Dynamic Step: {dynamic_step:.5f}")
                print(f"Previous Grid Levels:")
                print(f"  Long Entry: {next_long_price:.5f}")
                print(f"  Short Entry: {next_short_price:.5f}")
                print(f"New Grid Levels:")
                print(f"  Long Entry: {(next_long_price - dynamic_step):.5f}")
                print(f"  Short Entry: {(next_short_price - dynamic_step):.5f}")
        else:
            # Closing existing short position
            if self.state.enable_logging:
                print(f"\nClosing Short Position:")
                print(f"Record No: {self.state.record_no}")
                print(f"Current Position: {self.state.position}")
                print(f"Close Price: {current_price:.5f}")
                print(f"Dynamic Step: {dynamic_step:.5f}")
                print(f"Previous Grid Levels:")
                print(f"  Long Entry: {next_long_price:.5f}")
                print(f"  Short Entry: {next_short_price:.5f}")
                print(f"New Grid Levels:")
                print(f"  Long Entry: {(next_long_price - dynamic_step):.5f}")
                print(f"  Short Entry: {(next_short_price - dynamic_step):.5f}")
                
            self.close_positions(
                data=data,
                position_stack=short_stack,
                current_price=current_price,
                position_type=PositionType.SHORT,
                contract_quantity=ContractQuantity.SINGLE
            )
        
        # Move grid down in both cases (opening long or closing short)
        return next_long_price - dynamic_step, next_short_price - dynamic_step

    def _handle_short_entry(
        self,
        data: pd.DataFrame,
        long_stack: List[float],
        short_stack: List[float],
        current_price: float,
        next_long_price: float,
        next_short_price: float
    ) -> Tuple[float, float]:
        # Calculate dynamic step size
        dynamic_step = self.calculate_dynamic_step(data)
        self.state.current_grid_step = dynamic_step

        if self.state.position <= 0:
            # Opening new short position
            self.state.position -= 1
            short_stack.append(current_price)
            entry_time = data.iloc[self.state.record_no]['Datetime']
            self.state.open_positions_time[current_price] = entry_time
            
            if self.state.enable_logging:
                print(f"\nOpening Short Position:")
                print(f"Record No: {self.state.record_no}")
                print(f"Position Count: {self.state.position}")
                print(f"Entry Price: {current_price:.5f}")
                print(f"Dynamic Step: {dynamic_step:.5f}")
                print(f"Previous Grid Levels:")
                print(f"  Long Entry: {next_long_price:.5f}")
                print(f"  Short Entry: {next_short_price:.5f}")
                print(f"New Grid Levels:")
                print(f"  Long Entry: {(next_long_price + dynamic_step):.5f}")
                print(f"  Short Entry: {(next_short_price + dynamic_step):.5f}")
        else:
            # Closing existing long position
            if self.state.enable_logging:
                print(f"\nClosing Long Position:")
                print(f"Record No: {self.state.record_no}")
                print(f"Current Position: {self.state.position}")
                print(f"Close Price: {current_price:.5f}")
                print(f"Dynamic Step: {dynamic_step:.5f}")
                print(f"Previous Grid Levels:")
                print(f"  Long Entry: {next_long_price:.5f}")
                print(f"  Short Entry: {next_short_price:.5f}")
                print(f"New Grid Levels:")
                print(f"  Long Entry: {(next_long_price + dynamic_step):.5f}")
                print(f"  Short Entry: {(next_short_price + dynamic_step):.5f}")
                
            self.close_positions(
                data=data,
                position_stack=long_stack,
                current_price=current_price,
                position_type=PositionType.LONG,
                contract_quantity=ContractQuantity.SINGLE
            )
        
        # Move grid up in both cases (opening short or closing long)
        return next_long_price + dynamic_step, next_short_price + dynamic_step

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