# -*- coding: utf-8 -*-

print("starting script")

import time
import MetaTrader5 as mt5
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np



def get_forex_data(symbol, timeframe):

    # symbol = "Volatility 25 (1s) Index"  # Replace with your asset
    
    # Connect to MetaTrader 5
    if not mt5.initialize():
        print("MT5 Initialization failed")
        quit()
    
    # Get today's date
    end_date = datetime.datetime.now()
    # print("end_date",end_date)
    # Get the date 5 days ago
    start_date = end_date - datetime.timedelta(hours=10)
    # print("start_date",start_date)
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

# Function to place a trade

# Check account balance
def get_account_info():
    account_info = mt5.account_info()
    if account_info is None:
        print("❌ Failed to retrieve account info.")
        return None
    return account_info.balance

# Place a buy or sell order
def place_pending_order(symbol, volume, order_type, price, stop_loss_price, take_profit_price, comment):
    """
    Places a market order in MetaTrader 5.
    - order_type: 'buy' or 'sell'
    """
   
    # order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL
    order_type_mt5 = mt5.ORDER_TYPE_BUY_STOP if order_type == "buy_stop" else mt5.ORDER_TYPE_SELL_STOP
    # price = mt5.symbol_info_tick(symbol).ask if order_type == "buy" else mt5.symbol_info_tick(symbol).bid
    print(order_type_mt5)

    request = {

            "action": mt5.TRADE_ACTION_PENDING,  # mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,                   # lot size
            "price": price,         # price at which order is pending
            "type": order_type_mt5,   # pending order type (buy if price moves upward)
            "sl": stop_loss_price,
            "tp": take_profit_price, 
            "deviation": 10,
            "magic": 123456,
            "comment": comment ,
            "type_time": mt5.ORDER_TIME_GTC,   # good till canceled
            "type_filling": mt5.ORDER_FILLING_IOC #mt5.ORDER_FILLING_FOK,
    }

    print("request: ", request)

    result = mt5.order_send(request)
    if result is None:
        print("Order send failed. Check connection and request format.")
    else:
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Trade failed: {result.comment}")
        else:
            print(f"✅ Trade successful! {order_type.upper()} {symbol} at {price}")

    print("Last MT5 Error:", mt5.last_error())

def place_order(symbol, volume, order_type, price, stop_loss_price, take_profit_price, comment):
    """
    Places a market order in MetaTrader 5.
    - order_type: 'buy' or 'sell'
    """

    
    order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL

    request = {

            "action": mt5.TRADE_ACTION_DEAL,  # mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,                   # lot size
            "price": price,         # price at which order is pending
            "type": order_type_mt5,   # pending order type (buy if price moves upward)
            "sl": stop_loss_price,
            "tp": take_profit_price, 
            "deviation": 10,
            "magic": 123456,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,   # good till canceled
            "type_filling": mt5.ORDER_FILLING_FOK,
    }

    print("request: ", request)

    result = mt5.order_send(request)
    if result is None:
        print("Order send failed. Check connection and request format.")
    else:
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Trade failed: {result.comment}")
        else:
            print(f"✅ Trade successful! {order_type.upper()} {symbol} at {price}")

def close_trades_by_crossover(last_crossover):
    """
    Closes trades based on the last crossover direction.
    - If last crossover was DOWN, close all BUY positions.
    - If last crossover was UP, close all SELL positions.
    """
    
    if not mt5.initialize():
        print("Failed to connect to MT5")
        return "ERROR"

    # Check for open orders
    trades_open = mt5.positions_get()
    if len(trades_open) == 0:
        print("No open trades or connection issue.")
    
    for trade in trades_open:
        # Determine trade type to close
        if last_crossover == "down" and trade.type == mt5.ORDER_TYPE_BUY:
            close_trade(trade)

        elif last_crossover == "up" and trade.type == mt5.ORDER_TYPE_SELL:
            close_trade(trade)

    
    # Get all pending orders
    pending_orders = mt5.orders_get()

    # Check if there are any pending orders
    if pending_orders is None:
        print("Failed to retrieve pending orders:", mt5.last_error())
    elif len(pending_orders) == 0:
        print("No pending orders found.")
    else:
        print(f"Found {len(pending_orders)} pending orders:")
        for order in pending_orders:
            print(order.type, mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_SELL_STOP, last_crossover)
            # Determine trade type to close
            if last_crossover == "down" and order.type == mt5.ORDER_TYPE_BUY_STOP:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,  # Cancel pending order
                    "order": order.ticket,  # Use the order ticket ID
                }
                result = mt5.order_send(request)
                
            elif last_crossover == "up" and order.type == mt5.ORDER_TYPE_SELL_STOP:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,  # Cancel pending order
                    "order": order.ticket,  # Use the order ticket ID
                }
                result = mt5.order_send(request)

    return "CLOSED TRADES BASED ON CROSSOVER"

