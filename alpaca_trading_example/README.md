# Alpaca Trading API - Multi-Leg Options Trading

This project demonstrates how to use the Alpaca Trading API to create multi-leg options strategies with stop loss and take profit orders.

## Features

- **Multi-leg options strategies**: Bull call spreads, iron condors, straddles, strangles
- **Stop loss and take profit**: Automated risk management
- **Position monitoring**: Real-time position tracking
- **Order management**: Comprehensive order handling and history
- **Paper trading**: Safe testing environment

## Prerequisites

1. **Alpaca Account**: Sign up at [alpaca.markets](https://alpaca.markets)
2. **Options Trading Enabled**: Ensure your account has options trading permissions
3. **API Keys**: Generate API keys from your Alpaca dashboard
4. **Python 3.8+**: Required for the alpaca-py library

## Installation

1. **Clone or download this project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Alpaca API credentials:
   ```env
   ALPACA_API_KEY=your_paper_api_key_here
   ALPACA_SECRET_KEY=your_paper_secret_key_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```

## Usage Examples

### 1. Simple Options Trading

The `simple_options_trading.py` file provides basic options trading functionality:

```python
from simple_options_trading import SimpleOptionsTrader

# Initialize trader
trader = SimpleOptionsTrader()

# Buy a call option with stop loss and take profit
call_trade = trader.buy_call_option(
    symbol='AAPL',
    expiration_date='2024-01-19',
    strike_price=180.0,
    quantity=1,
    stop_loss_pct=0.25,  # 25% stop loss
    take_profit_pct=0.50  # 50% take profit
)

# Sell a put option with stop loss and take profit
put_trade = trader.sell_put_option(
    symbol='SPY',
    expiration_date='2024-01-19',
    strike_price=450.0,
    quantity=1,
    stop_loss_pct=0.30,
    take_profit_pct=0.60
)
```

### 2. Multi-Leg Options Strategies

The `multi_leg_options_trading.py` file provides advanced multi-leg strategies:

```python
from multi_leg_options_trading import MultiLegOptionsTrader

# Initialize trader
trader = MultiLegOptionsTrader()

# Create a bull call spread
bull_spread = trader.create_bull_call_spread(
    symbol='AAPL',
    expiration_date='2024-01-19',
    buy_strike=180.0,
    sell_strike=185.0,
    quantity=1,
    stop_loss_pct=0.25,
    take_profit_pct=0.50
)

# Create an iron condor
iron_condor = trader.create_iron_condor(
    symbol='SPY',
    expiration_date='2024-01-19',
    sell_put_strike=450.0,
    buy_put_strike=445.0,
    sell_call_strike=460.0,
    buy_call_strike=465.0,
    quantity=1,
    stop_loss_pct=0.30,
    take_profit_pct=0.60
)
```

## Strategy Explanations

### Bull Call Spread
- **Strategy**: Buy a call at a lower strike, sell a call at a higher strike
- **Max Loss**: Net premium paid
- **Max Profit**: Difference between strikes minus net premium
- **When to Use**: Moderately bullish outlook

### Iron Condor
- **Strategy**: Sell a put spread and a call spread simultaneously
- **Max Loss**: Width of the wider spread minus net premium received
- **Max Profit**: Net premium received
- **When to Use**: Neutral outlook with low volatility expectations

### Stop Loss and Take Profit

Both examples include automated stop loss and take profit orders:

- **Stop Loss**: Automatically closes position if loss exceeds specified percentage
- **Take Profit**: Automatically closes position if profit reaches specified percentage
- **Order Types**: Uses stop orders for stop loss and limit orders for take profit

## Risk Management

### Important Considerations

1. **Paper Trading First**: Always test strategies in paper trading before live trading
2. **Position Sizing**: Never risk more than you can afford to lose
3. **Stop Losses**: Always use stop losses to limit potential losses
4. **Expiration Dates**: Be aware of option expiration dates and time decay
5. **Liquidity**: Ensure options have sufficient liquidity for easy entry/exit

### Risk Parameters

- **Stop Loss Percentage**: Typically 25-50% of the position value
- **Take Profit Percentage**: Typically 50-100% of the position value
- **Position Size**: Limit to 1-5% of total portfolio per trade

## API Endpoints Used

### Trading Endpoints
- `POST /v2/orders` - Submit orders
- `GET /v2/orders` - Get order history
- `DELETE /v2/orders/{order_id}` - Cancel orders
- `GET /v2/positions` - Get current positions
- `DELETE /v2/positions/{symbol}` - Close positions

### Data Endpoints
- `GET /v2/stocks/{symbol}/bars` - Get historical data
- `GET /v2/stocks/{symbol}/trades` - Get real-time trades

## Error Handling

The code includes comprehensive error handling for:

- **API Errors**: Network issues, authentication problems
- **Order Errors**: Invalid symbols, insufficient funds, market closed
- **Position Errors**: Position not found, already closed
- **Timeout Errors**: Orders taking too long to fill

## Monitoring and Management

### Position Monitoring
```python
# Get current positions
positions = trader.get_positions()
print(f"Current positions: {positions}")

# Get order history
order_history = trader.get_order_history()
print(f"Order history: {order_history}")
```

### Account Information
```python
# Get account details
account_info = trader.get_account_info()
print(f"Account info: {account_info}")
```

## Common Issues and Solutions

### 1. "Symbol not found" Error
- **Cause**: Option symbol format is incorrect
- **Solution**: Verify expiration date format and strike price format
- **Example**: `AAPL20240119C00180000` for AAPL call at $180 strike

### 2. "Insufficient buying power" Error
- **Cause**: Account doesn't have enough funds
- **Solution**: Check account balance and margin requirements
- **Note**: Options require margin for short positions

### 3. "Market closed" Error
- **Cause**: Trying to trade outside market hours
- **Solution**: Use GTC (Good Till Canceled) orders or wait for market open

### 4. "Order not filled" Error
- **Cause**: Poor liquidity or unrealistic prices
- **Solution**: Use market orders or adjust limit prices

## Best Practices

1. **Start Small**: Begin with small position sizes
2. **Test Thoroughly**: Use paper trading extensively
3. **Monitor Closely**: Check positions regularly
4. **Document Trades**: Keep detailed records of all trades
5. **Learn Continuously**: Study options theory and market dynamics

## Legal Disclaimer

This code is for educational purposes only. Trading options involves substantial risk and may not be suitable for all investors. Past performance does not guarantee future results. Always consult with a financial advisor before making investment decisions.

## Support

For issues with the Alpaca API:
- [Alpaca Documentation](https://docs.alpaca.markets/)
- [Alpaca Support](https://alpaca.markets/support)

For issues with this code:
- Check the error messages and logs
- Verify API credentials and permissions
- Ensure all dependencies are installed correctly

## License

This project is provided as-is for educational purposes. Use at your own risk.