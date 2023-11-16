# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class LuxAlgoTEMA20Strategy(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = '1m'
    can_short: bool = True

    minimal_roi = {
        # "0": 0.001,
        "60": 100000
    }

    stoploss = -0.002
    trailing_stop = True
    startup_candle_count: int = 30

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe, metadata):
        """
        Calculate TEMA indicators and consecutive trend duration.

        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with indicators populated
        """
        # Calculate TEMA indicators
        timeperiod_tema = 50
        dataframe['tema'] = ta.TEMA(dataframe, timeperiod=timeperiod_tema)

        # Calculate consecutive trend duration
        is_rising = dataframe['tema'] > dataframe['tema'].shift()
        is_falling = dataframe['tema'] < dataframe['tema'].shift()

        window_size = 20
        dataframe['consecutive_bars_raising'] = is_rising.rolling(window=window_size + 1).sum() == window_size
        dataframe['consecutive_bars_falling'] = is_falling.rolling(window=window_size + 1).sum() == window_size

        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        """
        Based on TA indicators, populates the entry signal for the given dataframe.

        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        # Your entry logic here
        short_condition = (dataframe['consecutive_bars_raising']) & (dataframe['tema'] < dataframe['tema'].shift())
        long_condition = (dataframe['consecutive_bars_falling']) & (dataframe['tema'] > dataframe['tema'].shift())

        # Populate entry signals
        dataframe['enter_short'] = short_condition.astype(int)
        dataframe['enter_long'] = long_condition.astype(int)

        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        """
        Populate exit signals based on TA indicators.

        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """
        # Your exit logic here
        dataframe[dataframe['consecutive_bars_raising'] == True]
        dataframe[dataframe['consecutive_bars_falling'] == True]
        dataframe[dataframe['enter_long'] == 1]
        dataframe['consecutive_bars_raising']
        return dataframe