def close_trade(trade):
    """Sends a close order request for a specific trade."""

    # Define the opposite order type to close the trade
    opposite_type = mt5.ORDER_TYPE_SELL if trade.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    

    request = {
        "action": mt5.TRADE_ACTION_DEAL,  # Place opposite trade to close
        "position": trade.ticket,  # The trade ticket
        "symbol": trade.symbol,
        "volume": trade.volume,
        "type": opposite_type,  # Opposite order type
        "price": mt5.symbol_info_tick(trade.symbol).bid if trade.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(trade.symbol).ask,
        "deviation": 10,
        "magic": trade.magic,
        "comment": "Closing due to crossover",
    }

    result = mt5.order_send(request)

    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Failed to close trade {trade.ticket} ({trade.symbol})")
    else:
        print(f"✅ Closed trade {trade.ticket} ({trade.symbol})")

def is_trade_open(symbol):
    # Check if there is an open position for the given symbol
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        return False  # No open positions
    else:
        return True  # There's an open position

def check_existing_sell_stop(symbol, price):

    # Get all pending orders
    orders = mt5.orders_get(symbol=symbol, price=price)
    print("order: ", orders)
    
    if orders is None:
        print("No pending orders or connection issue.")
        return "ERROR"
    
    return orders
    

def sell_conditions(df, symbol, volume, stop_loss_adjust, cross_over_date):
    print("CHECKING ALL THE SELL CONDITIONS SINCE THE LAST CROSS OVER IS DOWN")
    # CONDITION 2
    df_2 = df.copy()
    df_2["condition2_sell"] = False  # Initialize the column with False
    df_2["condition3_sell"] = False  # Initialize the column with False
    df_2['stop_loss']=0.0
    df_2['tp']=0.0
    df_2['pending_order']=0.0
    

    # Get current price data
    tick_info = mt5.symbol_info_tick(symbol)

    if tick_info:
        current_price = tick_info.bid  # or tick_info.ask depending on your logic
        print(f"Current {symbol} Price: {current_price}")
    else:
        print(f"Failed to get price for {symbol}")

    # Apply the condition to all rows except the first two (to prevent index errors)
    # (df.iloc[i-1]["high"] > df.iloc[i-2]["high"]) and \
    for i in range(2, len(df_2)):
        
        if (df_2.iloc[i-1]["high"] > df_2.iloc[i-2]["high"]) and \
            (df_2.iloc[i-1]["close"] < df_2.iloc[i-2]["high"]) and \
               (df_2.iloc[i-1]["close"] > df_2.iloc[i-2]["low"]):
            
            df_2.loc[df_2.index[i-1], "condition2_sell"] = True  # Set to True if conditions are met
            df_2.loc[df_2.index[i-1], "stop_loss"] = df_2.iloc[i-2]["high"]
            df_2.loc[df_2.index[i-1], "tp"] = df_2.iloc[i-3]["low"]-stop_loss_adjust
            df_2.loc[df_2.index[i-1], "pending_order"] = df_2.iloc[i-1]["low"]
    
    
    df_2['condition1_sell'] = df_2['condition1_sell'].shift(1)
    df_2['non_touching'] = df_2['non_touching'].shift(1)

    if not is_trade_open(symbol):
        # Filter for CONDITION 2
        filtered_df2 = df_2[
            (df_2['cross_over'] == 'down') & 
            (df_2['non_touching'] == True) & 
            (df_2['condition1_sell'] == True) & 
            (df_2['condition2_sell'] == True)  &
            (df_2['condition3_sell'] == False) 
        ]
        
        # Example: Set stop loss at the high price
        # Display the filtered DataFrame
        if len(filtered_df2) >= 1:
            print("cross_over_date: ", cross_over_date)
            print("CONDITION 2 DATE: ", filtered_df2.index[-1])
            # Check if the cross_over_date is less than the CONDITION date
            if cross_over_date <= filtered_df2.index[-1]:
                print("cross over date is less than CONDITION date")
                # Now place a Pending Sell Order:
                volume=volume
                order_type = "sell_stop"
                pending_order_price=float(filtered_df2.iloc[-1]["pending_order"])
                sl = filtered_df2.iloc[-1]["stop_loss"]
                tp = filtered_df2.iloc[-1]["tp"]

                if check_existing_sell_stop(symbol, pending_order_price):
                    print(f"❌ A sell stop trade is already open for {symbol}. Skipping new see stop trade.")
                    return "HOLD"  # You can return whatever signal you need to indicate no trade

                place_pending_order(symbol, volume, order_type, pending_order_price, stop_loss_price=sl, take_profit_price=tp, comment="CONDITION-2")
            
                        
        

    
    # CONDITION 3
    df_3 = df_2.copy()

    if not is_trade_open(symbol):
        df_3["condition3_sell"] = False  # Initialize the column with False
        df_3['stop_loss']=0.0
        df_3['tp']=0.0
        df_3['pending_order']=0.0
        
        # Apply the condition to all rows except the first two (to prevent index errors)
        for i in range(2, len(df_3)):
            if (df_3.iloc[i-1]["close"] < df_3.iloc[i-4]["high"]) and \
                (df_3.iloc[i-1]["open"] < df_3.iloc[i-4]["high"]) and \
                (df_3.iloc[i-1]["open"] > df_3.iloc[i-3]["low"]) and \
               (df_3.iloc[i-1]["close"] > df_3.iloc[i-3]["low"]):
                
                df_3.loc[df_3.index[i-1], "condition3_sell"] = True  # Set to True if conditions are met
                df_3.loc[df_3.index[i-1], "stop_loss"] = df_3.iloc[i-4]["high"]
                df_3.loc[df_3.index[i-1], "tp"] = df_3.iloc[i-3]["low"]-stop_loss_adjust
                df_3.loc[df_3.index[i-1], "pending_order"] = df_3.iloc[i-3]["low"]
                
        
        df_3['condition2_sell'] = df_3['condition2_sell'].shift(1)
        df_3['condition1_sell'] = df_3['condition1_sell'].shift(1)
        df_3['non_touching'] = df_3['non_touching'].shift(1)
        
        
        # Filter for CONDITIONV 3
        filtered_df3 = df_3[
            (df_3['cross_over'] == 'down') & 
            (df_3['non_touching'] == True) & 
            (df_3['condition1_sell'] == True) & 
            # (df_3['condition2_sell'] == False) & 
            (df_3['condition3_sell'] == True)
        ]
        
        if len(filtered_df3) >= 1:
            print("cross_over_date: ", cross_over_date)
            print("CONDITION 2 DATE: ", filtered_df3.index[-1])
            # Check if the cross_over_date is less than the CONDITION date
            if cross_over_date <= filtered_df3.index[-1]:
                # Now place a Pending Sell Order:
                volume=volume
                order_type = "sell_stop"
                price=float(filtered_df3.iloc[-1]["pending_order"])
                sl = filtered_df3.iloc[-1]["stop_loss"]
                tp = filtered_df3.iloc[-1]["tp"]

                if check_existing_sell_stop(symbol, price):
                    print(f"❌ A sell stop trade is already open for {symbol}. Skipping new see stop trade.")
                    return "HOLD"  # You can return whatever signal you need to indicate no trade

                place_pending_order(symbol, volume, order_type, price, stop_loss_price=sl, take_profit_price=tp, comment="CONDITION 3-PENDINT ORDER")
            
            
    
    




    # CONDITION 2.2
    df_22 = df.copy()
    if not is_trade_open(symbol):
        # df_22 = df_22.drop(['condition2_sell', 'condition3_sell'], axis=1)
        df_22["condition2_2_sell"] = False  # Initialize the column with False
        df_22['stop_loss']=0.0
        df_22['tp']=0.0
        df_22['sell_order']=0.0
        
        # Apply the condition to all rows except the first two (to prevent index errors)
        for i in range(2, len(df_22)):
            if (df_22.iloc[i-1]["high"] > df_22.iloc[i-2]["high"]) and \
               (df_22.iloc[i-1]["close"] < df_22.iloc[i-2]["low"]):
                
                df_22.loc[df_22.index[i-1], "condition2_2_sell"] = True  # Set to True if conditions are met
                df_22.loc[df_22.index[i-1], "stop_loss"] = df_22.iloc[i-2]["high"]
                df_22.loc[df_22.index[i-1], "tp"] = df_22.iloc[i-1]["low"]-stop_loss_adjust
                df_22.loc[df_22.index[i-1], "sell_order"] = df_22.iloc[i-1]["close"]
        
        
        
        df_22['condition1_sell'] = df_22['condition1_sell'].shift(1)
        df_22['non_touching'] = df_22['non_touching'].shift(1)
        df_22.tail(20)
        
        
        # Filter for CONDITIONV 2_2
        filtered_df22 = df_22[
            (df_22['cross_over'] == 'down') & 
            (df_22['non_touching'] == True) & 
            (df_22['condition1_sell'] == True) & 
            (df_22['condition2_2_sell'] == True) 
        ]
        
        if len(filtered_df22) >= 1:
            print("cross_over_date: ", cross_over_date)
            print("condition2_2_sell: ", filtered_df22.index[-1])
            # Check if the cross_over_date is less than the CONDITION date
            if cross_over_date <= filtered_df22.index[-1]:
                # Now place a Pending Sell Order:
                volume=volume
                order_type = "sell"
                price=float(filtered_df22.iloc[-1]["sell_order"])
                sl = filtered_df22.iloc[-1]["stop_loss"]
                tp = filtered_df22.iloc[-1]["tp"]

                if check_existing_sell_stop(symbol, price):
                    print(f"❌ A sell stop trade is already open for {symbol}. Skipping new see stop trade.")
                    return "HOLD"  # You can return whatever signal you need to indicate no trade

                place_order(symbol, volume, order_type, price, stop_loss_price=sl, take_profit_price=tp, comment="CONDITION 2_2-ORDER")















