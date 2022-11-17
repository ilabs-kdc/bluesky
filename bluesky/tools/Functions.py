import psycopg2
import pandas as pd
from math import floor, ceil


def Connect_SQL_DB(dbname):
    """
        Function:   Makes a connection to a SQL database
        Args:
            - dbname: Name of the database with which a connection must be made
        Returns:
            - Connection

        Created by: Stijn Brunia
        Date: 1-11-2021
    """
    conn = psycopg2.connect(
        host="localhost",
        database=dbname,
        user="postgres",
        password="lucht_2")
    return conn

def query_DB_to_DF(dbname, query):
    """
        Function: Queries data from a SQL database and puts this into a python dataframe
        Args:
            - dbname: Name of the database in which the data is stored
            - query: The query that is used to get the correct data from the database
        Returns:
            - df: dataframe with the data queried from the database

        Created by: Stijn Brunia
        Date: 1-11-2021
        """
    conn = Connect_SQL_DB(dbname)
    sql_query = pd.read_sql_query(query, conn)
    df = pd.DataFrame(sql_query, columns=['timestamp_data', 'timestamp_prediction', 'lon', 'lat', 'alt', 'uwind', 'vwind'])
    return df

def find_datapoint_timeframe(df, point):
    """
        Function:   Function that finds the data values in a specific point, using interpolation over datapoints, in
                    three dimensions, in altitude, longitude and latitude.
        Args:
            - df: dataframe with the needed data
            - point: The point at which the data is needed, provided in [time, alt, lat, lon]
        Returns:
            - The data at a specific point, provided in [time, alt, lat, lon, uwind, vwind]

        Created by: Stijn Brunia
        Date: 21-10-2021
    """
    lon_min  = floor(point[3] * 10) / 10
    lon_plus = ceil(point[3]  * 10) / 10
    lat_min  = floor(point[2] * 10) / 10
    lat_plus = ceil(point[2]  * 10) / 10

    value_mmm, value_pmm = find_height_levels(df, point, lat_min, lon_min)
    value_mmp, value_pmp = find_height_levels(df, point, lat_min, lon_plus)
    value_mpm, value_ppm = find_height_levels(df, point, lat_plus, lon_min)
    value_mpp, value_ppp = find_height_levels(df, point, lat_plus, lon_plus)

    timeless_value  = interpolation(value_mmm, value_mmp, value_mpm, value_mpp, value_pmm, value_pmp, value_ppm, value_ppp, point[1], point[2], point[3])
    value           = [point[0], timeless_value[0], timeless_value[1], timeless_value[2], timeless_value[3], timeless_value[4]]
    return value

def find_height_levels(df, point, lat, lon):
    """
        Function:   Function that finds the specific height levels at which the datapoints are located. This is needed
                    because the data does not have the same height levels at different lon/lat combinations.
        Args:
            - df: dataframe with the needed data
            - point: The point at which the data is needed, provided in [time, alt, lat, lon], this function uses the alt
            - lat: The latitude of the datapoint that is needed
            - lon: The longitude of the datapoint that is needed
        Returns:
            - Two points, in [time, alt, lat, lon, uwind, vwind], between which altitude interpolation will be performed.

        Created by: Stijn Brunia
        Date: 23-10-2021
    """
    df_t = df.query('lat == ' + str(lat) + ' and lon ==' + str(lon))
    layer_min = layer_plus = -1
    value_m = value_p = -1
    for i in range(len(df_t)):
        if point[1] > df_t.iloc[i][4]:
            if i - 1 >= 0:
                layer_min = i
                layer_plus = i - 1
                break
    if layer_min != -1 and layer_plus != -1:
        value_m = [df_t.iloc[layer_min][4], lat, lon, df_t.iloc[layer_min][5], df_t.iloc[layer_min][6]]
        value_p = [df_t.iloc[layer_plus][4], lat, lon, df_t.iloc[layer_plus][5], df_t.iloc[layer_plus][6]]
    return value_m, value_p

