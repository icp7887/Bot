from AlgorithmImports import *

class QCAlgorithm:
    def SetStartDate(self, year, month, day):
        pass
    def SetEndDate(self, year, month, day):
        pass
    def SetCash(self, amount):
        pass
    # Add other necessary methods and properties...

# Now define your algorithm class as before
# class RefinedMovingAverageCrossAlgorithm(QCAlgorithm):
    # Your algorithm code goes here...

class RefinedMovingAverageCrossAlgorithm(QCAlgorithm):
    
    def Initialize(self):
        # Basic setup
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 1, 1)
        self.SetCash(100000)
        
        # Add multiple assets for diversification
        self.symbols = ["SPY", "AAPL", "GOOG"]
        self.assets = [self.AddEquity(symbol, Resolution.Daily).Symbol for symbol in self.symbols]
        
        # Set up indicators (using EMA instead of SMA for smoother crossover signals)
        self.fast_period = 50
        self.slow_period = 200
        
        self.ema_fast = {symbol: self.EMA(symbol, self.fast_period, Resolution.Daily) for symbol in self.assets}
        self.ema_slow = {symbol: self.EMA(symbol, self.slow_period, Resolution.Daily) for symbol in self.assets}
        
        # Set a risk tolerance level (for dynamic position sizing)
        self.risk_tolerance = 0.02   # Risk 2% of capital on each trade
        
        # Set up warmup period to allow moving averages to populate
        self.SetWarmup(self.slow_period)
    
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        for symbol in self.assets:
            if symbol not in data:
                continue
            
            # Check if moving averages are ready and have crossed
            if not self.ema_fast[symbol].IsReady or not self.ema_slow[symbol].IsReady:
                continue  # Ensure the EMAs are ready before proceeding
            
            # If the fast EMA crosses above the slow EMA, buy
            if self.ema_fast[symbol].Current.Value > self.ema_slow[symbol].Current.Value:
                # Calculate the size of the position based on risk tolerance
                position_percentage = self.CalculatePositionSize(symbol)
                
                if position_percentage > 0 and not self.Portfolio[symbol].Invested:
                    self.SetHoldings(symbol, position_percentage)
                    self.Debug(f"Bought {symbol} at {self.Securities[symbol].Price}")
            
            # If the fast EMA crosses below the slow EMA, sell
            elif self.ema_fast[symbol].Current.Value < self.ema_slow[symbol].Current.Value:
                if self.Portfolio[symbol].Invested:
                    self.Liquidate(symbol)
                    self.Debug(f"Sold {symbol} at {self.Securities[symbol].Price}")
    
    def CalculatePositionSize(self, symbol):
        """Calculate position size based on risk tolerance and current volatility."""
        atr = self.ATR(symbol, 14, MovingAverageType.Simple)  # Use ATR to assess volatility
        price = self.Securities[symbol].Price
        
        # Ensure ATR is ready, and both ATR and price are not zero to avoid division by zero errors
        if not atr.IsReady or atr.Current.Value == 0 or price == 0:
            self.Debug(f"ATR or price for {symbol} is not ready or zero, skipping position sizing.")
            return 0  # Return 0 to skip this trade
        
        risk_per_share = atr.Current.Value
        capital_risked = self.Portfolio.TotalPortfolioValue * self.risk_tolerance
        
        # Determine how many shares to buy based on risk per share
        shares_to_buy = capital_risked / risk_per_share
        
        # Return position size as a percentage of total portfolio (max 100%)
        position_percentage = min(1, shares_to_buy * price / self.Portfolio.TotalPortfolioValue)
        
        return position_percentage
    
    def OnOrderEvent(self, order_event):
        """Handle order events to place stop losses and take profits."""
        if order_event.Status == OrderStatus.Filled:
            symbol = order_event.Symbol
            if order_event.Direction == OrderDirection.Buy:
                # Set a stop-loss and take-profit for the newly bought asset
                stop_price = order_event.FillPrice * 0.95  # 5% stop-loss
                profit_price = order_event.FillPrice * 1.1  # 10% take-profit
                self.StopMarketOrder(symbol, -self.Portfolio[symbol].Quantity, stop_price)
                self.LimitOrder(symbol, -self.Portfolio[symbol].Quantity, profit_price)

if __name__ == "__main__":
    algo = RefinedMovingAverageCrossAlgorithm()
    algo.Initialize()