def check_signal(df, symbol, volume, stop_loss_adjust):
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

    # Apply the condition to all rows except the first two (to prevent index errors)
    for i in range(2, len(df)):
        if (df.iloc[i-1]["low"] < df.iloc[i-2]["low"]) and \
           (df.iloc[i-1]["close"] < df.iloc[i-2]["high"]) and \
           (df.iloc[i-1]["close"] > df.iloc[i-2]["low"]):
            df.loc[df.index[i-1], "condition1_sell"] = True  # Set to True if conditions are met

    print("df: \n", df.tail(10))
    last_crossover = df.iloc[-1]['cross_over']
    if last_crossover == "down":

        try:
            # Find the last "up" crossover
            last_up_index = df[df["cross_over"] == "up"].index[-1]
            # Find the first "down" crossover
            down_after_up = df.loc[last_up_index:].query("cross_over == 'up'").head(1).index[-1]
            # Firstly close all exisiting trades and pending trades
            close_trades_by_crossover(last_crossover)
            # # Check all the sell conditions
            sell_conditions(df, symbol, volume, stop_loss_adjust, down_after_up)
        except Exception as e:
            # By this way we can know about the type of error occurring
            print("The error is: ",e)

    elif  last_crossover == "up":

        try:
            # Find the last "down" crossover
            last_down_index = df[df["cross_over"] == "down"].index[-1]
            # Find the first "down" crossover
            up_after_down = df.loc[last_down_index:].query("cross_over == 'down'").head(1).index[-1]
            # Firstly close all exisiting trades and pending trades
            close_trades_by_crossover(last_crossover)
            # Check all the buy conditions
        except Exception as e:
            # By this way we can know about the type of error occurring
            print("The error is: ",e)

    # Example: Replace with your strategy logic
    print(f"Checking signals for {symbol}...")
    return "HOLD"

