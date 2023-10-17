import ccxt.pro as ccxtpro
import asyncio
import nest_asyncio
import pytz
from datetime import datetime
from binance_api import api_key, api_secret
import time
import ccxt
import pandas as pd
from datetime import timedelta

# Use nest_asyncio to allow async/await code to run in Jupyter Notebook
nest_asyncio.apply()

def get_current_dataframe_and_last_5_volume_sum():
    symbol = 'ETH/USDT'

    # Create an instance of the Binance exchange
    exchange = ccxt.binance({
        'options': {
            'defaultType': 'future',  # Set the default market type to 'future'
            'newUpdates': True 
        }
    })

    # Replace 'YOUR_START_TIMESTAMP' and 'YOUR_END_TIMESTAMP' with the desired timestamps
    current_time_utc = datetime.utcnow() - timedelta(hours=1)

    # Format the current time as a string in the required format ('%Y-%m-%dT%H:%M:%SZ')
    start_time_str = current_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Parse the formatted string to create the start_timestamp
    start_timestamp = exchange.parse8601(start_time_str)
    # Fetch historical OHLCV data for the specified trading pair and timeframe
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', since=start_timestamp, limit=None)

    # Create a DataFrame from the fetched data
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df['Timestamp'] = df['Timestamp'] + timedelta(hours=8)
    df['last_5_volume_sum'] = df['Volume'].rolling(window=6, min_periods=1).sum() - df['Volume']
    last_5_volume_sum = df['last_5_volume_sum'].iloc[-1]
    # Print the DataFrame
    return df, last_5_volume_sum

async def fetch_and_print_ohlcv(exchange, symbol, df_func):
    utc_plus_8 = pytz.timezone('Asia/Shanghai')

    try:
        previous_timestamp = None  # Variable to store the previous timestamp

        while True:
            ohlcv = await exchange.watch_ohlcv(symbol, timeframe='1m')

            timestamp_utc = datetime.fromtimestamp(ohlcv[-1][0] / 1000, tz=pytz.utc)
            timestamp_utc8 = timestamp_utc.astimezone(utc_plus_8)
            current_timestamp_str = timestamp_utc8.strftime('%Y-%m-%d %H:%M:%S')
            current_volume = ohlcv[-1][5]

            # Check if the timestamp has changed
            if current_timestamp_str != previous_timestamp:
                print(f"New timestamp: {current_timestamp_str}")
                df, last_5_volume_sum = df_func()

                previous_timestamp = current_timestamp_str  # Update the previous timestamp

            if current_volume > last_5_volume_sum:
                print(f"last_5_volume_sum: {last_5_volume_sum}, current_volume: {current_volume}")

            print(f"time: {current_timestamp_str}, open: {ohlcv[-1][1]}, high: {ohlcv[-1][2]}, low: {ohlcv[-1][3]}, close: {ohlcv[-1][4]}, volume: {ohlcv[-1][5]}, last_5_volume_sum: {last_5_volume_sum:.2f}")

            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await exchange.close()

async def main():
    symbol = 'ETH/USDT'
    exchange = ccxtpro.binance({
        'options': {
            'defaultType': 'future',  # Set the default market type to 'future'
            'newUpdates': True 
        }
    })

    await fetch_and_print_ohlcv(exchange, symbol, get_current_dataframe_and_last_5_volume_sum)

# Run the async/await code in a Jupyter Notebook cell
asyncio.run(main())
