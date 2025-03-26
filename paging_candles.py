import time
import MetaTrader5 as mt5
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np

from forex import *


def condition_2(symbol, df_2, stop_loss_adjust, cross_over_date, volume, cross_over_type, tp, order_type):

    # Get current price data
    tick_info = mt5.symbol_info_tick(symbol)

    if tick_info:
        current_price = tick_info.bid  # or tick_info.ask depending on your logic
        print(f"Current {symbol} Price: {current_price}")
    else:
        print(f"Failed to get price for {symbol}")

    # Apply the condition to all rows except the first two (to prevent index errors)
    for i in range(2, len(df_2)):
        
        if (df_2.iloc[i-1]["high"] > df_2.iloc[i-2]["high"]) and \
            (df_2.iloc[i-1]["close"] < df_2.iloc[i-2]["high"]) and \
               (df_2.iloc[i-1]["close"] > df_2.iloc[i-2]["low"]):
            
            df_2.loc[df_2.index[i-1], "condition2_sell"] = True  # Set to True if conditions are met
            df_2.loc[df_2.index[i-1], "stop_loss"] = df_2.iloc[i-3]["high"]
            df_2.loc[df_2.index[i-1], "tp"] = df_2.iloc[i-3]["low"]-stop_loss_adjust
            df_2.loc[df_2.index[i-1], "pending_order"] = df_2.iloc[i-3]["low"]
    
    
    df_2['condition1_sell'] = df_2['condition1_sell'].shift(1)
    df_2['non_touching'] = df_2['non_touching'].shift(1)





    if not is_trade_open(symbol):
        # Filter for CONDITION 2
        filtered_df2 = df_2[
            (df_2['cross_over'] == cross_over_type) & 
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
                order_type = order_type
                pending_order_price=float(filtered_df2.iloc[-1]["pending_order"])
                sl = filtered_df2.iloc[-1]["stop_loss"]
                # tp = filtered_df2.iloc[-1]["tp"]

                if check_existing_sell_stop(symbol, pending_order_price):
                    print(f"❌ A {order_type} trade is already open for {symbol}. Skipping new see stop trade.")
                    return "HOLD"  # You can return whatever signal you need to indicate no trade

                place_pending_order(symbol, volume, order_type, pending_order_price, stop_loss_price=sl, take_profit_price=tp, comment="CONDITION 2")
            
                        
def condition_3(symbol, df_2, stop_loss_adjust, cross_over_date, volume, cross_over_type, tp, order_type):

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
            (df_3['cross_over'] == cross_over_type) & 
            (df_3['non_touching'] == True) & 
            (df_3['condition1_sell'] == True) & 
            # (df_3['condition2_sell'] == False) & 
            (df_3['condition3_sell'] == True)
        ]
        
        if len(filtered_df3) >= 1:
            print("cross_over_date: ", cross_over_date)
            print("CONDITION 3 DATE: ", filtered_df3.index[-1])
            # Check if the cross_over_date is less than the CONDITION date
            if cross_over_date <= filtered_df3.index[-1]:
                # Now place a Pending Sell Order:
                volume=volume
                order_type = order_type
                price=float(filtered_df3.iloc[-1]["pending_order"])
                sl = filtered_df3.iloc[-1]["stop_loss"]
                # tp = filtered_df3.iloc[-1]["tp"]

                if check_existing_sell_stop(symbol, price):
                    print(f"❌ A {order_type} trade is already open for {symbol}. Skipping new see stop trade.")
                    return "HOLD"  # You can return whatever signal you need to indicate no trade


                place_pending_order(symbol, volume, order_type, price, stop_loss_price=sl, take_profit_price=tp, comment="CONDITION 3")
            
            
    

def condition_2_2(symbol, df, stop_loss_adjust, cross_over_date, volume, cross_over_type, tp, order_type):

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
                df_22.loc[df_22.index[i-1], "stop_loss"] = df_22.iloc[i-3]["high"]
                df_22.loc[df_22.index[i-1], "tp"] = df_22.iloc[i-1]["low"]-stop_loss_adjust
                df_22.loc[df_22.index[i-1], "sell_order"] = df_22.iloc[i-1]["close"]
        
        
        
        df_22['condition1_sell'] = df_22['condition1_sell'].shift(1)
        df_22['non_touching'] = df_22['non_touching'].shift(1)
        df_22.tail(20)
        
        
        # Filter for CONDITIONV 2_2
        filtered_df22 = df_22[
            (df_22['cross_over'] == cross_over_type) & 
            (df_22['non_touching'] == True) & 
            (df_22['condition1_sell'] == True) & 
            (df_22['condition2_2_sell'] == True) 
        ]
        
        if len(filtered_df22) >= 1:
            print("cross_over_date: ", cross_over_date)
            print("CONDITION 2.2 DATE: ", filtered_df22.index[-1])
            # Check if the cross_over_date is less than the CONDITION date
            if cross_over_date <= filtered_df22.index[-1]:
                # Now place a Pending Sell Order:
                volume=volume
                order_type = order_type
                price=float(filtered_df22.iloc[-1]["sell_order"])
                sl = filtered_df22.iloc[-1]["stop_loss"]
                # tp = filtered_df22.iloc[-1]["tp"]

                if check_existing_sell_stop(symbol, price):
                    print(f"❌ A {order_type} trade is already open for {symbol}. Skipping new see stop trade.")
                    return "HOLD"  # You can return whatever signal you need to indicate no trade


                place_order(symbol, volume, order_type, price, stop_loss_price=sl, take_profit_price=tp, comment="CONDITION 2_2")







def sell_conditions(df, symbol, volume, stop_loss_adjust, cross_over_date, tp):
    print("CHECKING ALL THE SELL CONDITIONS SINCE THE LAST CROSS OVER IS DOWN")
    df_2 = df.copy()
    df_2["condition2_sell"] = False  # Initialize the column with False
    df_2["condition3_sell"] = False  # Initialize the column with False
    df_2['stop_loss']=0.0
    df_2['tp']=0.0
    df_2['pending_order']=0.0


    cross_over_type = 'down'

    # check if a trade has been placed for the pair on this day
    # check_pair_trade_today(cro)

    condition_2(symbol, df_2, stop_loss_adjust, cross_over_date,volume, cross_over_type, tp, order_type='sell_stop')

    condition_3(symbol, df_2, stop_loss_adjust, cross_over_date,volume, cross_over_type, tp, order_type='sell_stop')
    
    condition_2_2(symbol, df, stop_loss_adjust, cross_over_date,volume, cross_over_type, tp, order_type='sell')


    
        

    
    
    

def buy_conditions(df, symbol, volume, stop_loss_adjust, cross_over_date):
    print("CHECKING ALL THE BUY CONDITIONS SINCE THE LAST CROSS OVER IS UP")
    df_2 = df.copy()
    df_2["condition2_sell"] = False  # Initialize the column with False
    df_2["condition3_sell"] = False  # Initialize the column with False
    df_2['stop_loss']=0.0
    df_2['tp']=0.0
    df_2['pending_order']=0.0

    cross_over_type = 'up'

    condition_2(symbol, df_2, stop_loss_adjust, cross_over_date,volume, cross_over_type, order_type='buy_stop')

    condition_3(symbol, df_2, stop_loss_adjust, cross_over_date,volume, cross_over_type, order_type='buy_stop')
    
    condition_2_2(symbol, df, stop_loss_adjust, cross_over_date,volume, cross_over_type, order_type='buy')
