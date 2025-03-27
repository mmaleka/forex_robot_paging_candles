import time
import MetaTrader5 as mt5
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np
import json
import os

from forex import close_trades_by_crossover
from paging_candles import sell_conditions, buy_conditions




def should_place_order(symbol, cross_over_date):
    """
    Checks if a new order should be placed based on the last trade date.

    :param symbol: The trading pair (e.g., "Volatility 75 Index")
    :param cross_over_date: The last crossover date (datetime object)
    :return: True if a new order should be placed, otherwise False
    """
    # Define time range to get previous orders
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=30)  # Adjust as needed

    # Retrieve trade history from MT5
    trades = mt5.history_deals_get(start_time, end_time)

    if trades is None or len(trades) == 0:
        print("No previous trades found. Placing new order.")
        return True

    # Filter trades for the given symbol
    symbol_trades = [trade for trade in trades if trade.symbol == symbol]

    if not symbol_trades:
        print("No previous trades for this symbol. Placing new order.")
        return True

    # Get the last trade date
    last_trade_date = max(trade.time for trade in symbol_trades)
    last_trade_date = datetime.datetime.fromtimestamp(last_trade_date)

    # Check if the crossover date is after the last trade date
    if last_trade_date < cross_over_date:
        print("Place order or pending order on new order date.")
        return True
    else:
        print("No new order needed.")
        return False





def get_consecutive_losses(symbol):
    """
    Returns the number of consecutive losses for a given symbol in the trade DataFrame.
    
    :param df: DataFrame containing trade history
    :param symbol: The trading pair (e.g., "Volatility 75 Index")
    :return: Tuple of (is_last_trade_loss, consecutive_losses)
    """

    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(hours=24)
    
    # Get trade history for the last X hours
    trades = mt5.history_deals_get(start_time, now)
    df = pd.DataFrame(list(trades), columns=trades[0]._asdict().keys())
    # Convert 'time' to a readable datetime format
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df_non_zero_profit = df[df['profit'] != 0]
    df_non_zero_profit['result'] = df_non_zero_profit['profit'].apply(lambda x: 'win' if x > 0 else 'loss')

    # df_symbol_trades = df_non_zero_profit[df_non_zero_profit['symbol'] == symbol]
    df_symbol_trades = df_non_zero_profit

    if not df_symbol_trades.empty:
        # Get the last trade
        last_trade = df_symbol_trades.iloc[-1]
        print("last_trade['result']: ", last_trade['result'])
        
        # Check if the last trade was a loss
        is_last_trade_loss = last_trade['result'] == 'loss'
        
        # Count consecutive losses
        consecutive_losses = 0
        for i in range(len(df_symbol_trades) - 1, -1, -1):
            if df_symbol_trades.iloc[i]['result'] == 'loss':
                consecutive_losses += 1
            else:
                break  # Stop when a win is found
        
        return is_last_trade_loss, consecutive_losses
    else:
        print(f"No trades found for {symbol}.")
        return False, 0





# Function to check if a pair has an active SELL trade for today
def has_today_trade(symbol, trade_type):
    """
    Checks if a trade (BUY/SELL) exists for the given symbol today.
    :param symbol: The currency pair to check (e.g., "EURUSD").
    :param trade_type: 0 for BUY, 1 for SELL.
    :return: True if a trade exists, otherwise False.
    """
    today = datetime.datetime.now()
    start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Get all trades for today
    trades = mt5.history_deals_get(start_time, end_time)

    if trades is None or len(trades) == 0:
        return False  # No trades for today

    for trade in trades:
        # print("trade.comment[:2]: ", trade.comment[:2])
        if trade.symbol == symbol and trade.type == trade_type and trade.comment != "Closing due to c" and trade.reason != 4:
            print("trade already placed: ", trade)
            return True  # Found a trade

    return False  # No trade found



