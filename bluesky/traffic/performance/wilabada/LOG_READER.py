import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

fpm = 0.00508

file_1 = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\output\UIT.log"
file_2 = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\output\AAN.log"
file_2 = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\output\LOG1__20220922_11-57-30.log"
file_3 = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\output\LOG1__20220922_13-58-29.log"

def LOG_READER(file):
    data = pd.read_csv(file, sep=",", header = 1)
    sw = True
    for name in range(len(list(data.columns))):
        if sw == True:
            data.rename(columns={list(data.columns)[name]: list(data.columns)[name].replace("#", " ").strip()},
                        inplace=True)
            sw = False
        else:
            data.rename(columns = {list(data.columns)[name]: list(data.columns)[name].strip()}, inplace=True)

    NumAC = len(set(data.iloc[:,1].values))
    AllAC = list(set(data.iloc[:,1].values))

    data_dict = {}
    for column_i in range(len(list(data.columns))):
        data_dict[list(data.columns)[column_i]] = data.iloc[:,column_i].values

    data_dict_ac = {}

    if NumAC > 1:
        print("I assume that the data has ", len(AllAC), "aircraft.")
        for line in range(len(data_dict[list(data.columns)[0]])):
            AC = data_dict["id"][line]
            if AC not in data_dict_ac:
                data_dict_ac[AC] = {}
                for column in list(data.columns):
                    data_dict_ac[AC][column] = []
            for column in list(data.columns):
                data_dict_ac[AC][column].append(data_dict[column][line])
                if column == "vs":
                    if "fpm" not in data_dict_ac[AC]:
                        data_dict_ac[AC]["fpm"] = []
                    data_dict_ac[AC]["fpm"].append(data_dict[column][line]/fpm)
                if column == "alt":
                    if "FL" not in data_dict_ac[AC]:
                        data_dict_ac[AC]["FL"] = []
                    data_dict_ac[AC]["FL"].append(data_dict[column][line]/0.3048/100)
    elif NumAC < 1:
        raise Exception("I've found no aircraft in your log.")
    else:
        print("I assume that the data has 1 aircraft.")
        for column in list(data.columns):
            data_dict_ac[column] = []
        for line in range(len(data_dict[list(data.columns)[0]])):
            for column in list(data.columns):
                data_dict_ac[column].append(data_dict[column][line])
                if column == "vs":
                    if "fpm" not in data_dict_ac:
                        data_dict_ac["fpm"] = []
                    data_dict_ac["fpm"].append(data_dict[column][line]/fpm)
                if column == "alt":
                    if "FL" not in data_dict_ac:
                        data_dict_ac["FL"] = []
                    data_dict_ac["FL"].append(data_dict[column][line]/0.3048/100)

    return data_dict_ac

print(LOG_READER(file_2))

# two = True
# linewidth = 3
#
# data = LOG_READER(file_1)
# time = np.array(data['simt'])-data['simt'][0]
# alt = data["alt"]
# vs = data["fpm"]
#
# fig, axs = plt.subplots(2)
# axs[0].plot(time, alt, label = "data_1", linewidth = linewidth)
# axs[1].plot(time, vs, label = "data_2", linewidth = linewidth)
#
# if two:
#     data = LOG_READER(file_2)
#     time = np.array(data['simt']) - data['simt'][0]
#     alt = data["alt"]
#     vs = data["fpm"]
#
#     axs[0].plot(time, alt, label = "data_1", linestyle = "dashed", linewidth = linewidth)
#     axs[1].plot(time, vs, label = "data_2", linestyle = "dashed", linewidth = linewidth)
#
# axs[0].title.set_text("Altitude")
# axs[1].title.set_text("VS [fpm]")
#
# plt.legend()
# plt.show()