import requests
import os
import datetime
import zipfile
from tqdm import tqdm
import pandas as pd
import feather

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

        for current_date in (start_date + datetime.timedelta(n) for n in range((end_date - start_date).days + 1)):
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

                    # Transfer to Feather format
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
                # df = self._convert_to_seconds(df)
                combined_df = pd.concat([combined_df, df]) if combined_df is not None else df
            progress_bar.update(1)

        progress_bar.close()
        return combined_df

    def delete_all_data(self):
        os.system(f'rm -rf {self.zip_download_dir}')
        os.system(f'rm -rf {self.csv_extract_dir}')
        os.system(f'rm -rf {self.feather_stored_dir}')

# Example usage:
base_url = 'https://data.binance.vision/data/futures/um/daily/aggTrades/ETHUSDT/'
zip_download_dir = '/allah/freqtrade/Orange_project/aggTrades/binance_aggTrades'
csv_extract_dir = '/allah/freqtrade/Orange_project/aggTrades/decompressed_csv'
feather_stored_dir = '/allah/freqtrade/Orange_project/aggTrades/feather_data'

data_processor = DataProcessor(base_url, zip_download_dir, csv_extract_dir, feather_stored_dir)
start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2023, 10, 16)

# Download, extract, and featherize data
# data_processor.download_and_extract_and_feather_data(datetime.date(2022, 6, 1), datetime.date(2023, 10, 20))

# # Combine selected Feather files to a DataFrame
combined_df = data_processor.combine_from_feather_to_df(feather_stored_dir, datetime.date(2023, 10, 14), datetime.date(2023, 10, 15))

# # Perform operations with combined_df as needed.

import pandas as pd
from datetime import datetime
import feather

# combined_df = data_processor.combine_from_feather_to_df(feather_stored_dir, datetime.date(2023, 4, 13), datetime.date(2023, 5, 16))

def format_and_save_dataframe(input_df, output_path):
    # Create a copy of the input DataFrame
    df_formatted = input_df.copy()

    # Define the end time for your time series
    end_time = datetime.strptime('2023-10-16 23:00:00', '%Y-%m-%d %H:%M:%S')

    # Create a new index based on a range with 1-minute frequency
    new_index = pd.date_range(end=end_time, periods=len(df_formatted), freq='1T')

    # Assign the new index to the DataFrame and rename columns
    df_formatted.index = new_index
    df_formatted = df_formatted.rename(columns={'': 'real_1s'})

    # Reset the index to make the 'date' column a regular column
    df_formatted = df_formatted.reset_index()

    # Rename and format columns to match the target format
    df_formatted['date'] = df_formatted['index']
    df_formatted['volume'] = df_formatted['quantity']
    # df_formatted['date'] = pd.to_datetime(df_formatted['date']).dt.strftime('%Y-%m-%d %H:%M:%S') + '+00:00'
    df_formatted['date'] = pd.to_datetime(df_formatted['date'])

    df_formatted_temp = df_formatted[['date','real_1s','open', 'high', 'low', 'close', 'volume', 'first_trade_id', 'last_trade_id', 'agg_trade_id', 'is_buyer_maker']]

    df_formatted = df_formatted[['date', 'open', 'high', 'low', 'close', 'volume']]

    # Save the formatted DataFrame to a Feather file
    # feather.write_dataframe(df_formatted, output_path)
    df_formatted.to_feather(
            output_path, compression_level=9, compression='lz4')
    return df_formatted_temp
# Usage
input_df = combined_df.copy()  # Replace with your actual DataFrame
output_path = '/allah/freqtrade/user_data/data/binance/futures/BTC_USDT_USDT-1m-futures.feather'
df_formatted_temp = format_and_save_dataframe(input_df, output_path)
df_formatted_temp[['real_1s']].to_feather('/allah/freqtrade/user_data/strategies/real_1s.feather')

df_test = df_formatted_temp.copy()
df_test.drop("date", axis=1, inplace=True)
import pandas as pd


# Convert the 'real_1s' column to datetime objects
df_test['real_1s'] = pd.to_datetime(df_test['real_1s'])

# Sort the DataFrame by 'real_1s'
df_test = df_test.sort_values(by='real_1s')

# Define a function to calculate the aggregated sum for each minute
def calculate_aggregated_sum(df):
    return df['volume'].cumsum() 
    # return df['volume'].cumsum() - df['volume']

# Apply the function to the DataFrame
df_test['aggregate_volume_sum'] = df_test.groupby(df_test['real_1s'].dt.strftime('%Y-%m-%d %H:%M')).apply(calculate_aggregated_sum).values
# df_test['last_3_minutes_volumes_sum'] = 
# print(df_test)

# df_test
def calculate_volumes_sum(df):
    return df['volume'].sum()

# Group the last three minutes and apply the function
result = df_test.groupby(df_test['real_1s'].dt.strftime('%Y-%m-%d %H:%M')).apply(calculate_volumes_sum)

# Create a new DataFrame from the result Series
result_df = pd.DataFrame(result, columns=['current_minute_volume'])

print(result_df)


pd.dataframe(result)