def has_recent_trade(symbol, trade_type, hours=0.001):
    """
    Checks if a trade (BUY/SELL) exists for the given symbol in the last X hours.
    :param symbol: The currency pair to check (e.g., "EURUSD").
    :param trade_type: 0 for BUY, 1 for SELL.
    :param hours: The number of hours to check (default is 1 hour).
    :return: True if a trade exists, otherwise False.
    """
    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(hours=hours)
    
    # Get trade history for the last X hours
    trades = mt5.history_deals_get(start_time, now)

    if trades is None or len(trades) == 0:
        return False  # No trades in the last X hours

    for trade in trades:
        if trade.symbol == symbol and trade.type == trade_type and trade.comment != "Closing due to c" and trade.reason != 4:
            print("Trade already placed: ", trade)
            return True  # Found a trade in the last X hours

    return False  # No trade found






def get_forex_data(symbol, timeframe):

    # symbol = "Volatility 25 (1s) Index"  # Replace with your asset
    
    # Connect to MetaTrader 5
    if not mt5.initialize():
        print("MT5 Initialization failed")
        quit()
    
    # Get today's date
    end_date = datetime.datetime.now()

    # Get the date 5 days ago
    start_date = end_date - datetime.timedelta(hours=24)

    # # Define the start and end date
    # start_date = datetime.datetime(2025, 2, 7, 8, 0)  # Adjust the date and time as needed
    # end_date = datetime.datetime(2025, 2, 11, 23, 59)  # Adjust the date and time as needed


    # Get historical data
    rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    df = pd.DataFrame(rates)
    
    # Convert time to datetime
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    df = df.drop(['tick_volume', 'spread', 'real_volume'], axis=1)

    return df


# Function to check if a candle is non-touching
def find_non_touching_candles(df):
    non_touching = []

    for i in range(len(df)):
        if df['low'].iloc[i] > df['EMA_4'].iloc[i] and df['low'].iloc[i] > df['EMA_7'].iloc[i]:
            non_touching.append(True)
        elif df['high'].iloc[i] < df['EMA_4'].iloc[i] and df['high'].iloc[i] < df['EMA_7'].iloc[i]:
            non_touching.append(True)
        else:
            non_touching.append(False)

    df['non_touching'] = non_touching  # Add the new column to the DataFrame
    return df



