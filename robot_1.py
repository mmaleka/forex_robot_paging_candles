# -*- coding: utf-8 -*-

print("starting script")

import time
import MetaTrader5 as mt5
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np

from utilities import get_forex_data, check_signal
from forex import get_account_info


# List all the pairs to monitor-

currency_pairs = {
    "Volatility 10 Index": {"volume": 0.5, "stop_loss_adjust": 2000, "tp": 5.0}, #done tp = 5 #
    "Volatility 25 Index": {"volume": 0.5, "stop_loss_adjust": 2000, "tp": 3.0}, #done tp = 3 #
    "Volatility 50 Index": {"volume": 4.0, "stop_loss_adjust": 2000, "tp": 10.0}, #done tp = 10 #
    "Volatility 75 Index": {"volume": 0.005, "stop_loss_adjust": 1000, "tp": 5.0}, #done tp = 5 #
    "Volatility 100 Index": {"volume": 0.5, "stop_loss_adjust": 2000 , "tp": 5.0},  #done tp = 5 #
    "Volatility 10 (1s) Index": {"volume": 0.5, "stop_loss_adjust": 2000, "tp": 5.0}, #done tp = 5 #
    "Volatility 25 (1s) Index": {"volume": 0.005, "stop_loss_adjust": 2000, "tp": 10.0},#done tp = 10 #
    "Volatility 50 (1s) Index": {"volume": 0.005, "stop_loss_adjust": 2000, "tp": 10.},#done tp = 10 #
    "Volatility 75 (1s) Index": {"volume": 0.001, "stop_loss_adjust": 2000, "tp": 2.0}, #done tp = 2 #
    "Volatility 100 (1s) Index": {"volume": 0.5, "stop_loss_adjust": 2000, "tp": 2.0}, #done tp = 2 #
    "Volatility 150 (1s) Index": {"volume": 0.01, "stop_loss_adjust": 2000, "tp": 5.0}, #done tp = 5 #
    "Jump 10 Index": {"volume": 0.01, "stop_loss_adjust": 2000, "tp": 3.0}, #done tp = 3 #
    "Jump 100 Index": {"volume": 0.01, "stop_loss_adjust": 2000, "tp": 1.}, #done tp = 1 #
    "Jump 75 Index": {"volume": 0.01, "stop_loss_adjust": 2000, "tp": 1.0}, #done tp = 1 #
    "Drift Switch Index 30": {"volume": 0.02, "stop_loss_adjust": 2000, "tp": 1.0}, #done tp = 1 #
    "Drift Switch Index 20": {"volume": 0.02, "stop_loss_adjust": 2000, "tp": 1.0}, #done tp = 1 #
    "Drift Switch Index 10": {"volume": 0.02, "stop_loss_adjust": 2000, "tp": 1.0}, #done tp = 1 #
    "Step Index": {"volume": 0.1, "stop_loss_adjust": 2000, "tp": 5.0}, #done tp = 5 #
}


# TimeFrame_ = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15, mt5.TIMEFRAME_M30, mt5.TIMEFRAME_H1]
timeframe = mt5.TIMEFRAME_M5


while True:
    # loop through each pair to find a trade
    for pair in currency_pairs:
        print(pair, currency_pairs[pair]['volume'], currency_pairs[pair]['stop_loss_adjust'])

        # # now loop through each time frame
        # for timeframe in TimeFrame_:
        #     print(f"searching for trades on {timeframe}")
        volume = currency_pairs[pair]['volume']
        stop_loss_adjust = currency_pairs[pair]['stop_loss_adjust']
        tp = currency_pairs[pair]['tp']
        df = get_forex_data(pair, timeframe)
        signal = check_signal(df, pair, volume, stop_loss_adjust, timeframe, tp)
        # print(f"Signal for {pair}: {signal}")
    
    print("Waiting for 5 seconds before next check...\n")
    time.sleep(5)  # Wait for 60 seconds before checking again




















