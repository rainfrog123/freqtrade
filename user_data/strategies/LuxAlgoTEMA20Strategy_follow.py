# --- Do not remove these libs ---
import numpy as np  # noqa
from datetime import datetime, timedelta
import pandas as pd  # noqa
from pandas import DataFrame
from typing import Optional, Union

# Import necessary libraries
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter, 
                                IStrategy, IntParameter)
from freqtrade.optimize.space import Categorical, Dimension, Integer, SKDecimal

class LuxAlgoTEMA20Strategy_follow(IStrategy):
    INTERFACE_VERSION = 3

    # Set default timeframe and allow shorting
    timeframe = '1m'
    can_short: bool = True

    # Define minimal ROI and stoploss settings
    minimal_roi = {
        "0" : 10000
    }
    stoploss = -0.0023
    trailing_stop = True
    startup_candle_count: int = 30

    # Optimal for the strategy
    tema_window_size = IntParameter(10, 25, default=20, space='buy', optimize=True)

    class HyperOpt:
        # Define a custom stoploss space.
        def stoploss_space():
            return [SKDecimal(-0.0035, -0.001, decimals=4, name='stoploss')]
        
    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                proposed_leverage: float, max_leverage: float, entry_tag: Optional[str], side: str,
                **kwargs) -> float:
        return 125.0  # Default leverage for other cases

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
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        # Calculate consecutive trend duration
        is_rising_tema = dataframe['tema'] > dataframe['tema'].shift()
        is_falling_tema = dataframe['tema'] < dataframe['tema'].shift()

        # Set default window size
        tema_window_size = 10
        if self.tema_window_size.value:
            tema_window_size = self.tema_window_size.value

        # Calculate consecutive rising and falling bars for tema
        dataframe['consecutive_bars_raising_tema'] = is_rising_tema.rolling(window=tema_window_size + 1).sum() == tema_window_size
        dataframe['consecutive_bars_falling_tema'] = is_falling_tema.rolling(window=tema_window_size + 1).sum() == tema_window_size

        # Entry logic for short and long conditions using lambda functions
        short_conditions = lambda df: df['consecutive_bars_falling_tema']
        long_conditions = lambda df: df['consecutive_bars_raising_tema']

        # Populate entry signals
        dataframe['enter_short'] = short_conditions(dataframe).astype(int)
        dataframe['enter_long'] = long_conditions(dataframe).astype(int)

        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        """
        Populate exit signals based on TA indicators.

        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with exit columns populated
        """

        return dataframe
