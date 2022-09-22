import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

fpm = 0.00508

file = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\output\LOG1__20220922_10-24-00.log"

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

    data_dict = {}
    for column_i in range(len(list(data.columns))):
        data_dict[list(data.columns)[column_i]] = data.iloc[:,column_i].values
        if list(data.columns)[column_i] == "vs":
            data_dict["fpm"] = data.iloc[:, column_i].values/fpm
    return data_dict

print(LOG_READER(file))


# time = np.array(data['simt'])-data['simt'][0]
# alt = data['alt']
# vs = data['vs']/fpm
#
# fig, axs = plt.subplots(2)
#
# axs[0].plot(time, alt)
# axs[1].plot(time, vs)
# plt.show()