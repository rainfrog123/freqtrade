import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import IStrategy
from freqtrade.optimize.space import SKDecimal

class ChangePointTrendStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '15m'
    can_short: bool = True
    minimal_roi = {"60": 10000}
    stoploss = -0.007
    trailing_stop = True
    startup_candle_count: int = 30

    def informative_pairs(self):
        """Define pairs for additional data. Currently none used."""
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Calculate indicators used by the strategy."""
        dataframe['tema'] = ta.TEMA(dataframe, timeperiod=50)
        dataframe['trend'] = np.where(
            dataframe['tema'] > dataframe['tema'].shift(1), 'UP',
            np.where(dataframe['tema'] < dataframe['tema'].shift(1), 'DOWN', 'STABLE')
        )
        dataframe['trend_change'] = dataframe['trend'] != dataframe['trend'].shift(1)
        dataframe['trend_change_point'] = dataframe['trend_change'] & (dataframe['trend'] != 'STABLE')
        dataframe['trend_group'] = dataframe['trend_change_point'].cumsum()
        dataframe['trend_duration'] = dataframe.groupby('trend_group').cumcount() + 1
        last_trend_durations = dataframe.groupby('trend_group')['trend_duration'].transform('last')
        dataframe['trend_duration'] = np.where(
            dataframe['trend_change_point'], last_trend_durations.shift(1), None
        )

        dataframe['last_trend_durations'] = dataframe.groupby('trend_group')['trend_duration'].transform('last')
        dataframe['last_trend_durations'] = dataframe['last_trend_durations'].shift(1)
        dataframe['last_trend_durations'] = np.where(
            dataframe['trend_change_point'], dataframe['last_trend_durations'], None
        )
        threshold_1 = 5
        threshold_2 = 5
        threshold_3 = 5
        threshold_4 = 5

        dataframe['state'] = np.where(
            (dataframe['trend_duration'] <= 5) & (dataframe['last_trend_durations'] <= 5),
            'locked',
            np.where(
                (dataframe['trend_duration'] >= 5) & (dataframe['last_trend_durations'] >= 5),
                'unlocked',
                'inherit'
            )
        )

        # Propagate the previous valid state for rows where state should be inherited
        valid_state = dataframe['state'].replace('inherit', np.nan)
        dataframe['state'] = valid_state.fillna(method='ffill').fillna('locked')  # Default to 'locked' if no prior state exists

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Define conditions for entering trades."""
        dataframe.loc[
            (dataframe['trend_change_point']) & (dataframe['trend'] == 'UP') & (dataframe['state'] == 'unlocked'),
            'enter_long'] = 1
        dataframe.loc[
            (dataframe['trend_change_point']) & (dataframe['trend'] == 'DOWN') & (dataframe['state'] == 'unlocked'),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Define conditions for exiting trades if needed."""
        return dataframe

    class HyperOpt:
        @staticmethod
        def stoploss_space():
            return [SKDecimal(-0.015, -0.001, decimals=4, name='stoploss')]

        # Define custom ROI space if needed
