# -*- coding: utf-8 -*-

# Import necessary libraries
import numpy as np
import talib


def initialize(context):
    # Define Symbol
    context.security = symbol('CASH,EUR,USD')

    # Define stop-loss and take-profit thesholds
    context.stop_loss_threshold = 0.02
    context.take_profit_threshold = 0.03

    context.stop_loss = np.nan
    context.take_profit = np.nan

    context.position = 0

    schedule_function(square_off,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close(minutes=2))


def handle_data(context, data):

    # Fetch 1 day data for the above security
    prices = data.history(
        context.security, ['open', 'high', 'low', 'close'], 60, '1m')

    # Calculate the Average True Range(ATR)
    prices['ATR'] = talib.ATR(prices['high'], prices['low'],
                              prices['close'], timeperiod=30)

    # Calculate the rolling mean of ATR
    prices['ATR_MA_5'] = prices['ATR'].rolling(5).mean()

    # Flag the minutes where ATR breaks out its rolling mean
    ATR_breakout = prices['ATR'][-1] > prices['ATR_MA_5'][-1]

    # Check if the fourth candle is higher than the highest of the previous 3 candle
    four_candle_high = prices.iloc[-1, 1] >= prices.iloc[-4:, 1].max()

    # Check if the fourth candle is lower than the lowest of the previous 3 candles
    four_candle_low = prices.iloc[-1, 2] <= prices.iloc[-4:, 2].min()

    # Long entry and exit condition
    long_entry = ATR_breakout and four_candle_high
    long_exit = prices['close'][-1] < context.stop_loss or prices['close'][-1] > context.take_profit

    # Short entry and exit condition
    short_entry = ATR_breakout and four_candle_low
    short_exit = prices['close'][-1] > context.stop_loss or prices['close'][-1] < context.take_profit

    # Place the order
    if long_entry and context.position == 0:
        order(context.security, 100)
        context.position = 1
        print('Long Entry')
        context.stop_loss = prices['close'][-1] * (1-context.stop_loss_threshold)
        context.take_profit = prices['close'][-1] * (1+context.take_profit_threshold)

    elif short_entry and context.position == 0:
        order(context.security, -100)
        context.position = -1
        print('Short Entry')
        context.stop_loss = prices['close'][-1] * (1+context.stop_loss_threshold)
        context.take_profit = prices['close'][-1] * (1-context.take_profit_threshold)

    elif long_exit and context.position == 1:
        order_target_percent(context.security, 0)
        context.position = 0
        print('Long Exit')
        context.stop_loss = np.nan
        context.take_profit = np.nan

    elif short_exit and context.position == -1:
        order_target_percent(context.security, 0)
        context.position = 0
        print('Short Exit')
        context.stop_loss = np.nan
        context.take_profit = np.nan


def square_off(context, data):
    # Exit Position
    if ~context.position == 0:
        order_target_percent(context.security, 0)
        context.position = 0
        print('Close Position')
        context.stop_loss = np.nan
        context.take_profit = np.nan