def check_signal(df, symbol, volume, stop_loss_adjust, timeframe, tp):
    """
    Placeholder function to check trading signals for a given currency pair.
    Replace this with your actual strategy.
    """

    df["EMA_4"] = df["close"].ewm(span=4, adjust=False).mean()  # Simple Moving Average (50)
    df["EMA_7"] = df["close"].ewm(span=7, adjust=False).mean()  # Simple Moving Average (200)df['cross_over'] = None  # Initialize column with None
    last_signal = None  # Keep track of the last crossover
    
    # Identify crossover points
    for i in range(1, len(df)):
        if df['EMA_4'].iloc[i] > df['EMA_7'].iloc[i] and df['EMA_4'].iloc[i-1] <= df['EMA_7'].iloc[i-1]:
            last_signal = 'up'  # Set last signal to up
        elif df['EMA_4'].iloc[i] < df['EMA_7'].iloc[i] and df['EMA_4'].iloc[i-1] >= df['EMA_7'].iloc[i-1]:
            last_signal = 'down'  # Set last signal to down
    
        df.at[df.index[i], 'cross_over'] = last_signal  # Apply the last signal to all following rows



    df = find_non_touching_candles(df)

    df["condition1_sell"] = False  # Initialize the column with False




    
    print(f"timeframe {timeframe}")
    print("df before shifting: \n", df.tail(5))
    

    # Check if DataFrame is empty
    if df.empty:
        print("The DataFrame is empty.")
    else:
        last_crossover = df.iloc[-1]['cross_over']
        

        if last_crossover == "down":



            # Apply the condition to all rows except the first two (to prevent index errors)
            for i in range(2, len(df)):
                if (df.iloc[i-1]["low"] < df.iloc[i-2]["low"]) and \
                (df.iloc[i-1]["close"] < df.iloc[i-2]["high"]) and \
                (df.iloc[i-1]["close"] > df.iloc[i-2]["low"]):
                    df.loc[df.index[i-1], "condition1_sell"] = True  # Set to True if conditions are met




            # # if has_today_trade(symbol, 1):
            # if has_recent_trade(symbol, 1, hours=1):
            #     print(f"🚫 Trade already placed for {symbol}, skipping...")
            # else:
            #     print(f"🟢 No {symbol} trade found for today, looking for trade...")

            # Example usage:
            is_last_trade_loss, consecutive_losses = get_consecutive_losses(symbol)
            if consecutive_losses <= 5:
                if is_last_trade_loss == True:
                    volume = consecutive_losses*volume*2
            


            try:
                # Find the last "up" crossover
                last_up_index = df[df["cross_over"] == "up"].index[-1]
                # Find the first "down" crossover
                down_after_up = df.loc[last_up_index:].query("cross_over == 'up'").head(1).index[-1]
                if should_place_order(symbol, down_after_up):
                    print(f"🟢 No {symbol} trade found for today, looking for trade...")


                    # Firstly close all exisiting trades and pending trades
                    close_trades_by_crossover(last_crossover, symbol, tp)

                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info:
                        print(f"Min lot: {symbol_info.volume_min}")
                        # volume = symbol_info.volume_min
                        # print(f"Max lot: {symbol_info.volume_max}")
                        # print(f"Lot step: {symbol_info.volume_step}")
                    else:
                        print("Symbol not found. Make sure it's correct and available.")


                    # Check all the sell conditions and return true if trade has been placed
                    
                    
                    sell_conditions(df, symbol, volume, stop_loss_adjust, down_after_up, tp)
                else:
                    print(f"🚫 Trade already placed for {symbol}, skipping...")
                    

            except Exception as e:
                # By this way we can know about the type of error occurring
                print("The error is: ",e)

        elif  last_crossover == "up":
                
            # Apply the condition to all rows except the first two (to prevent index errors)
            for i in range(2, len(df)):
                if (df.iloc[i-1]["high"] > df.iloc[i-2]["high"]) and \
                (df.iloc[i-1]["close"] > df.iloc[i-2]["low"]) and \
                (df.iloc[i-1]["close"] < df.iloc[i-2]["high"]):
                    df.loc[df.index[i-1], "condition1_sell"] = True  # Set to True if conditions are met



            

            # # if has_today_trade(symbol, 0):
            # if has_recent_trade(symbol, 0, hours=1):
            #     print(f"🚫 Trade already placed for {symbol}, skipping...")
            # else:
            #     print(f"🟢 No {symbol} trade found for today, looking for trade...")

            # Example usage:
            is_last_trade_loss, consecutive_losses = get_consecutive_losses(symbol)
            if consecutive_losses <= 5:
                if is_last_trade_loss == True:
                    volume = consecutive_losses*volume*2



            

            try:
                # Find the last "down" crossover
                last_down_index = df[df["cross_over"] == "down"].index[-1]
                # Find the first "down" crossover
                up_after_down = df.loc[last_down_index:].query("cross_over == 'down'").head(1).index[-1]
                if should_place_order(symbol, down_after_up):
                    print(f"🟢 No {symbol} trade found for today, looking for trade...")

                    # Firstly close all exisiting trades and pending trades
                    close_trades_by_crossover(last_crossover, symbol, tp)
                    # Check all the buy conditions

                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info:
                        print(f"Min lot: {symbol_info.volume_min}")
                        # print(f"Max lot: {symbol_info.volume_max}")
                        # print(f"Lot step: {symbol_info.volume_step}")
                    else:
                        print("Symbol not found. Make sure it's correct and available.")


                    # # Check all the sell conditions
                    buy_conditions(df, symbol, volume, stop_loss_adjust, up_after_down, tp)
                
                else:
                    print(f"🚫 Trade already placed for {symbol}, skipping...")

            except Exception as e:
                # By this way we can know about the type of error occurring
                print("The error is: ",e)





    # Example: Replace with your strategy logic
    print(f"Checking signals for {symbol}...")
    return "HOLD"