# List all the pairs to monitor
currency_pairs = {
    "Volatility 10 Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 25 Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 50 Index": {"volume": 4.0, "stop_loss_adjust": 2000},
    "Volatility 75 Index": {"volume": 0.01, "stop_loss_adjust": 2000},
    "Volatility 100 Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 10 (1s) Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 25 (1s) Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 50 (1s) Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 75 (1s) Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 100 (1s) Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Volatility 150 (1s) Index": {"volume": 1, "stop_loss_adjust": 2000},
    "Jump 10 Index": {"volume": 0.1, "stop_loss_adjust": 2000},
    "Jump 100 Index": {"volume": 0.1, "stop_loss_adjust": 2000},
    "Jump 75 Index": {"volume": 0.1, "stop_loss_adjust": 2000},
    # "Drift Switch 10 Index": {"volume": 0.1, "stop_loss_adjust": 2000},
    # "Drift Switch 20 Index": {"volume": 0.1, "stop_loss_adjust": 2000},
    # "Drift Switch 30 Index": {"volume": 0.1, "stop_loss_adjust": 2000},
    "Step Index": {"volume": 1, "stop_loss_adjust": 2000},
}

timeframe = mt5.TIMEFRAME_M15
while True:
    for symbol in currency_pairs:
        print(symbol, currency_pairs[symbol]['volume'], currency_pairs[symbol]['stop_loss_adjust'])
        volume = currency_pairs[symbol]['volume']
        stop_loss_adjust = currency_pairs[symbol]['stop_loss_adjust']
        df = get_forex_data(symbol, timeframe)
        signal = check_signal(df, symbol, volume, stop_loss_adjust)
        print(f"Signal for {symbol}: {signal}")
    
    print("Waiting for 15 seconds before next check...\n")
    time.sleep(10)  # Wait for 60 seconds before checking again



Kind regards

Bongani Mathye
Quality Engineer  

Phone:      +27 64 652 3377
www.rheinmetall.com

 

