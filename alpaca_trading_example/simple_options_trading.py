"""
Simple Options Trading with Alpaca API

This example shows basic options trading with stop loss and take profit orders.
It's simpler than the multi-leg strategies and easier to understand.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest, 
    LimitOrderRequest,
    StopOrderRequest,
    GetOrdersRequest
)
from alpaca.trading.enums import (
    OrderSide, 
    TimeInForce, 
    OrderStatus
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleOptionsTrader:
    """
    Simple options trading with stop loss and take profit
    """
    
    def __init__(self):
        """Initialize the trading client"""
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        
        self.trading_client = TradingClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
            paper=True
        )
        
        logger.info("SimpleOptionsTrader initialized successfully")
    
    def get_account_info(self) -> Dict:
        """Get current account information"""
        account = self.trading_client.get_account()
        return {
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value),
            'equity': float(account.equity)
        }
    
    def buy_call_option(
        self,
        symbol: str,
        expiration_date: str,
        strike_price: float,
        quantity: int,
        stop_loss_pct: float = 0.25,
        take_profit_pct: float = 0.50
    ) -> Dict:
        """
        Buy a call option with stop loss and take profit
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            expiration_date: Option expiration date (YYYY-MM-DD)
            strike_price: Strike price for the call option
            quantity: Number of contracts
            stop_loss_pct: Stop loss percentage (0.25 = 25% loss)
            take_profit_pct: Take profit percentage (0.50 = 50% profit)
        """
        
        # Create option symbol
        option_symbol = f"{symbol}{expiration_date.replace('-', '')}C{strike_price:08.0f}"
        
        logger.info(f"Buying call option: {option_symbol}")
        logger.info(f"Strike: ${strike_price}, Quantity: {quantity}")
        
        try:
            # Buy the call option
            buy_order = MarketOrderRequest(
                symbol=option_symbol,
                qty=quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            response = self.trading_client.submit_order(buy_order)
            logger.info(f"Buy order submitted: {response.id}")
            
            # Wait for order to fill
            self._wait_for_order_to_fill(response.id)
            
            # Get the filled order to get the average price
            filled_order = self.trading_client.get_order_by_id(response.id)
            avg_price = float(filled_order.filled_avg_price) if filled_order.filled_avg_price else 0
            
            # Calculate stop loss and take profit prices
            stop_loss_price = avg_price * (1 - stop_loss_pct)
            take_profit_price = avg_price * (1 + take_profit_pct)
            
            # Set stop loss order
            stop_loss_order = self._set_stop_loss(
                option_symbol, quantity, stop_loss_price
            )
            
            # Set take profit order
            take_profit_order = self._set_take_profit(
                option_symbol, quantity, take_profit_price
            )
            
            return {
                'strategy': 'buy_call',
                'symbol': option_symbol,
                'quantity': quantity,
                'strike_price': strike_price,
                'avg_price': avg_price,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'buy_order_id': response.id,
                'stop_loss_order': stop_loss_order,
                'take_profit_order': take_profit_order,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error buying call option: {e}")
            raise
    
    def sell_put_option(
        self,
        symbol: str,
        expiration_date: str,
        strike_price: float,
        quantity: int,
        stop_loss_pct: float = 0.25,
        take_profit_pct: float = 0.50
    ) -> Dict:
        """
        Sell a put option with stop loss and take profit
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            expiration_date: Option expiration date (YYYY-MM-DD)
            strike_price: Strike price for the put option
            quantity: Number of contracts
            stop_loss_pct: Stop loss percentage (0.25 = 25% loss)
            take_profit_pct: Take profit percentage (0.50 = 50% profit)
        """
        
        # Create option symbol
        option_symbol = f"{symbol}{expiration_date.replace('-', '')}P{strike_price:08.0f}"
        
        logger.info(f"Selling put option: {option_symbol}")
        logger.info(f"Strike: ${strike_price}, Quantity: {quantity}")
        
        try:
            # Sell the put option
            sell_order = MarketOrderRequest(
                symbol=option_symbol,
                qty=quantity,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            response = self.trading_client.submit_order(sell_order)
            logger.info(f"Sell order submitted: {response.id}")
            
            # Wait for order to fill
            self._wait_for_order_to_fill(response.id)
            
            # Get the filled order to get the average price
            filled_order = self.trading_client.get_order_by_id(response.id)
            avg_price = float(filled_order.filled_avg_price) if filled_order.filled_avg_price else 0
            
            # Calculate stop loss and take profit prices
            stop_loss_price = avg_price * (1 + stop_loss_pct)  # Higher price for short position
            take_profit_price = avg_price * (1 - take_profit_pct)  # Lower price for short position
            
            # Set stop loss order (buy to close)
            stop_loss_order = self._set_stop_loss(
                option_symbol, quantity, stop_loss_price, side=OrderSide.BUY
            )
            
            # Set take profit order (buy to close)
            take_profit_order = self._set_take_profit(
                option_symbol, quantity, take_profit_price, side=OrderSide.BUY
            )
            
            return {
                'strategy': 'sell_put',
                'symbol': option_symbol,
                'quantity': quantity,
                'strike_price': strike_price,
                'avg_price': avg_price,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'sell_order_id': response.id,
                'stop_loss_order': stop_loss_order,
                'take_profit_order': take_profit_order,
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error selling put option: {e}")
            raise
    
    def _set_stop_loss(
        self, 
        symbol: str, 
        quantity: int, 
        stop_price: float,
        side: OrderSide = OrderSide.SELL
    ) -> Optional[Dict]:
        """Set stop loss order"""
        
        try:
            stop_order = StopOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.GTC,
                stop_price=stop_price
            )
            
            response = self.trading_client.submit_order(stop_order)
            logger.info(f"Stop loss order submitted: {response.id} at ${stop_price}")
            return {
                'order_id': response.id,
                'type': 'stop_loss',
                'price': stop_price,
                'status': response.status
            }
        except Exception as e:
            logger.error(f"Error setting stop loss: {e}")
            return None
    
    def _set_take_profit(
        self, 
        symbol: str, 
        quantity: int, 
        limit_price: float,
        side: OrderSide = OrderSide.SELL
    ) -> Optional[Dict]:
        """Set take profit order"""
        
        try:
            limit_order = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.GTC,
                limit_price=limit_price
            )
            
            response = self.trading_client.submit_order(limit_order)
            logger.info(f"Take profit order submitted: {response.id} at ${limit_price}")
            return {
                'order_id': response.id,
                'type': 'take_profit',
                'price': limit_price,
                'status': response.status
            }
        except Exception as e:
            logger.error(f"Error setting take profit: {e}")
            return None
    
    def _wait_for_order_to_fill(self, order_id: str, timeout: int = 300):
        """Wait for an order to fill with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            order = self.trading_client.get_order_by_id(order_id)
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELED]:
                logger.info(f"Order {order_id} status: {order.status}")
                return
            time.sleep(2)
        
        logger.warning(f"Timeout waiting for order {order_id} to fill")
    
    def get_positions(self) -> list:
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
    
    def close_position(self, symbol: str):
        """Close a specific position"""
        try:
            self.trading_client.close_position(symbol)
            logger.info(f"Closed position for {symbol}")
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
    
    def get_order_history(self, symbol: str = None) -> list:
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
    """Example usage of the SimpleOptionsTrader"""
    
    # Initialize the trader
    trader = SimpleOptionsTrader()
    
    # Get account information
    account_info = trader.get_account_info()
    logger.info(f"Account Info: {account_info}")
    
    # Example 1: Buy a call option
    try:
        call_trade = trader.buy_call_option(
            symbol='AAPL',
            expiration_date='2024-01-19',  # Adjust to available expiration
            strike_price=180.0,
            quantity=1,
            stop_loss_pct=0.25,
            take_profit_pct=0.50
        )
        logger.info(f"Call option trade: {json.dumps(call_trade, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to buy call option: {e}")
    
    # Example 2: Sell a put option
    try:
        put_trade = trader.sell_put_option(
            symbol='SPY',
            expiration_date='2024-01-19',  # Adjust to available expiration
            strike_price=450.0,
            quantity=1,
            stop_loss_pct=0.30,
            take_profit_pct=0.60
        )
        logger.info(f"Put option trade: {json.dumps(put_trade, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to sell put option: {e}")
    
    # Get current positions
    positions = trader.get_positions()
    logger.info(f"Current positions: {json.dumps(positions, indent=2)}")
    
    # Get order history
    order_history = trader.get_order_history()
    logger.info(f"Order history: {json.dumps(order_history, indent=2)}")


if __name__ == "__main__":
    main()