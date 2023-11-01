from typing import Any, Dict
import os
from datetime import timedelta, datetime
import zipfile
from tqdm import tqdm
import pandas as pd
import feather
import argparse
import requests
from freqtrade.configuration import TimeRange

class DataProcessor:
    def __init__(self, base_url, zip_download_dir, csv_extract_dir, feather_stored_dir):
        self.base_url = base_url
        self.zip_download_dir = zip_download_dir
        self.csv_extract_dir = csv_extract_dir
        self.feather_stored_dir = feather_stored_dir

    def download_file(self, url, destination):
        if os.path.exists(destination):
            print(f"File {destination} already exists. Skipping download.")
            return
        response = requests.get(url)
        if response.status_code == 200:
            with open(destination, 'wb') as file:
                file.write(response.content)

    def download_and_extract_and_feather_data(self, start_date, end_date):
        os.makedirs(self.zip_download_dir, exist_ok=True)
        os.makedirs(self.csv_extract_dir, exist_ok=True)
        os.makedirs(self.feather_stored_dir, exist_ok=True)
        download_bar = tqdm(total=(end_date - start_date).days + 1, desc="Downloading, Extracting, and Featherizing")

        for current_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
            date_str = current_date.strftime('%Y-%m-%d')
            zip_url = f'{self.base_url}ETHUSDT-aggTrades-{date_str}.zip'
            zip_filename = os.path.join(self.zip_download_dir, f'ETHUSDT-aggTrades-{date_str}.zip')

            self.download_file(zip_url, zip_filename)

            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    extracted_file_path = os.path.join(self.csv_extract_dir, file_info.filename)

                    if not os.path.exists(extracted_file_path):
                        zip_ref.extract(file_info, path=self.csv_extract_dir)
                    else:
                        print(f"File {extracted_file_path} already exists. Skipping extraction.")

                    csv_file_path = extracted_file_path
                    feather_file_path = os.path.join(self.feather_stored_dir, f"{os.path.splitext(file_info.filename)[0]}.feather")
                    self.transfer_to_feather(csv_file_path, feather_file_path)

            download_bar.update(1)
        download_bar.close()

    def transfer_to_feather(self, csv_file_path, feather_file_path):
        if not os.path.exists(feather_file_path):
            df = pd.read_csv(csv_file_path)
            df = self._convert_to_seconds(df)
            df.to_feather(feather_file_path)
        else:
            print(f"Feather file for {csv_file_path} already exists. Skipping transfer.")

    def _convert_to_seconds(self, df):
        df['utc_time'] = pd.to_datetime(df['transact_time'], unit='ms')
        df.set_index('utc_time', inplace=True)

        resampled_df = df.resample('S').agg({
            'agg_trade_id': 'first',
            'price': 'ohlc',
            'quantity': 'sum',
            'first_trade_id': 'first',
            'last_trade_id': 'last',
            'is_buyer_maker': 'last',
        })
        resampled_df.reset_index(inplace=True)
        resampled_df.columns = resampled_df.columns.droplevel()
        resampled_df.fillna(method='ffill', inplace=True)
        resampled_df.fillna(method='bfill', inplace=True)

        return resampled_df

    def combine_from_feather_to_df(self, data_dir, start_date, end_date):
        data_files = [file for file in os.listdir(data_dir) if file.endswith('.feather')]
        data_files.sort()
        combined_df = None
        progress_bar = tqdm(total=len(data_files), desc="Combining Feather Files")

        for data_file in data_files:
            date_str = '-'.join(data_file.split('-')[-3:]).replace('.feather', '')
            file_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

            if start_date <= file_date <= end_date:
                data_path = os.path.join(data_dir, data_file)
                df = pd.read_feather(data_path)
                combined_df = pd.concat([combined_df, df]) if combined_df is not None else df
            progress_bar.update(1)

        progress_bar.close()
        return combined_df
    
    def _binance_feather_name(self, ticker, timeframe):
        return f'{ticker}-{timeframe}.feather'

    def save_to_binance_data_dir(self, start_date, end_date, ticker, timeframe):
        df = self.combine_from_feather_to_df(self.feather_stored_dir, start_date, end_date)
        feather_path = os.path.join(self.binance_data_stored_dir, self._binance_feather_name(ticker, timeframe))
        df.to_feather(feather_path)


    def delete_all_data(self):
        os.system(f'rm -rf {self.zip_download_dir}')
        os.system(f'rm -rf {self.csv_extract_dir}')
        os.system(f'rm -rf {self.feather_stored_dir}')


def start_download_1s_data(args: Dict[str, Any]) -> int:
    base_url = 'https://data.binance.vision/data/futures/um/daily/aggTrades/ETHUSDT/'
    zip_download_dir = '/allah/freqtrade/Orange_project/aggTrades/binance_aggTrades'
    csv_extract_dir = '/allah/freqtrade/Orange_project/aggTrades/decompressed_csv'
    feather_stored_dir = '/allah/freqtrade/Orange_project/aggTrades/feather_data'
    binance_data_stored_dir = '/allah/freqtrade/user_data/data/binance/futures'

    data_processor = DataProcessor(base_url, zip_download_dir, csv_extract_dir, feather_stored_dir)

    timerange = TimeRange()
    if 'days' in args:
        time_since = (datetime.now() - timedelta(days=args['days'])).strftime("%Y%m%d")
        time_until = datetime.now().strftime("%Y%m%d")
        timerange = TimeRange.parse_timerange(f'{time_since}-{time_until}')
        start_date = datetime.fromtimestamp(timerange.startts).date()
        end_date = datetime.fromtimestamp(timerange.stopts).date()

    try:
        data_processor.download_and_extract_and_feather_data(start_date, end_date)
        data_processor.save_to_binance_data_dir(feather_stored_dir, start_date, end_date)
    except Exception as e:
        print(e)
    return 0
