# from OUTBOUND_FUNCS import *
import psutil
import glob as glob
from multiprocessing import Pool, Process, Manager
import pandas as pd
import time
import os
from pathlib import Path
import numpy as np
from copy import deepcopy
import pickle
import warnings
warnings.filterwarnings('ignore')
pd.set_option("display.max_rows", None, "display.max_columns", None)
# pd.set_option("max_columns", None) # show all cols
# pd.set_option('max_colwidth', None) # show full width of showing cols
# pd.set_option("expand_frame_repr", False)

# folder = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Compare\Surr"
FP_file = "fp2019-202209"
# FP_file = "fp20190101"
SUR_header = list(pd.read_csv("artas.fields", sep=";").columns)
# folder = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Outbound_data\SUR_Files"
folder = r"C:\DATA"

maxfl = 100
stepsize = 3

def read_csv(filename):
    """"
    Function required in order to utilize multiple threads.

    """
    frame_id = os.path.split(filename)[-1]
    frame_id = frame_id.split("_")[0] + "_" + frame_id.split("_")[1] + "_" + frame_id.split("_")[2]
    usecols = ["acid", "alt", "tas", "ias", "cROCD"]
    data = pd.read_csv(filename, names=SUR_header, sep = ";", dtype={"alt": float})#, "cROCD": float})

    data = data.drop([column for column in SUR_header if column not in usecols], axis=1)

    if data.dtypes["cROCD"] == object:
        for index, row in data.iterrows():
            if row["cROCD"].count('.') == 2:
                data.at[index, "cROCD"] = ".".join(row["cROCD"].split('.')[:2])
        data["cROCD"] = pd.to_numeric(data["cROCD"], downcast = "float")

    data = data[~(data["alt"] > 100) & ~(data["cROCD"] <= 0) & ~(data["ias"] < 90)]
    data = data.round({"alt": 0})
    data["alt"] = data["alt"].astype(int).apply(lambda x: round_stepsize(x, stepsize))

    data["diff"] = data["ias"].diff()
    df1 = data[~(data["ias"] < 210) & ~(data["ias"] > 230)]
    df2 = df1[~(df1["diff"] > 5)]
    if len(df2) > 5:
        data = data[~(data["ias"] > 210)]

    data = data.drop(columns = ["diff"])
    data = data.reset_index(drop = True)

    return data, frame_id

def SUR_import():
    """
    Leuke comment hier.

    Returns:

    """
    start = time.time()
    file_list = glob.glob(folder + "/**/*.sur", recursive = True)
    print("Starting to import", len(file_list), "SUR files.")

    num_cpus = psutil.cpu_count()

    with Pool(processes=num_cpus) as pool:
        df_list, framenames = zip(*pool.map(read_csv, file_list))

    print("It took me", round(time.time()-start, 1), "[s] to import", len(file_list), "files.")

    return df_list, framenames


def read_csv_V2(filenamelist):
    """"
    Function required in order to utilize multiple threads.

    """
    dataL = []
    framenames = []
    for filename in filenamelist:
        frame_id = os.path.split(filename)[-1]
        frame_id = frame_id.split("_")[0] + "_" + frame_id.split("_")[1] + "_" + frame_id.split("_")[2]
        framenames.append(frame_id)
        usecols = ["acid", "alt", "tas", "ias", "cROCD"]
        data = pd.read_csv(filename, names=SUR_header, sep = ";", dtype={"alt": float})#, "cROCD": float})

        data = data.drop([column for column in SUR_header if column not in usecols], axis=1)

        if data.dtypes["cROCD"] == object:
            for index, row in data.iterrows():
                if row["cROCD"].count('.') == 2:
                    data.at[index, "cROCD"] = ".".join(row["cROCD"].split('.')[:2])
            data["cROCD"] = pd.to_numeric(data["cROCD"], downcast = "float")

        data = data[~(data["alt"] > 100) & ~(data["cROCD"] <= 0) & ~(data["ias"] < 90)]
        data = data.round({"alt": 0})
        data["alt"] = data["alt"].astype(int)

        data = data.reset_index(drop = True)
        dataL.append(data)

    return dataL, framenames