def interpolation(value_mmm, value_mmp, value_mpm, value_mpp, value_pmm, value_pmp, value_ppm, value_ppp, alt, lat, lon):
    """
            Function:   Function that interpolated over alt, lat and lon, between 8 points.
            Args:
                - value_mmm (and variations): the 8 datapoint which are used for the interpolation [time, alt, lat, lon, uwind, vwind]
                - alt: The altitude value of the datapoint that is needed
                - lat: The latitude value of the datapoint that is needed
                - lon: The longitude value of the datapoint that is needed
            Returns:
                - The wanted datapoint, in [time, alt, lat, lon, uwind, vwind], that has been retrieved via interpolation.

            Created by: Stijn Brunia
            Date: 23-10-2021
    """

    if value_mmm != -1 and value_mmp != -1 and value_mpm != -1 and value_mpp != -1 and value_pmm != -1 and value_pmp != -1 and value_ppm != -1 and value_ppp != -1:
        value_mm = [value_mmm[0], value_mmm[1], lon, interpolate(lon, value_mmm[2], value_mmp[2], value_mmm[3], value_mmp[3]), interpolate(lon, value_mmm[2], value_mmp[2], value_mmm[4], value_mmp[4])]
        value_mp = [value_mpm[0], value_mpm[1], lon, interpolate(lon, value_mpm[2], value_mpp[2], value_mpm[3], value_mpp[3]), interpolate(lon, value_mpm[2], value_mpp[2], value_mpm[4], value_mpp[4])]
        value_pm = [value_pmm[0], value_pmm[1], lon, interpolate(lon, value_pmm[2], value_pmp[2], value_pmm[3], value_pmp[3]), interpolate(lon, value_pmm[2], value_pmp[2], value_pmm[4], value_pmp[4])]
        value_pp = [value_ppm[0], value_ppm[1], lon, interpolate(lon, value_ppm[2], value_ppp[2], value_ppm[3], value_ppp[3]), interpolate(lon, value_ppm[2], value_ppp[2], value_ppm[4], value_ppp[4])]

        value_m  = [value_mm[0], lat, lon, interpolate(lat, value_mm[1], value_mp[1], value_mm[3], value_mp[3]), interpolate(lat, value_mm[1], value_mp[1], value_mm[4], value_mp[4])]
        value_p  = [value_pm[0], lat, lon, interpolate(lat, value_pm[1], value_pp[1], value_pm[3], value_pp[3]), interpolate(lat, value_pm[1], value_pp[1], value_pm[4], value_pp[4])]

        value    = [alt, lat, lon, round(interpolate(alt, value_m[0], value_p[0], value_m[3], value_p[3]),4), round(interpolate(alt, value_m[0], value_p[0], value_m[4], value_p[4]),4)]

    else:
        value = [alt, lat, lon, 0, 0]
    return value

def interpolate(value , value_a , value_b, answer_a , answer_b):
    """
        Function:   The function that actually performs the interpolation
        Args:
            - value: The x at which y is needed
            - value_a: The first x below the needed x, at which y is known
            - value_b: The first x above the needed x, at which y is known
            - answer_a: The y value at value_a
            - answer_b: The y value at value_b
        Returns:
            - answer: The y at value

        Created by: Stijn Brunia
        Date: 23-10-2021
    """
    if value_a != value_b:
        answer = (value - value_a)/(value_b - value_a) * (answer_b-answer_a) + answer_a
        return answer
    return answer_a

def time_interpolation(timefrac , answer_a , answer_b):
    """
        Function:   Function that interpolates over time
        Args:
            - timefrac: The fraction of the difference between the wanted point and first known point a, over the difference
                        between known points a and b.
            - answer a: The known value at point a
            - answer b: The known value at point b
        Returns:
            - The wanted value, interpolated over time between point a and b

        Created by: Stijn Brunia
        Date: 23-10-2021
    """
    answer = timefrac * (answer_b-answer_a) + answer_a
    return answer

def utc2stamps(utc):
    """
        Function:   Function that translates the system utc to the needed timestamp
        Args:
            - utc: The system utc time, in yyyy-mm-dd hh:mm:ss
        Returns:
            - stamp1: The first available timestamp with data below the current utc
            - stamp2: The first available timestamp with data above the current utc

        Created by: Stijn Brunia
        Date: 11-11-2021
    """
    utc     = str(utc)
    day     = utc[8:10]
    month   = utc[5:7]
    year    = utc[0:4]
    hour    = utc[11:13]
    minutes = utc[14:16]

    stamp1 = year[2:] + month + day + hour + minutes[0]
    if int(minutes[0]) < 5:
        stamp2 = str(int(stamp1) + 1)
    else:
        stamp2 = str(int(stamp1) + 10 - int(minutes[0]))
        if int(stamp2[6:8]) > 23:
            stamp2 = str(int(stamp2) + 760 )
            days = days_in_month(int(stamp2[2:4]), int("20" + stamp2[0:2]))
            if int(stamp2[4:6]) > days:
                stamp2 = str(int(stamp2) + 100000 - days*1000)
                if int(stamp2[2:4]) > 12:
                    stamp2 = str(int(stamp2) +8800000)
    return stamp1, stamp2

def utc2frac(utc, stamp):
    """
        Function:   Function that translates the system utc to the time fration of the difference between the wanted point and first known point a, over the difference
                        between known points a and b.
        Args:
            - utc: The system utc time, in yyyy-mm-dd hh:mm:ss
            - stamp: The timestamp of the first known datapoint below the current utc
        Returns:
            - frac: The fraction of the difference between the wanted point and first known point a, over the difference
                    between known points a and b.

        Created by: Stijn Brunia
        Date: 11-11-2021
    """
    utc             = str(utc)
    stamp           = str(stamp)
    minutes_utc     = utc[14:16]
    seconds_utc     = utc[17:19]
    minutes_stamp   = stamp[8] + "0"
    d_minutes       = int(minutes_utc) - int(minutes_stamp)
    d_seconds       = int(d_minutes) * 60 + int(seconds_utc)
    frac            = d_seconds/600

    return frac

def days_in_month(month, year):
    """
        Function:   Function that tells the number of days in a month, when giving the month and year
        Args:
            - month: The month of which you want to know the number of days in it
            - year: The year of this specific month, needed for leap years
        Returns:
            - days: The number of days in this specific month

        Created by: Stijn Brunia
        Date: 11-11-2021
    """
    days = 31;
    if month == 2:
        days = 28;
        if floor(year / 4) == (year / 4):
            days = 29
    if month == 4:
        days = 30
    if month == 6:
        days = 30
    if month == 9:
        days = 30
    if month == 11:
        days = 30
    return days