import numpy as np
import pandas as pd

import os, urllib.request, json, tqdm


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
        - datas: List of historical data for all ISINs specified in ISINs
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


def unpack_to_daily_list(data):
    """
    From the json data loaded from the API or the json files, this function returns a list of the days
    and a list of the corresponging values
    
    Input:
        - data: Json data from the API or the json dump
    
    Output:
        - [days,values]: two lists: daily pd.datetime timestamps in data and corresponding closing values
    """
    
    days   = [pd.to_datetime(day) for day in data['Time Series (Daily)'].keys()]
    values = [float(data['Time Series (Daily)'][day]['4. close']) for day in data['Time Series (Daily)'].keys()]
    
#     invert order: from new to old => from old to new
    days   = np.array(days[::-1])
    values = np.array(values[::-1])
    
    return [days, values]


def get_pairwise_values(
    unpacked_data,
    time_delta
):
    """
    Returns a list of tuples of closing values of a stock at a specified distance in time
    
    Input:
        - unpacked_data: [days, values]: Tuple of Lists containing the closing values of the
                         stock at hand and the days corresponding days
        - time_delta: pd.Timedelta specifying the desired time diff
        
    Output:
        - pairwise_values: List of tuples of the form (value at t_0, value at t_0 + time_delta),
                           where t_0 is sampled in the distance of a day
    """
    
    matching_tolerance = pd.to_timedelta(10, unit = 'day')
    fail_count_treshold = 10
    
    [days,values] = unpacked_data
    pairwise_values = []
    
    fail_count = 0
    for day, value_0 in zip(days,values):
        t_0_plus_time_delta_exists = (
            np.min(
                np.abs(
                    days - (day + time_delta)
                )
            ) < matching_tolerance
        )
#         print(t_0_plus_time_delta_exists, day, day + time_delta)
        if not t_0_plus_time_delta_exists:
            fail_count += 1
            
        if t_0_plus_time_delta_exists:
            pairwise_values.append(
                [
                    value_0,
                    values[
                        np.argmin(
                            np.abs(
                                days - (day + time_delta)
                            )
                        )
                    ]
                ]
            )
            
        if fail_count > fail_count_treshold:
            break
    
    pairwise_values = np.array(pairwise_values)
    
    return pairwise_values
    
    
def calculate_risk_histogram(
    pairwise_values,
    time_delta
):
    """
    returns the histogram for the effective annual growth
    after a time_delta.
    
    Input:
        - pairwise_values: numpy array of shape (num_samples,2) for pairwise values
                           of a stock at 2 time instances separated by a constant time
                           time_delta
        - time_delta: time by which value pairs are separated
    
    Output:
        - effective_annual_growth: correspoding list of effective annual growths in between the pairs
    """
    
    relative_growth = (pairwise_values[:,1] - pairwise_values[:,0])/pairwise_values[:,0]
    num_years       = time_delta.total_seconds()/365/24/60/60
    
    effective_annual_growth = np.exp(
        np.log(relative_growth) / num_years
    ) - 1
    
    return effective_annual_growth


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
    
    data          = get_historical_data([symbol])[0]
    unpacked_data = unpack_to_daily_list(data)
    
    histograms = []
    for time_delta in tqdm.tqdm(time_deltas):
        pairwise_values = get_pairwise_values(unpacked_data,time_delta)
        histograms.append(
            calculate_risk_histogram(pairwise_values,time_delta)
        )
    
    return histograms