def SUR_import_V2():
    """
    Leuke comment hier.

    Returns:

    """
    start = time.time()
    file_list = glob.glob(folder + "/**/*.sur", recursive = True)
    print("Starting to import", len(file_list), "SUR files.")

    num_cpus = psutil.cpu_count()
    file_list = np.array_split(file_list, num_cpus)

    with Pool(processes=int(num_cpus)) as pool:
        df_list, framenames = zip(*pool.map_async(read_csv_V2, file_list))

    print("It took me", round(time.time()-start, 1), "[s] to import the SUR files.")

    return df_list, framenames

def FP_data():
    """
    Leuke comment hier.
    """
    print("Starting to import flight plan data.")

    usecols = ["idx", "time", "acid", "dest", "number_of_aircraft", "a_c_type", "trwy", "SID_id", "sfpl_id"]

    start = time.time()
    names = list(pd.read_csv("hdr.fpdata", sep=";").columns)
    data = pd.read_csv(FP_file, names=names, sep=";", dtype={"old_dest": str, "idx": str, "sfpl_id": str})
    data = data[data['SID_id'].apply(lambda x: isinstance(x, str))]

    data = data.drop([column for column in names if column not in usecols], axis = 1)
    data["idx"] = data["idx"].str[:-4]
    data["framenames"] = data[["idx", "acid", "sfpl_id"]].agg("_".join, axis=1)

    months = data["idx"].str[:-2].unique().tolist()

    data_lst = [data[data["idx"].str.startswith(month)].reset_index() for month in months]

    print("It took me", round(time.time() - start, 1), "[s] to import and split the FP data to SIDs only.")

    return data, data.loc[:, "framenames"], months, data_lst



def round_stepsize(x, stepsize):
    return int(stepsize * round(float(x)/stepsize))

def combine(FP_months, FP_lst, SUR_data, SUR_acids):
    print("Starting to combine dataframes per aircraft type one dataframe")
    start = time.time()

    AC_lst = []
    AC_data = []
    AC_dict = {}

    for index in range(len(SUR_data)):
        if index%100==0:
            print(index)
        SUR_dataframe = SUR_data[index]
        CO_month = SUR_acids[index].split("_")[0][:-2]

        FP_rows = FP_lst[FP_months.index(CO_month)]

        FP_AC_row = FP_rows.loc[FP_rows["framenames"] == SUR_acids[index]].reset_index()

        if SUR_dataframe.empty or FP_AC_row.empty:
            continue

        AC_type = FP_AC_row.at[0, "a_c_type"]
        AC_dest = FP_AC_row.at[0, "dest"]
        AC_airline = SUR_dataframe.at[0, "acid"][:3]
        AC_rwy = FP_AC_row.at[0, "trwy"]
        AC_date = FP_AC_row.at[0, "framenames"].split("_")[0]
        SUR_dataframe = SUR_dataframe.assign(dest = [AC_dest for num in range(len(SUR_dataframe))],
                                             airline = [AC_airline for num in range(len(SUR_dataframe))],
                                             rwy = [AC_rwy for num in range(len(SUR_dataframe))],
                                             date = [AC_date for num in range(len(SUR_dataframe))])

        if AC_type not in AC_lst:
            AC_data.append(pd.DataFrame())
            AC_lst.append(AC_type)
            AC_dict[AC_type] = [pd.DataFrame()]
        AC_dict[AC_type].append(SUR_dataframe)


    for AC_type in AC_lst:
        AC_data[AC_lst.index(AC_type)] = pd.concat(AC_dict[AC_type])

    print("Finished combining all data into one dataframe in", round(time.time()-start,1), "[s]")

    return AC_data, AC_lst


