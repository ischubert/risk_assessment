import numpy as np
import pandas as pd

import os, urllib.request, json, tqdm, warnings


alphavantage_data_dir = '../data/alphavantage_data/'
alpha_vantage_key = os.environ['ALPHAVANTAGEKEY']

def get_historical_data(
    symbols,
    update = False
):
    """
    reads historical stock value data from ../data and 
    downloads historical stock value data from alpha vantage
    if local copy does not exist or update = False is specified
    
    Input:
        - symbols: List of symbols of the stock values I want to get data for
        - update: Bool whether the data should be updated if it exists already
        
    Output:
        - datas: List of historical data for all symbols specified in symbols
    """
    
    datas = []
    
    for symbol in symbols:
        if already_exists(symbol):
            if update:
                datas.append(
                    download_data(symbol)
                )
            else:
                datas.append(
                    read_data(symbol)
                )
        else:
            datas.append(
                download_data(symbol)
            )
    return datas


def already_exists(symbol):
    """
    This function checks if the data for the specified symbol already exists
    
    Input:
        - symbol: symbol for which existence of downloaded data is checked
        
    Output:
        - exists: Bool indicating whether or not the file exists
    """
    return os.path.isfile(alphavantage_data_dir + symbol + '.json')


def download_data(symbol):
    """
    downloads historical stock value data for the specified ISIN
    to ../data and returns data
    
    Input:
        - symbol: symbol of the stock data is downloaded and returned for
        
    Output:
        - data: Historical stock value data for ISIN speciefied in input
    """
    
    api_call_options = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'outputsize': 'full',
        'datatype': 'json',
        'apikey': alpha_vantage_key
    }
    
    api_call_url = 'https://www.alphavantage.co/query?' + '&'.join([
        '='.join([option,api_call_options[option]]) for option in api_call_options.keys()
    ])
     
    with urllib.request.urlopen(api_call_url) as url:
        data = json.loads(url.read().decode())
        
    if 'Error Message' in data.keys():
        error_msg_string = data['Error Message']
        raise(Exception('API request returned Error Message: ' + error_msg_string))
        
    with open(alphavantage_data_dir + symbol + '.json', 'w') as outfile:
        json.dump(data, outfile)
    
    return data


def read_data(symbol):
    """
    reads historical stock value data for the specified ISIN
    from ../data
    
    Input:
        - symbol: symbol of the stock data is downloaded and returned for
        
    Output:
        - data: Historical stock value data for ISIN specified in input
    """
    
    with open(alphavantage_data_dir + symbol + '.json', 'r') as infile:
        data = json.load(infile)
    
    return data


def unpack_to_daily_df(data):
    """
    From the json data loaded from the API or the json files, this function returns a list of the days
    and a list of the corresponging values
    
    Input:
        - data: Json data from the API or the json dump
    
    Output:
        - values_df: pd.DataFrame with the day as index and a single column called 'value' containing the value.
          This dataframe is resampled daily to the nearest value found in the dataset
    """
    
    days   = [pd.to_datetime(day) for day in data['Time Series (Daily)'].keys()]
    values = [float(data['Time Series (Daily)'][day]['4. close']) for day in data['Time Series (Daily)'].keys()]
    
#     invert order: from new to old => from old to new
    days   = np.array(days[::-1])
    values = np.array(values[::-1])
    
#     throw out faulty zeros
    days_clean   = []
    values_clean = []
    
    for day, value in zip(days,values):
        if value>0:
            days_clean.append(day)
            values_clean.append(value)
    
    
    values_df = pd.DataFrame.from_records(
        np.array([days_clean,values_clean]).T,
        columns = ['day','value']
    ).set_index('day').resample('1D').nearest()
    
    return values_df


def get_pairwise_values(
    values_df,
    time_delta
):
    """
    Returns a list of tuples of closing values of a stock at a specified distance in time
    
    Input:
        - values_df: pd.DataFrame with the day as index and a single column called 'value' containing the value.
                     This dataframe is resampled daily to the nearest value found in the dataset
        - time_delta: pd.Timedelta specifying the desired time diff
        
    Output:
        - pairs_df: pd.DataFrame with the day as index, and the two columns
                    'value_original' and 'value_after_time_delta'
    """
    
    offset_values_df = values_df.set_index(values_df.index - time_delta).resample('1D').nearest()
    
    pairs_df = values_df.merge(
        offset_values_df,
        how = 'left',
        on = 'day',
        suffixes = [
            '_original',
            '_after_time_delta'
        ]
    )
    
#     drop all dates that could not be merged:
    pairs_df = pairs_df.dropna(axis = 0)
    
    return pairs_df
    
    
def calculate_risk_histogram(
    pairs_df,
    time_delta
):
    """
    returns the histogram for the effective annual growth
    after a time_delta.
    
    Input:
        - pairs_df: pd.DataFrame with the day as index, and the two columns
                    'value_original' and 'value_after_time_delta'
        - time_delta: time by which value pairs are separated
    
    Output:
        - effective_annual_growth: correspoding np.array of effective annual growths in between the pairs
    """
    
    num_years       = time_delta.total_seconds()/365/24/60/60
    
    pairs_df['relative_growth'] = pairs_df.value_after_time_delta / pairs_df.value_original
    
    effective_annual_growth = np.exp(
        np.log(pairs_df.relative_growth) / num_years
    ) - 1
    
    pairs_df['effective_annual_growth'] = np.exp(
        np.log(pairs_df.relative_growth) / num_years
    ) - 1
    
    return np.array(pairs_df.effective_annual_growth)


def calculate_risk_histogram_as_function_of_time(
    symbol,
    time_deltas
):
    """
    Function wrapper for the entire histogram extraction.
    Returns the histograms for the effective annual growth
    after a time_delta in time_deltas based on historical data.
    
    Input:
        - symbol: symbol of the stock value the histograms are calculated for
        - time_deltas: list of pd.timedelta for which for which the histograms are calculated
    
    Output:
        - histograms: List of histograms for the corresponding time_deltas in time_deltas
    """
    
    data      = get_historical_data([symbol])[0]
    values_df = unpack_to_daily_df(data)
    
#     check if requested time spans are covered
    for time_delta in time_deltas:
        if np.max(values_df.index) - np.min(values_df.index) < time_delta:
            warnings.warn(
                'Requested Time Delta is ' + str(time_delta) + ', but time span covered '\
                'by data is only ' + str(np.max(values_df.index) - np.min(values_df.index))
            )
    
    histograms = []
    for time_delta in tqdm.tqdm(time_deltas):
        pairs_df = get_pairwise_values(values_df,time_delta)
        histograms.append(
            calculate_risk_histogram(pairs_df,time_delta)
        )
    
    return histograms