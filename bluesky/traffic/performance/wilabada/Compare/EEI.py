import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as sc
from bluesky.tools.aero import ft, vcas2tas, kts

class EEI():
    def __init__(self):
        file_directory = r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\climbPerf-20191231.txt"
        self.data = pd.read_csv(file_directory, delimiter ="\t", header = None)
        self.data.columns = ["AC Type", "Airline", "Destination", "Placeholder", "FL", "# aircraft", "IAS", "Mach",
                             "ROC Barometric", "ROC Inertial"]
        self.data["FL"] = self.data["FL"] * 20

        self.ACtypes = self.data.iloc[:,0].values
        self.Airline = self.data.iloc[:,1].values
        self.Destination = self.data.iloc[:,2].values
        self.Placeholder = self.data.iloc[:,3].values
        self.FL = self.data.iloc[:,4].values
        self.NumberAC = self.data.iloc[:,5].values
        self.IAS = self.data.iloc[:,6].values
        self.Mach = self.data.iloc[:,7].values
        self.ROCBarometric = self.data.iloc[:,8].values
        self.ROCInertial = self.data.iloc[:,9].values

        dict = {}

        # Here, self.ACtypes has the same length as the file has. Therefore, we need to create a unique set of aircraft,
        # and we check whether a dict has already been created for this aircraft type, i.e. "ACType not in dict".
        for index in range(0, len(self.ACtypes)):
            if "ZZ" in self.Destination[index]:
                continue
            if self.ACtypes[index] not in dict and "ZZ" not in self.ACtypes[index]:
                dict[self.ACtypes[index]] = {}
            if self.FL[index] not in dict[self.ACtypes[index]].keys():
                dict[self.ACtypes[index]][self.FL[index]] = {"Airline": [], "Destination": [], "Number AC": [],
                                                                   "IAS": [], "Mach": [], "ROC Barometric": [],
                                                                   "ROC Inertial": []}

            dict[self.ACtypes[index]][self.FL[index]]["Airline"].append(self.Airline[index])
            dict[self.ACtypes[index]][self.FL[index]]["Destination"].append(self.Destination[index])
            dict[self.ACtypes[index]][self.FL[index]]["Number AC"].append(self.NumberAC[index])
            dict[self.ACtypes[index]][self.FL[index]]["IAS"].append(self.IAS[index])
            dict[self.ACtypes[index]][self.FL[index]]["Mach"].append(self.Mach[index])
            dict[self.ACtypes[index]][self.FL[index]]["ROC Barometric"].append(self.ROCBarometric[index])
            dict[self.ACtypes[index]][self.FL[index]]["ROC Inertial"].append(self.ROCInertial[index])

        dict_speedsIAS = {}
        dict_speedsMach = {}
        dict_ROC = {}
        dict_speedsFL = {}
        for ACType in dict:
            dict_speedsIAS[ACType] = []
            dict_speedsFL[ACType] = []
            dict_speedsMach[ACType] = []
            dict_ROC[ACType] = []
            for FL in dict[ACType]:
                if sum(dict[ACType][FL]["Number AC"]) == 0:
                    continue
                IAS = sum([IAS * NumberAC for IAS, NumberAC in zip(dict[ACType][FL]["IAS"],
                      dict[ACType][FL]["Number AC"])])/sum(dict[ACType][FL]["Number AC"])
                dict_speedsIAS[ACType].append(IAS)

                Mach = sum([Mach * NumberAC for Mach, NumberAC in zip(dict[ACType][FL]["Mach"],
                      dict[ACType][FL]["Number AC"])])/sum(dict[ACType][FL]["Number AC"])
                dict_speedsMach[ACType].append(Mach)

                ROC = sum([ROC * NumberAC for ROC, NumberAC in zip(dict[ACType][FL]["ROC Inertial"],
                      dict[ACType][FL]["Number AC"])])/sum(dict[ACType][FL]["Number AC"])
                dict_ROC[ACType].append(ROC)

                dict_speedsFL[ACType].append(FL)

        for ACType in dict:
            dict_speedsFL[ACType], dict_speedsIAS[ACType], dict_ROC[ACType] = list(zip(*sorted(zip(dict_speedsFL[ACType], dict_speedsIAS[ACType], dict_ROC[ACType]))))

        self.speedsFL = dict_speedsFL
        self.speedsIAS = dict_speedsIAS
        self.speedsMach = dict_speedsMach
        self.ROC = dict_ROC
        self.speedfuncs = {}
        self.ROCfuncs = {}

        pop_list = []
        for ACType in dict:
            if len(dict_speedsFL[ACType]) > 2:
                self.speedfuncs[ACType] = sc.interp1d(np.array(dict_speedsFL[ACType]),
                                             np.array(self.speedsIAS[ACType]), kind="cubic")
                self.ROCfuncs[ACType] = sc.interp1d(np.array(dict_speedsFL[ACType]),
                                             np.array(self.ROC[ACType]), kind="cubic")
            else:
                pop_list.append(ACType)
        for i in pop_list:
            dict.pop(i)
        self.dict = dict

    def speeds(self, ACType, alt):
        IASlst = []
        for i in range(len(ACType)):
            success = False
            try:
                IAS = self.speedfuncs[ACType[i]](alt[i]/ft/100)
                success = True
            except:
                IASlst.append(False)
            if success:
                IASlst.append(IAS)
        IASlst = np.array(IASlst)
        return IASlst

    def ROCf(self, ACType, alt):
        ROClst = []
        for i in range(len(ACType)):
            success = False
            try:
                ROC = self.ROCfuncs[ACType[i]](alt[i]/ft/100)
                success = True
            except:
                ROClst.append(False)
            if success:
                ROClst.append(ROC)
        ROClst = np.array(ROClst)
        return ROClst