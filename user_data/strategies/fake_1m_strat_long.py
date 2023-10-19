# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib

class fake_1m_strat_long(IStrategy):

    INTERFACE_VERSION = 3

    timeframe = '1m'

    # Can this strategy go shoart?
    can_short: bool = True

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0": 0.0006
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.001

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        import feather
        data_from_feather = feather.read_dataframe('/allah/freqtrade/user_data/strategies/real_1s.feather')
        dataframe['real_1s'] = data_from_feather['real_1s']
        class DataFrameProcessor:
            def __init__(self, df):
                self.df = df

            def prepare_dataframe(self):
                df_copy = self.df.copy()
                df_copy.drop("date", axis=1, inplace=True)
                df_copy['real_1s'] = pd.to_datetime(df_copy['real_1s'])
                df_copy = df_copy.sort_values(by='real_1s')
                return df_copy

            def calculate_aggregated_sum(self, df):
                return df['volume'].cumsum()

            def aggregate_minute_data(self):
                aggregated_data = self.df.groupby(self.df['real_1s'].dt.strftime('%Y-%m-%d %H:%M')).apply(self.calculate_aggregated_sum)
                return aggregated_data

            def calculate_volumes_and_open_sum(self, df):
                return pd.Series({
                    'current_minute_volume': df['volume'].sum(),
                    'open_price': df['open'].iloc[0]
                })

            def process_data(self):
                df_test = self.prepare_dataframe()
                df_test['aggregate_volume_sum'] = df_test.groupby(df_test['real_1s'].dt.strftime('%Y-%m-%d %H:%M')).apply(self.calculate_aggregated_sum).values
                df_1m_aggregated = df_test.groupby(df_test['real_1s'].dt.strftime('%Y-%m-%d %H:%M')).apply(self.calculate_volumes_and_open_sum)
                df_1m_aggregated = df_1m_aggregated.reset_index()
                df_1m_aggregated.columns = ['real_1s', 'current_minute_volume', 'open_price']
                df_1m_aggregated['last_3_minutes_volumes_sum'] = df_1m_aggregated['current_minute_volume'].rolling(4).sum() - df_1m_aggregated['current_minute_volume']
                df_test['last_3_minutes_volumes_sum'] = df_test['real_1s'].dt.strftime('%Y-%m-%d %H:%M').map(df_1m_aggregated.set_index('real_1s')['last_3_minutes_volumes_sum'])
                df_test['open_price'] = df_test['real_1s'].dt.strftime('%Y-%m-%d %H:%M').map(df_1m_aggregated.set_index('real_1s')['open_price'])
                df_test['entry'] = 0
                condition = df_test['aggregate_volume_sum'] > df_test['last_3_minutes_volumes_sum']
                condition = condition & (condition != condition.shift(1))
                df_test.loc[condition, 'entry'] = 1
                return df_test

        # Usage
        df_processor = DataFrameProcessor(dataframe)
        dataframe = df_processor.process_data()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with entry columns populated
        """
        # return dataframe    
        condition_long = (dataframe['entry'] == 1) & (dataframe['close'] > dataframe['open_price'])
        condition_short = (dataframe['entry'] == 1) & (dataframe['close'] < dataframe['open_price'])

        dataframe.loc[condition_long, 'enter_long'] = 1
        
        # dataframe.loc[condition_short, 'enter_short'] = 1


        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        return dataframe

