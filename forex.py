import time
import MetaTrader5 as mt5
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np



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
            "price": float(price),         # price at which order is pending
            "type": order_type_mt5,   # pending order type (buy if price moves upward)
            "sl": stop_loss_price,
            # "tp": take_profit_price, 
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
            # "price": float(price),         # price 
            "type": order_type_mt5,   # pending order type (buy if price moves upward)
            "sl": stop_loss_price,
            # "tp": take_profit_price, 
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




def close_trades_by_crossover(last_crossover, symbol, tp):
    """
    Closes trades based on the last crossover direction.
    - If last crossover was DOWN, close all BUY positions.
    - If last crossover was UP, close all SELL positions.
    """
    
    print("last_crossover: ", last_crossover)
    if not mt5.initialize():
        print("Failed to connect to MT5")
        return "ERROR"

    # Check for open orders
    trades_open = mt5.positions_get()
    if len(trades_open) == 0:
        print("No open trades or connection issue.")
    
    for trade in trades_open:
        print("trade.type: ", mt5.ORDER_TYPE_BUY, trade.type, last_crossover, trade.symbol)

        # Close the trade is the profit reaches 2 dollars
        close_trade_if_profit(trade, tp)

        # # Determine trade type to close
        # if last_crossover == "down" and trade.type == mt5.ORDER_TYPE_BUY and symbol == trade.symbol:
        #     close_trade(trade)

        # elif last_crossover == "up" and trade.type == mt5.ORDER_TYPE_SELL and symbol == trade.symbol:
        #     close_trade(trade)



    
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
            # Determine trade type to close
            if last_crossover == "down" and order.type == mt5.ORDER_TYPE_BUY_STOP and symbol == order.symbol:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,  # Cancel pending order
                    "order": order.ticket,  # Use the order ticket ID
                }
                result = mt5.order_send(request)
                
            elif last_crossover == "up" and order.type == mt5.ORDER_TYPE_SELL_STOP and symbol == order.symbol:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,  # Cancel pending order
                    "order": order.ticket,  # Use the order ticket ID
                }
                result = mt5.order_send(request)


    return "CLOSED TRADES BASED ON CROSSOVER"



def close_trade_if_profit(trade, tp):
    """Sends a close order is the profit reaches 5 dollars"""
    print("take profit dollar: ", tp)
    if trade.profit >= tp: #or trade.profit <= -3:  # Close trade if profit ≥ $5 or loss ≤ -$10
            close_trade(trade)





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
    


