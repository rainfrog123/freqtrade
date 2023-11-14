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
        "60": 100000
    }

    stoploss = -0.004
    trailing_stop = True
    startup_candle_count: int = 30

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe, metadata):
        # Calculate TEMA indicators
        timeperiod_tema = 50
        tema = ta.TEMA(dataframe, timeperiod=timeperiod_tema)
        dataframe['tema'] = tema

        # Calculate previous trend duration
        timeperiod_trend_duration = 20
        previous_trend_duration = ta.sum(dataframe['tema'] > dataframe['tema'].shift(), timeperiod=timeperiod_trend_duration)
        dataframe['previous_trend_duration'] = previous_trend_duration

        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        # Your entry logic here
        dataframe.loc[
            (
                (dataframe['tema'] > dataframe['tema'].shift()) &
                (dataframe['previous_trend_duration'] >= 1)
            ),
            'entry'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        # Your exit logic here
        return dataframe
