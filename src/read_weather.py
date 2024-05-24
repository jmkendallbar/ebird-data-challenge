import pandas as pd
import os
import datetime

from astral.sun import sun
from astral import Observer

import pytz
from timezonefinder import TimezoneFinder

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

def get_sun_data(home_dir,my_site_num,dates):
    #file_daily_weather = os.path.join(home_dir,'swamp_aru_recorder_info.csv')
    #daily_weather = pd.read_csv(file_daily_weather)
    file_sensors = os.path.join(home_dir,'swamp_aru_recorder_info.csv')
    data_sensors = pd.read_csv(file_sensors)

    latitude, longitude = data_sensors.loc[data_sensors['site_num'] == my_site_num, ['latitude', 'longitude']].values[0]
    
    
    # determine time zone
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
    if timezone_str is None:
       print(f"Warning: Time Zone cannot be determined.")
    tz = pytz.timezone(timezone_str)
    
    
    observer = Observer(latitude, longitude)
    sun_data_list = []
    for date in dates:
        sun_info = sun(observer, date=date)
        
        # correct the time zone
        sun_info = {k: v.astimezone(tz) if isinstance(v, datetime.datetime) else v for k, v in sun_info.items()}
        sun_info['date'] = date
        sun_data_list.append(sun_info)

    # change list to df
    sun_data_df = pd.DataFrame(sun_data_list)
    columns = ['date'] + [col for col in sun_data_df.columns if col != 'date']
    sun_data_df = sun_data_df[columns]
    
    return sun_data_df


if __name__ == "__main__":
    home_dir = r'..\data\umich_swamp_aru_anaylsis'
    output_dir = os.path.join(home_dir,'outputs')
    selected_columns = ['datetime', 'wind_speed', 'daily_precipitation','air_tempp']

    weather_df = get_weather_data(home_dir,selected_columns)
    print(weather_df.head())
    weather_df.to_csv(os.path.join(output_dir, 'weather_selected_data.csv'))
    
    my_site_num  = 21 
    # these sites are so close to each other. so here I just chose a random one 
    unique_dates = weather_df['datetime'].dt.date.unique()
    sun_df = get_sun_data(home_dir,my_site_num,unique_dates)
    sun_df.to_csv(os.path.join(output_dir, 'sun_data.csv'))
    
    
