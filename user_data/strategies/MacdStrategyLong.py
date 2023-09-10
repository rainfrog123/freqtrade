# Remove unnecessary imports
from freqtrade.strategy import IStrategy
from technical import qtpylib
import talib.abstract as ta

class MacdStrategyLong(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = '3m'
    can_short: bool = True

    minimal_roi = {
        "60": 10000
    }

    stoploss = -0.002
    trailing_stop = True
    startup_candle_count: int = 30

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe, metadata):
        # Calculate MACD indicators
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        return dataframe

    def populate_entry_trend(self, dataframe, metadata):
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        # Crossed above signal
        crossed_above = qtpylib.crossed_above(dataframe['macd'], dataframe['macdsignal'])
        dataframe.loc[crossed_above, 'enter_long'] = 1

        # Crossed below signal
        crossed_below = qtpylib.crossed_below(dataframe['macd'], dataframe['macdsignal'])
        dataframe.loc[crossed_below, 'enter_long'] = 1


        return dataframe

    def populate_exit_trend(self, dataframe, metadata):
        return dataframe