def country_dict(destinations, countries):
    dict = {}

    for i in destinations:
        country_df = countries.loc[countries["ident"] == i].reset_index()
        # print(country_df)
        if country_df.empty:
            dict[i] = "ZZ"
            continue
        country = country_df.at[0, "iso_country"]
        if "US/" in country:
            country = "US"
        dict[i] = country

    return dict

def continent(countries, continents):
    dict = {}
    for i in countries:
        if pd.isnull(i):
            continue
        continent_df = continents.loc[continents["two_code"] == i.replace(" ", "")].reset_index()
        if continent_df.empty:
            dict[i] = "ZZ"
            continue
        dict[i] = continent_df.at[0, "continent"]
    return dict

def split_V2(AC_data_lst, AC_lst):
    print("Started splitting data")
    start = time.time()
    counter = 0

    airports = pd.read_csv(r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\data\navdata\airports.dat",
                           skiprows=0, usecols=[0, 6], sep=',')
    airports = pd.read_csv(r"D:\airports.csv", sep=',', usecols = [1, 8])
    continents = pd.read_csv(r"countries.txt", sep = '\t')
    AC_all_types_of_data = []

    for i in AC_data_lst:
        AC = AC_lst[counter]

        i = i.drop_duplicates(['alt', 'framename'], keep='last')
        destinations = i["dest"].unique()
        lst = country_dict(destinations, airports)
        # i["country"] = i["dest"].apply(lambda x: countries.loc[countries["# code"] == x].reset_index().at[0, " country code"])
        i["country"] = i["dest"].apply(lambda x: lst[x].replace(" ", "") if lst[x] != None else np.NaN)
        countries = i["country"].unique()
        lst = continent(countries, continents)
        i["continent"] = i["country"].apply(lambda x: lst[x] if type(x) != float else None)

        df_ACtype = i.groupby(["alt"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline = i.groupby(["airline", "alt"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline_dest = i.groupby(["airline", "dest", "alt"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_dest = i.groupby(["dest", "alt"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_dest_country = i.groupby(["country", "alt"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_continent = i.groupby(["continent", "alt"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline_country = i.groupby(["country", "alt", "airline"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline_continent = i.groupby(["continent", "alt", "airline"]).mean().reset_index().assign().round(
            {"cROCD": 2, "ias": 1, "tas": 1})

        df_ACtype["ac_type"] = AC
        df_ACtype_airline["ac_type"] = AC
        df_ACtype_airline_dest["ac_type"] = AC
        df_ACtype_dest["ac_type"] = AC
        df_ACtype_dest_country["ac_type"] = AC
        df_ACtype_continent["ac_type"] = AC
        df_ACtype_airline_country["ac_type"] = AC
        df_ACtype_airline_continent["ac_type"] = AC



        df_ACtype["data_type"] = "TT"
        df_ACtype_airline["data_type"] = "TA"
        df_ACtype_airline_dest["data_type"] = "TAD"
        df_ACtype_dest["data_type"] = "TD"
        df_ACtype_dest_country["data_type"] = "TCOU"
        df_ACtype_continent["data_type"] = "TCON"
        df_ACtype_airline_country["data_type"] = "TADL"
        df_ACtype_airline_continent["data_type"] = "TADC"

        counter = counter + 1

        AC_all_types_of_data.append(df_ACtype)
        AC_all_types_of_data.append(df_ACtype_airline)
        AC_all_types_of_data.append(df_ACtype_airline_dest)
        AC_all_types_of_data.append(df_ACtype_dest)
        AC_all_types_of_data.append(df_ACtype_dest_country)
        AC_all_types_of_data.append(df_ACtype_continent)
        AC_all_types_of_data.append(df_ACtype_airline_country)
        AC_all_types_of_data.append(df_ACtype_airline_continent)

    # Create csv based on aircraft type, airline and destination.
    pd.concat(AC_all_types_of_data).reset_index(drop = True).to_csv("AC_DATA.csv", sep = '\t')



    print("Finished splitting after", time.time()-start, "[s]")
    # print(pd.concat(AC_all_types_of_data).reset_index(drop = True))

def split_V3(AC_data_lst, AC_lst):
    print("Started splitting data")
    start = time.time()
    counter = 0

    airports = pd.read_csv(r"D:\airports.csv", sep=',', usecols = [1, 8], keep_default_na=False)
    # print(airports)
    continents = pd.read_csv(r"countries.txt", sep = '\t', keep_default_na=False)
    # print(continents)
    AC_all_types_of_data = []

    for i in AC_data_lst:
        AC = AC_lst[counter]

        # i = i.drop_duplicates(['alt', 'framename'], keep='last')
        destinations = i["dest"].unique()
        lst = country_dict(destinations, airports)

        print("{}, which is number {} of {}.".format(AC, counter, len(AC_lst)))

        i["country"] = i["dest"].apply(lambda x: lst[x] if lst[x] != None else None)
        countries = i["country"].unique()
        lst = continent(countries, continents)
        i["continent"] = i["country"].apply(lambda x: lst[x] if type(x) != float else None)

        df_ACtype_temp = i.groupby(["alt"])
        df_ACtype_keys = df_ACtype_temp.groups.keys()
        df_ACtype = df_ACtype_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype["num_ac"] = [len(df_ACtype_temp.get_group(key)) for key in df_ACtype_keys]

        df_ACtype_airline_temp = i.groupby(["airline", "alt"])
        df_ACtype_airline_keys = df_ACtype_airline_temp.groups.keys()
        df_ACtype_airline = df_ACtype_airline_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline["num_ac"] = [len(df_ACtype_airline_temp.get_group(key)) for key in df_ACtype_airline_keys]

        df_ACtype_airline_dest_temp = i.groupby(["airline", "dest", "alt"])
        df_ACtype_airline_dest_keys = df_ACtype_airline_dest_temp.groups.keys()
        df_ACtype_airline_dest = df_ACtype_airline_dest_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline_dest["num_ac"] = [len(df_ACtype_airline_dest_temp.get_group(key)) for key in df_ACtype_airline_dest_keys]

        df_ACtype_dest_temp = i.groupby(["dest", "alt"])
        df_ACtype_dest_keys = df_ACtype_dest_temp.groups.keys()
        df_ACtype_dest = df_ACtype_dest_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_dest["num_ac"] = [len(df_ACtype_dest_temp.get_group(key)) for key in df_ACtype_dest_keys]

        df_ACtype_dest_country_temp = i.groupby(["country", "alt"])
        df_ACtype_dest_country_keys = df_ACtype_dest_country_temp.groups.keys()
        # print(df_ACtype_dest_country_keys)
        df_ACtype_dest_country = df_ACtype_dest_country_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_dest_country["num_ac"] = [len(df_ACtype_dest_country_temp.get_group(key)) for key in df_ACtype_dest_country_keys]

        df_ACtype_continent_temp = i.groupby(["continent", "alt"])
        df_ACtype_continent_temp_keys = df_ACtype_continent_temp.groups.keys()
        df_ACtype_continent = df_ACtype_continent_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_continent["num_ac"] = [len(df_ACtype_continent_temp.get_group(key)) for key in df_ACtype_continent_temp_keys]

        df_ACtype_airline_country_temp = i.groupby(["country", "alt", "airline"])
        df_ACtype_airline_country_keys = df_ACtype_airline_country_temp.groups.keys()
        df_ACtype_airline_country = df_ACtype_airline_country_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline_country["num_ac"] = [len(df_ACtype_airline_country_temp.get_group(key)) for key in df_ACtype_airline_country_keys]

        df_ACtype_airline_continent_temp = i.groupby(["continent", "alt", "airline"])
        df_ACtype_airline_continent_keys = df_ACtype_airline_continent_temp.groups.keys()
        df_ACtype_airline_continent = df_ACtype_airline_continent_temp.mean().reset_index().assign().round({"cROCD": 2, "ias": 1, "tas": 1})
        df_ACtype_airline_continent["num_ac"] = [len(df_ACtype_airline_continent_temp.get_group(key)) for key in df_ACtype_airline_continent_keys]

        df_ACtype["ac_type"] = AC
        df_ACtype_airline["ac_type"] = AC
        df_ACtype_airline_dest["ac_type"] = AC
        df_ACtype_dest["ac_type"] = AC
        df_ACtype_dest_country["ac_type"] = AC
        df_ACtype_continent["ac_type"] = AC
        df_ACtype_airline_country["ac_type"] = AC
        df_ACtype_airline_continent["ac_type"] = AC

        df_ACtype["data_type"] = "TT"
        df_ACtype_airline["data_type"] = "TA"
        df_ACtype_airline_dest["data_type"] = "TAD"
        df_ACtype_dest["data_type"] = "TD"
        df_ACtype_dest_country["data_type"] = "TCOU"
        df_ACtype_continent["data_type"] = "TCON"
        df_ACtype_airline_country["data_type"] = "TADL"
        df_ACtype_airline_continent["data_type"] = "TADC"

        counter = counter + 1

        AC_all_types_of_data.append(df_ACtype)
        AC_all_types_of_data.append(df_ACtype_airline)
        AC_all_types_of_data.append(df_ACtype_airline_dest)
        AC_all_types_of_data.append(df_ACtype_dest)
        AC_all_types_of_data.append(df_ACtype_dest_country)
        AC_all_types_of_data.append(df_ACtype_continent)
        AC_all_types_of_data.append(df_ACtype_airline_country)
        AC_all_types_of_data.append(df_ACtype_airline_continent)

    # Create csv based on aircraft type, airline and destination.
    CSV = pd.concat(AC_all_types_of_data).reset_index(drop = True)
    CSV = CSV[~(CSV["num_ac"] < 5)]
    CSV.to_csv("AC_DATA_S3.csv", sep = '\t')

    print("Finished splitting after", time.time()-start, "[s]")
    # print(pd.concat(AC_all_types_of_data).reset_index(drop = True))


if __name__ == '__main__':
    # Returns flight plan of departing aircraft with a Standard Instrument Departure in one dataframe. Also returns all
    # acids (i.e. date+callsign+sfpl_id) in FP_acids.
    FP_data, FP_acids, FP_months, FP_lst = FP_data()

    # Returns list of dataframes. One dataframe per SUR file. Also returns all acids (i.e. date+callsign+sfpl_id) in
    # SUR_acids.
    # SUR_data, SUR_acids = SUR_import_V2()
    SUR_data, SUR_acids = SUR_import()

    pickle.dump(FP_data, open("FP_S_data.p", "wb"))
    pickle.dump(FP_acids, open("FP_S_acids.p", "wb"))
    pickle.dump(FP_months, open("FP_S_months.p", "wb"))
    pickle.dump(FP_lst, open("FP_S_lst.p", "wb"))
    pickle.dump(SUR_data, open("SUR_S_data.p", "wb"))
    pickle.dump(SUR_acids, open("SUR_S_acids.p", "wb"))

    # COMBINE_multithread(FP_months, FP_lst, SUR_data, SUR_acids)
    # Returns dataframes per aircraft
    AC_data, AC_lst = combine(FP_months, FP_lst, SUR_data, SUR_acids)


    # print(AC_data)
    pickle.dump(AC_data, open("AC_S_data.p", "wb"))
    pickle.dump(AC_lst, open("AC_S_lst.p", "wb"))
    # AC_data = pickle.load(open("AC_data.p", "rb"))
    # AC_lst = pickle.load(open("AC_lst.p", "rb"))

    # split_V2(AC_data, AC_lst)
    split_V3(AC_data, AC_lst)

