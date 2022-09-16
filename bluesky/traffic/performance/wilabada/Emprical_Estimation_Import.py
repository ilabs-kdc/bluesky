import pandas as pd
import numpy as np

class ESI():
    def __init__(self):
        self.data = pd.read_csv('climbPerf-20191231.txt', delimiter = "\t", header = None)
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

    def sort(self):
        dict = {}

        # Here, self.ACtypes has the same length as the file has. Therefore, we need to create a unique set of aircraft,
        # and we check whether a dict has already been created for this aircraft type, i.e. "ACType not in dict".
        for index in range(0, len(self.ACtypes)):
            if self.ACtypes[index] not in dict and "ZZ" not in self.ACtypes[index]:
                dict[self.ACtypes[index]] = {}
            if "ZZ" in self.Destination[index]:
                continue
            if self.FL[index] not in dict[self.ACtypes[index]].keys():
                dict[self.ACtypes[index]][self.FL[index]] = {"Airline": [], "Destination": [], "Number AC": [],
                                                                   "IAS": [], "Mach": [], "ROC Barometric": [],
                                                                   "ROC Inertial": []}

            dict[self.ACtypes[index]][self.FL[index]]["Airline"].append(self.Airline[index])
            dict[self.ACtypes[index]][self.FL[index]]["Destination"].append(self.Destination[index])
            dict[self.ACtypes[index]][self.FL[index]]["Number AC"].append(self.NumberAC[index])
            dict[self.ACtypes[index]][self.FL[index]]["IAS"].append(self.IAS[index])
            # dict[self.ACtypes[index]][self.FL[index]]["Mach"].append(self.Mach[index])
            # dict[self.ACtypes[index]][self.FL[index]]["ROC Barometric"].append(self.ROCBarometric[index])
            # dict[self.ACtypes[index]][self.FL[index]]["ROC Inertial"].append(self.ROCInertial[index])

        return dict

    def general(self):
        dict = self.sort()
        dict_speeds = {}
        for ACType in dict:
            dict_speeds[ACType] = {}
            for FL in dict[ACType]:
                if sum(dict[ACType][FL]["Number AC"]) == 0:
                    continue
                IAS = sum([IAS * NumberAC for IAS, NumberAC in zip(dict[ACType][FL]["IAS"],
                      dict[ACType][FL]["Number AC"])])/sum(dict[ACType][FL]["Number AC"])
                dict_speeds[ACType][FL] = IAS
        for i in dict_speeds:
            print(i, dict_speeds[i])





A = ESI()
A.general()