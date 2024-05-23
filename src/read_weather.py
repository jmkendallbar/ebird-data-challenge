import pandas as pd
import datetime
import os


def get_weather_data(home_dir,selected_columns= ['datetime', 'wind_speed', 'daily_precipitation']):  
    '''
    get the weather data

    Parameters
    ----------
    home_dir : home direction of the data.
    selected_columns : list of column names requested, optional
        The default is ['datetime', 'wind_speed', 'daily_precipitation'].

    Returns
    -------
    result_df : dataFrame
        contains the requested columns.

    returns warning if any required columns is missing
    '''
   
    # read csv
    file_hourly_weather = os.path.join(home_dir,'swamp_hourly_weather.csv')
    hourly_weather = pd.read_csv(file_hourly_weather)
    file_daily_weather = os.path.join(home_dir,'swamp_daily_weather.csv')
    daily_weather = pd.read_csv(file_daily_weather)
    
    hourly_weather['datetime'] = pd.to_datetime(hourly_weather[['year', 'month', 'day', 'hour']])
    daily_weather['datetime'] = pd.to_datetime(daily_weather['date'], format='%Y-%m-%d')
    
    # rename columns in daily_weather
    daily_weather = daily_weather.rename(columns=lambda x: 'daily_' + x \
        if x not in ['date', 'datetime','year','month','day'] else x)
    
    # expand hourly data to daily
    expanded_rows = []
    for _, row in daily_weather.iterrows():
        date = row['datetime']
        for hour in range(24):
            hourly_row = row.copy()
            hourly_row['datetime'] = date + datetime.timedelta(hours=hour)
            expanded_rows.append(hourly_row)
    
    expanded_daily_weather = pd.DataFrame(expanded_rows)
    
    # merge two DataFrame and select the columns
    merged_weather = pd.merge(hourly_weather, expanded_daily_weather, on='datetime', suffixes=('_hourly', '_daily'))
    
    # check missing columns
    missing_columns = [col for col in selected_columns if col not in merged_weather.columns]
    if missing_columns:
        print(f"Warning: The following columns are missing: {missing_columns}")
    
    # get the required columns
    final_columns = [col for col in selected_columns if col in merged_weather.columns]
    result_df = merged_weather[final_columns]
    
    return result_df




if __name__ == "__main__":
    home_dir = r'C:\Users\lkong\OneDrive\Documents\Research Laptop\meeting notes\2024.5 Merlin Dataset\umich_swamp_aru_anaylsis'
    selected_columns = ['datetime', 'wind_speed', 'daily_precipitation','air_tempp']

    result_df = get_weather_data(home_dir,selected_columns)
    print(result_df.head())