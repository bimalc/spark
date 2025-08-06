"""
Alpaca Trading API - Multi-Leg Options Trading with Stop Loss and Take Profit

This example demonstrates how to:
1. Create multi-leg options strategies (spreads, straddles, strangles)
2. Set stop loss and take profit orders
3. Monitor positions and manage risk
4. Handle different order types and time-in-force settings

Requirements:
- Alpaca account with options trading enabled
- API keys configured in environment variables
- Sufficient buying power for the strategies
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import json

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest, 
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    GetOrdersRequest
)
from alpaca.trading.enums import (
    OrderSide, 
    TimeInForce, 
    OrderType,
    OrderStatus
)
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiLegOptionsTrader:
    """
    A class to handle multi-leg options trading with stop loss and take profit
    """
    
    def __init__(self):
        """Initialize the trading client and data client"""
        # Get API credentials from environment variables
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        
        # Initialize clients
        self.trading_client = TradingClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
            paper=True  # Use paper trading
        )
        
        self.data_client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.secret_key
        )
        
        logger.info("MultiLegOptionsTrader initialized successfully")
    
    def get_account_info(self) -> Dict:
        """Get current account information"""
        account = self.trading_client.get_account()
        return {
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value),
            'equity': float(account.equity),
            'daytrade_count': account.daytrade_count
        }
    
    def create_bull_call_spread(
        self, 
        symbol: str, 
        expiration_date: str,
        buy_strike: float,
        sell_strike: float,
        quantity: int,
        stop_loss_pct: float = 0.25,
        take_profit_pct: float = 0.50
    ) -> Dict:
        """
        Create a bull call spread strategy
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            expiration_date: Option expiration date (YYYY-MM-DD)
            buy_strike: Strike price for the long call
            sell_strike: Strike price for the short call
            quantity: Number of contracts
            stop_loss_pct: Stop loss percentage (0.25 = 25% loss)
            take_profit_pct: Take profit percentage (0.50 = 50% profit)
        """
        
        # Option symbols for the spread
        buy_call_symbol = f"{symbol}{expiration_date.replace('-', '')}C{buy_strike:08.0f}"
        sell_call_symbol = f"{symbol}{expiration_date.replace('-', '')}C{sell_strike:08.0f}"
        
        logger.info(f"Creating bull call spread for {symbol}")
        logger.info(f"Buy call: {buy_call_symbol} at strike {buy_strike}")
        logger.info(f"Sell call: {sell_call_symbol} at strike {sell_strike}")
        
        # Calculate max loss and max profit
        max_loss = (sell_strike - buy_strike) * 100 * quantity
        max_profit = (sell_strike - buy_strike) * 100 * quantity
        
        # Create the spread orders
        orders = []
        
        try:
            # Buy the lower strike call
            buy_order = MarketOrderRequest(
                symbol=buy_call_symbol,
                qty=quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            buy_response = self.trading_client.submit_order(buy_order)
            orders.append({
                'order_id': buy_response.id,
                'symbol': buy_call_symbol,
                'side': 'BUY',
                'quantity': quantity,
                'status': buy_response.status
            })
            
            logger.info(f"Buy order submitted: {buy_response.id}")
            
            # Sell the higher strike call
            sell_order = MarketOrderRequest(
                symbol=sell_call_symbol,
                qty=quantity,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            sell_response = self.trading_client.submit_order(sell_order)
            orders.append({
                'order_id': sell_response.id,
                'symbol': sell_call_symbol,
                'side': 'SELL',
                'quantity': quantity,
                'status': sell_response.status
            })
            
            logger.info(f"Sell order submitted: {sell_response.id}")
            
            # Wait for orders to fill
            self._wait_for_orders_to_fill([buy_response.id, sell_response.id])
            
            # Set stop loss and take profit orders
            stop_loss_order = self._set_stop_loss_for_spread(
                symbol, buy_call_symbol, sell_call_symbol, 
                quantity, max_loss, stop_loss_pct
            )
            
            take_profit_order = self._set_take_profit_for_spread(
                symbol, buy_call_symbol, sell_call_symbol,
                quantity, max_profit, take_profit_pct
            )
            
            return {
                'strategy': 'bull_call_spread',
                'symbol': symbol,
                'orders': orders,
                'max_loss': max_loss,
                'max_profit': max_profit,
                'stop_loss_order': stop_loss_order,
                'take_profit_order': take_profit_order,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error creating bull call spread: {e}")
            # Cancel any open orders
            self._cancel_orders([order['order_id'] for order in orders])
            raise
    
    def create_iron_condor(
        self,
        symbol: str,
        expiration_date: str,
        sell_put_strike: float,
        buy_put_strike: float,
        sell_call_strike: float,
        buy_call_strike: float,
        quantity: int,
        stop_loss_pct: float = 0.25,
        take_profit_pct: float = 0.50
    ) -> Dict:
        """
        Create an iron condor strategy
        
        Args:
            symbol: Stock symbol
            expiration_date: Option expiration date
            sell_put_strike: Strike price for the short put
            buy_put_strike: Strike price for the long put
            sell_call_strike: Strike price for the short call
            buy_call_strike: Strike price for the long call
            quantity: Number of contracts
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        
        # Option symbols
        sell_put_symbol = f"{symbol}{expiration_date.replace('-', '')}P{sell_put_strike:08.0f}"
        buy_put_symbol = f"{symbol}{expiration_date.replace('-', '')}P{buy_put_strike:08.0f}"
        sell_call_symbol = f"{symbol}{expiration_date.replace('-', '')}C{sell_call_strike:08.0f}"
        buy_call_symbol = f"{symbol}{expiration_date.replace('-', '')}C{buy_call_strike:08.0f}"
        
        logger.info(f"Creating iron condor for {symbol}")
        
        # Calculate max loss and max profit
        put_spread_width = sell_put_strike - buy_put_strike
        call_spread_width = buy_call_strike - sell_call_strike
        max_loss = max(put_spread_width, call_spread_width) * 100 * quantity
        max_profit = (sell_call_strike - sell_put_strike) * 100 * quantity
        
        orders = []
        
        try:
            # Sell put
            sell_put_order = MarketOrderRequest(
                symbol=sell_put_symbol,
                qty=quantity,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            sell_put_response = self.trading_client.submit_order(sell_put_order)
            orders.append({
                'order_id': sell_put_response.id,
                'symbol': sell_put_symbol,
                'side': 'SELL',
                'quantity': quantity,
                'status': sell_put_response.status
            })
            
            # Buy put
            buy_put_order = MarketOrderRequest(
                symbol=buy_put_symbol,
                qty=quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            buy_put_response = self.trading_client.submit_order(buy_put_order)
            orders.append({
                'order_id': buy_put_response.id,
                'symbol': buy_put_symbol,
                'side': 'BUY',
                'quantity': quantity,
                'status': buy_put_response.status
            })
            
            # Sell call
            sell_call_order = MarketOrderRequest(
                symbol=sell_call_symbol,
                qty=quantity,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            sell_call_response = self.trading_client.submit_order(sell_call_order)
            orders.append({
                'order_id': sell_call_response.id,
                'symbol': sell_call_symbol,
                'side': 'SELL',
                'quantity': quantity,
                'status': sell_call_response.status
            })
            
            # Buy call
            buy_call_order = MarketOrderRequest(
                symbol=buy_call_symbol,
                qty=quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            buy_call_response = self.trading_client.submit_order(buy_call_order)
            orders.append({
                'order_id': buy_call_response.id,
                'symbol': buy_call_symbol,
                'side': 'BUY',
                'quantity': quantity,
                'status': buy_call_response.status
            })
            
            # Wait for orders to fill
            order_ids = [sell_put_response.id, buy_put_response.id, 
                        sell_call_response.id, buy_call_response.id]
            self._wait_for_orders_to_fill(order_ids)
            
            # Set stop loss and take profit
            stop_loss_order = self._set_stop_loss_for_iron_condor(
                symbol, orders, max_loss, stop_loss_pct
            )
            
            take_profit_order = self._set_take_profit_for_iron_condor(
                symbol, orders, max_profit, take_profit_pct
            )
            
            return {
                'strategy': 'iron_condor',
                'symbol': symbol,
                'orders': orders,
                'max_loss': max_loss,
                'max_profit': max_profit,
                'stop_loss_order': stop_loss_order,
                'take_profit_order': take_profit_order,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error creating iron condor: {e}")
            self._cancel_orders([order['order_id'] for order in orders])
            raise
    
    def _set_stop_loss_for_spread(
        self, 
        symbol: str, 
        buy_symbol: str, 
        sell_symbol: str,
        quantity: int,
        max_loss: float,
        stop_loss_pct: float
    ) -> Optional[Dict]:
        """Set stop loss order for a spread strategy"""
        
        stop_loss_amount = max_loss * stop_loss_pct
        
        # Create a stop order to close the spread if loss exceeds threshold
        stop_order = StopOrderRequest(
            symbol=buy_symbol,  # Close the long position
            qty=quantity,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            stop_price=stop_loss_amount / (quantity * 100)  # Approximate stop price
        )
        
        try:
            response = self.trading_client.submit_order(stop_order)
            logger.info(f"Stop loss order submitted: {response.id}")
            return {
                'order_id': response.id,
                'type': 'stop_loss',
                'amount': stop_loss_amount,
                'status': response.status
            }
        except Exception as e:
            logger.error(f"Error setting stop loss: {e}")
            return None
    
    def _set_take_profit_for_spread(
        self,
        symbol: str,
        buy_symbol: str,
        sell_symbol: str,
        quantity: int,
        max_profit: float,
        take_profit_pct: float
    ) -> Optional[Dict]:
        """Set take profit order for a spread strategy"""
        
        take_profit_amount = max_profit * take_profit_pct
        
        # Create a limit order to close the spread when profit target is reached
        limit_order = LimitOrderRequest(
            symbol=buy_symbol,  # Close the long position
            qty=quantity,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC,
            limit_price=take_profit_amount / (quantity * 100)  # Approximate limit price
        )
        
        try:
            response = self.trading_client.submit_order(limit_order)
            logger.info(f"Take profit order submitted: {response.id}")
            return {
                'order_id': response.id,
                'type': 'take_profit',
                'amount': take_profit_amount,
                'status': response.status
            }
        except Exception as e:
            logger.error(f"Error setting take profit: {e}")
            return None
    
    def _set_stop_loss_for_iron_condor(
        self,
        symbol: str,
        orders: List[Dict],
        max_loss: float,
        stop_loss_pct: float
    ) -> Optional[Dict]:
        """Set stop loss for iron condor strategy"""
        
        stop_loss_amount = max_loss * stop_loss_pct
        
        # For iron condor, we need to close all positions if stop loss is hit
        # This is a simplified approach - in practice, you might want more sophisticated logic
        
        try:
            # Create a stop order for the short put (most vulnerable leg)
            short_put_symbol = orders[0]['symbol']  # First order is sell put
            stop_order = StopOrderRequest(
                symbol=short_put_symbol,
                qty=orders[0]['quantity'],
                side=OrderSide.BUY,  # Buy to close the short put
                time_in_force=TimeInForce.GTC,
                stop_price=stop_loss_amount / (orders[0]['quantity'] * 100)
            )
            
            response = self.trading_client.submit_order(stop_order)
            logger.info(f"Iron condor stop loss order submitted: {response.id}")
            return {
                'order_id': response.id,
                'type': 'stop_loss',
                'amount': stop_loss_amount,
                'status': response.status
            }
        except Exception as e:
            logger.error(f"Error setting iron condor stop loss: {e}")
            return None
    
    def _set_take_profit_for_iron_condor(
        self,
        symbol: str,
        orders: List[Dict],
        max_profit: float,
        take_profit_pct: float
    ) -> Optional[Dict]:
        """Set take profit for iron condor strategy"""
        
        take_profit_amount = max_profit * take_profit_pct
        
        try:
            # Close the short put when profit target is reached
            short_put_symbol = orders[0]['symbol']
            limit_order = LimitOrderRequest(
                symbol=short_put_symbol,
                qty=orders[0]['quantity'],
                side=OrderSide.BUY,  # Buy to close
                time_in_force=TimeInForce.GTC,
                limit_price=take_profit_amount / (orders[0]['quantity'] * 100)
            )
            
            response = self.trading_client.submit_order(limit_order)
            logger.info(f"Iron condor take profit order submitted: {response.id}")
            return {
                'order_id': response.id,
                'type': 'take_profit',
                'amount': take_profit_amount,
                'status': response.status
            }
        except Exception as e:
            logger.error(f"Error setting iron condor take profit: {e}")
            return None
    
    def _wait_for_orders_to_fill(self, order_ids: List[str], timeout: int = 300):
        """Wait for orders to fill with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_filled = True
            
            for order_id in order_ids:
                order = self.trading_client.get_order_by_id(order_id)
                if order.status not in [OrderStatus.FILLED, OrderStatus.CANCELED]:
                    all_filled = False
                    break
            
            if all_filled:
                logger.info("All orders have been filled")
                return
            
            time.sleep(2)
        
        logger.warning("Timeout waiting for orders to fill")
    
    def _cancel_orders(self, order_ids: List[str]):
        """Cancel multiple orders"""
        for order_id in order_ids:
            try:
                self.trading_client.cancel_order_by_id(order_id)
                logger.info(f"Canceled order: {order_id}")
            except Exception as e:
                logger.error(f"Error canceling order {order_id}: {e}")
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        positions = self.trading_client.get_all_positions()
        return [
            {
                'symbol': pos.symbol,
                'qty': float(pos.qty),
                'side': pos.side,
                'market_value': float(pos.market_value),
                'unrealized_pl': float(pos.unrealized_pl),
                'current_price': float(pos.current_price)
            }
            for pos in positions
        ]
    
    def close_position(self, symbol: str, qty: float = None):
        """Close a specific position"""
        try:
            if qty is None:
                # Close entire position
                self.trading_client.close_position(symbol)
            else:
                # Close partial position
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=abs(qty),
                    side=OrderSide.SELL if qty > 0 else OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
                self.trading_client.submit_order(order)
            
            logger.info(f"Closed position for {symbol}")
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
    
    def get_order_history(self, symbol: str = None) -> List[Dict]:
        """Get order history"""
        request = GetOrdersRequest()
        if symbol:
            request.symbols = [symbol]
        
        orders = self.trading_client.get_orders(request)
        return [
            {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side,
                'type': order.type,
                'status': order.status,
                'filled_at': order.filled_at,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
            }
            for order in orders
        ]


def main():
    """Example usage of the MultiLegOptionsTrader"""
    
    # Initialize the trader
    trader = MultiLegOptionsTrader()
    
    # Get account information
    account_info = trader.get_account_info()
    logger.info(f"Account Info: {account_info}")
    
    # Example 1: Create a bull call spread
    try:
        bull_spread = trader.create_bull_call_spread(
            symbol='AAPL',
            expiration_date='2024-01-19',  # Adjust to available expiration
            buy_strike=180.0,
            sell_strike=185.0,
            quantity=1,
            stop_loss_pct=0.25,
            take_profit_pct=0.50
        )
        logger.info(f"Bull call spread created: {json.dumps(bull_spread, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to create bull call spread: {e}")
    
    # Example 2: Create an iron condor
    try:
        iron_condor = trader.create_iron_condor(
            symbol='SPY',
            expiration_date='2024-01-19',  # Adjust to available expiration
            sell_put_strike=450.0,
            buy_put_strike=445.0,
            sell_call_strike=460.0,
            buy_call_strike=465.0,
            quantity=1,
            stop_loss_pct=0.30,
            take_profit_pct=0.60
        )
        logger.info(f"Iron condor created: {json.dumps(iron_condor, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to create iron condor: {e}")
    
    # Get current positions
    positions = trader.get_positions()
    logger.info(f"Current positions: {json.dumps(positions, indent=2)}")
    
    # Get order history
    order_history = trader.get_order_history()
    logger.info(f"Order history: {json.dumps(order_history, indent=2)}")


if __name__ == "__main__":
    main()