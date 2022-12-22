import pandas as pd
import scipy.interpolate as sc
import numpy as np
import os
from bluesky import settings

settings.set_variable_defaults(perf_path_WILABADA = 'data/performance/WILABADA')

class EEI:
    def __init__(self):
        '''
        Definition: (Purpose of the class)
        Methods:
            method_name_1(): (Purpose of method 1)
            method_name_2(): (Purpose of method 2)
            ...

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''
        file = 'WILABADA_TAKE_OFF_PERFORMANCE.csv'

        try:
            file = os.path.join(settings.perf_path_WILABADA, file)
        except:
            raise FileNotFoundError("Error, could not find file {}.".format(file))

        data = pd.read_csv(file, sep='\t')
        data = data.groupby(["data_type"])
        self.TAD = data.get_group("TAD").reset_index(drop=True)
        self.TADL = data.get_group("TADL").reset_index(drop=True)
        self.TADC = data.get_group("TADC").reset_index(drop=True)
        self.TA = data.get_group("TA").reset_index(drop=True)
        self.TD = data.get_group("TD").reset_index(drop=True)
        self.TCOU = data.get_group("TCOU").reset_index(drop=True)
        self.TCON = data.get_group("TCON").reset_index(drop=True)
        self.TT = data.get_group("TT").reset_index(drop=True)

        self.TADG = self.TAD.groupby(["ac_type", "airline", "dest"])
        self.TADLG = self.TADL.groupby(["ac_type", "airline", "country"])
        self.TADCG = self.TADC.groupby(["ac_type", "airline", "continent"])
        self.TAG = self.TA.groupby(["ac_type", "airline"])
        self.TDG = self.TD.groupby(["ac_type", "dest"])
        self.TCOUG = self.TCOU.groupby(["ac_type", "country"])
        self.TCONG = self.TCON.groupby(["ac_type", "continent"])
        self.TTG = self.TT.groupby(["ac_type"])

        self.ac_airline_dest = self.TADG.groups.keys()
        self.ac_airline_country = self.TADLG.groups.keys()
        self.ac_airline = self.TAG.groups.keys()
        self.ac_airline_continent = self.TADCG.groups.keys()
        self.ac_dest = self.TDG.groups.keys()
        self.ac_country = self.TCOUG.groups.keys()
        self.ac_continent = self.TCONG.groups.keys()

        # self.AC_types = self.TT['ac_type'].unique()
        self.AC_types = self.TAD['ac_type'].unique()

        self.airports = pd.read_csv(os.path.join(settings.perf_path_WILABADA, 'WILABADA_AIRPORTS.csv'), sep=',', usecols = [1, 8])

        self.continents = pd.read_csv(os.path.join(settings.perf_path_WILABADA, 'WILABADA_COUNTRIES.txt'), sep ='\t')
        self.continents["two_code"] = self.continents["two_code"].apply(lambda x: x if not pd.isnull(x) else "NA")

        self.kind = "linear"
        self.kts = 0.514444
        self.fpm = 0.3048/60

    def select(self, ID, AC_type, **kwargs):
        if "dest" in kwargs:
            country = self.airports.loc[self.airports["ident"] == kwargs["dest"]].reset_index()

            if len(country) > 0:
                country = country.at[0, "iso_country"]
                continent = self.continents.loc[self.continents["two_code"] == country].reset_index().at[0, "continent"]
            else:
                country = None
                continent = None

        swA = False
        swT = False
        min_datapoints = 20

        if "airline" in kwargs:
            if "dest" in kwargs:
                if (AC_type, kwargs["airline"], kwargs["dest"]) in self.ac_airline_dest:
                    if len(self.TADG.get_group((AC_type, kwargs["airline"], kwargs["dest"]))) > min_datapoints:
                        print("{} ({}) uses airline and airport specific data to {}.".format(ID, AC_type, kwargs["dest"]))
                        return self.TADf(AC_type, kwargs["airline"], kwargs["dest"])
                if (AC_type, kwargs["airline"], country) in self.ac_airline_country:
                    if len(self.TADLG.get_group((AC_type, kwargs["airline"], country))) > min_datapoints:
                        print("{} ({}) is defaulting to airline and country ({}) specific data".format(ID, AC_type, country))
                        return self.TADLf(AC_type, kwargs["airline"], country)
                if (AC_type, kwargs["airline"], continent) in self.ac_airline_continent:
                    if len(self.TADCG.get_group((AC_type, kwargs["airline"], continent))) > min_datapoints:
                        print("{} ({}) is defaulting to airline and continent ({}) specific data".format(ID, AC_type, continent))
                        return self.TADCf(AC_type, kwargs["airline"], continent)
            if (AC_type, kwargs["airline"]) in self.ac_airline:
                if len(self.TAG.get_group((AC_type, kwargs["airline"]))) > min_datapoints:
                    print("Defaulting to average airline performance for {} ({}). Aircraft type specific destination/country/continent data not found.".format(ID, AC_type))
                    return self.TAf(AC_type, kwargs["airline"])
            print("Insufficient data is available for ({}, {}) or {} does not operate the {}.".format(ID, AC_type, kwargs["airline"], AC_type))
            swA = True
        if "airline" not in kwargs or swA:
            if "dest" in kwargs:
                if (AC_type, kwargs["dest"]) in self.ac_dest:
                    print("{} ({}) uses airport specific data (not airline performance data) to {}.".format(ID, AC_type, kwargs["dest"]))
                    return self.TDf(AC_type, kwargs["dest"])
                elif (AC_type, country) in self.ac_country:
                    print("{} ({}) is defaulting to country ({}) specific data (not airline performance data).".format(ID, AC_type, country))
                    return self.TCOUf(AC_type, country)
                elif (AC_type, continent) in self.ac_continent:
                    print("{} ({}) is defaulting to continent ({}) specific data (not airline performance data).".format(ID, AC_type, continent))
                    return self.TCONf(AC_type, continent)
            if AC_type in self.AC_types:
                print("Defaulting to average aircraft performance for {} ({}) (not airline performance data).".format(ID, AC_type))
                return self.TTf(AC_type)
        if AC_type not in self.AC_types:
            print("No data available for {} ({}). Using B744 average performance.".format(ID, AC_type))
            return self.TTf("B744")

    def select_type(self, AC_type, **kwargs):
        if "dest" in kwargs:
            country = self.airports.loc[self.airports["ident"] == kwargs["dest"]].reset_index()

            if len(country) > 0:
                country = country.at[0, "iso_country"]
                continent = self.continents.loc[self.continents["two_code"] == country].reset_index().at[0, "continent"]
            else:
                country = None
                continent = None

        swA = False
        swT = False
        min_datapoints = 20

        if "airline" in kwargs:
            if "dest" in kwargs:
                if (AC_type, kwargs["airline"], kwargs["dest"]) in self.ac_airline_dest:
                    if len(self.TADG.get_group((AC_type, kwargs["airline"], kwargs["dest"]))) > min_datapoints:
                        return "TAD"
                if (AC_type, kwargs["airline"], country) in self.ac_airline_country:
                    if len(self.TADLG.get_group((AC_type, kwargs["airline"], country))) > min_datapoints:
                        return "TADL"
                if (AC_type, kwargs["airline"], continent) in self.ac_airline_continent:
                    if len(self.TADCG.get_group((AC_type, kwargs["airline"], continent))) > min_datapoints:
                        return "TADC"
            if (AC_type, kwargs["airline"]) in self.ac_airline:
                if len(self.TAG.get_group((AC_type, kwargs["airline"]))) > min_datapoints:
                    return "TA"
            swA = True
        if "airline" not in kwargs or swA:
            if "dest" in kwargs:
                if (AC_type, kwargs["dest"]) in self.ac_dest:
                    return "TD"
                elif (AC_type, country) in self.ac_country:
                    return "TCOU"
                elif (AC_type, continent) in self.ac_continent:
                    return "TCON"
            if AC_type in self.AC_types:
                return "TT"
        if AC_type not in self.AC_types:
            return "BASIC"

    def TADf(self, ac_type, airline, dest):
        '''
        Function: Returns interpolate functions based upon airline and destination airport specific performance data.

        Args:
            ac_type:    Aircraft type. Use ICAO code (e.g. "B744")
            airline:    Airline code. Use ICAO code (e.g. "KLM")
            dest:       Airport code. Use four letter code (e.g. "EHAM")
        Returns:
            TADf_IAS: Interpolate function that returns IAS when input is given in FL.
            TADf_ROC: Interpolate function that returns ROC when input is given in FL.
            IAS_slope_max: maximum slope of IAS per flight level

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TAD_temp = self.TAD.groupby(["ac_type", "airline", "dest"]).get_group((ac_type, airline, dest)).reset_index(drop=True)
        FL_temp = np.arange(0, TAD_temp["alt"].max() + 1, 1)
        TADf_IAS = sc.interp1d(TAD_temp.loc[:, "alt"].values, TAD_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TADf_ROC = sc.interp1d(TAD_temp.loc[:, "alt"].values, TAD_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TAD_temp["ias"].diff().max()/(TAD_temp.at[1, "alt"] - TAD_temp.at[0, "alt"])

        data = {"alt": FL_temp, "IAS": TADf_IAS, "cROCD": TADf_ROC}

        TAD_df = pd.DataFrame(data=data)

        return TAD_df, IAS_slope_max

    def TADLf(self, ac_type, airline, country):
        '''
        Function: Returns interpolate functions based upon airline and destination country specific performance data.

        Args:
            ac_type:    Aircraft type. Use ICAO code (e.g. "B744")
            airline:    Airline code. Use ICAO code (e.g. "KLM")
            country:    Country code. Use two letter (alpha-2) code (e.g. "NL")
        Returns:
            return_1: (Description of returned item 1)
            return_2: (Description of returned item 2)

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TADL_temp = self.TADLG.get_group((ac_type, airline, country)).reset_index(drop=True)
        FL_temp = np.arange(0, TADL_temp["alt"].max() + 1, 1)
        TADLf_IAS = sc.interp1d(TADL_temp.loc[:, "alt"].values, TADL_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TADLf_ROC = sc.interp1d(TADL_temp.loc[:, "alt"].values, TADL_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TADL_temp["ias"].diff().max() / (TADL_temp.at[1, "alt"] - TADL_temp.at[0, "alt"])

        data = {"alt": FL_temp, "IAS": TADLf_IAS, "cROCD": TADLf_ROC}

        TADL_df = pd.DataFrame(data=data)

        return TADL_df, IAS_slope_max

    def TADCf(self, ac_type, airline, continent):
        '''
        Function: Returns interpolate functions based upon airline and destination continent specific performance data.

        Args:
            ac_type:    Aircraft type. Use ICAO code (e.g. "B744")
            airline:    Airline code. Use ICAO code (e.g. "KLM")
            continent:  Continent. Use full name of continent (e.g. "South America")
        Returns:
            return_1: (Description of returned item 1)
            return_2: (Description of returned item 2)
            ....

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TADC_temp = self.TADCG.get_group((ac_type, airline, continent)).reset_index(drop=True)
        FL_temp = np.arange(0, TADC_temp["alt"].max() + 1, 1)
        TADCf_IAS = sc.interp1d(TADC_temp.loc[:, "alt"].values, TADC_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TADCf_ROC = sc.interp1d(TADC_temp.loc[:, "alt"].values, TADC_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TADC_temp["ias"].diff().max() / (TADC_temp.at[1, "alt"] - TADC_temp.at[0, "alt"])

        data = {"alt": FL_temp, "IAS": TADCf_IAS, "cROCD": TADCf_ROC}

        TADC_df = pd.DataFrame(data=data)

        return TADC_df, IAS_slope_max

    def TAf(self, ac_type, airline):
        '''
        Function: Returns interpolate functions based upon airline specific performance data.
        Args:
            ac_type:    Aircraft type. Use ICAO code (e.g. "B744")
            airline:    Airline code. Use ICAO code (e.g. "KLM")
        Returns:
            return_1: (Description of returned item 1)
            return_2: (Description of returned item 2)
            ....

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TA_temp = self.TAG.get_group((ac_type, airline)).reset_index(drop=True)
        FL_temp = np.arange(0, TA_temp["alt"].max() + 1, 1)
        TAf_IAS = sc.interp1d(TA_temp.loc[:, "alt"].values, TA_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TAf_ROC = sc.interp1d(TA_temp.loc[:, "alt"].values, TA_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TA_temp["ias"].diff().max() / (TA_temp.at[1, "alt"] - TA_temp.at[0, "alt"])

        data = {"alt": FL_temp, "IAS": TAf_IAS, "cROCD": TAf_ROC}

        TA_df = pd.DataFrame(data=data)

        return TA_df, IAS_slope_max

    def TDf(self, ac_type, dest):
        '''
        Function: Returns interpolate functions based upon destination airport specific performance data.
        Args:
            ac_type:    Aircraft type. Use ICAO code (e.g. "B744")
            dest:       Airport code. Use four letter code (e.g. "EHAM")
        Returns:
            return_1: (Description of returned item 1)
            return_2: (Description of returned item 2)
            ....

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TD_temp = self.TDG.get_group((ac_type, dest)).reset_index(drop=True)
        FL_temp = np.arange(0, TD_temp["alt"].max() + 1, 1)
        TDf_IAS = sc.interp1d(TD_temp.loc[:, "alt"].values, TD_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TDf_ROC = sc.interp1d(TD_temp.loc[:, "alt"].values, TD_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TD_temp["ias"].diff().max() / (TD_temp.at[1, "alt"] - TD_temp.at[0, "alt"])

        data = {"alt": FL_temp, "IAS": TDf_IAS, "cROCD": TDf_ROC}

        TD_df = pd.DataFrame(data=data)

        return TD_df, IAS_slope_max

    def TCOUf(self, ac_type, country):
        '''
        Function: Returns interpolate functions based upon destination country specific performance data.
        Args:
            ac_type:    Aircraft type. Use ICAO code (e.g. "B744")
            country:    Country code. Use two letter (alpha-2) code (e.g. "NL")
        Returns:
            return_1: (Description of returned item 1)
            return_2: (Description of returned item 2)
            ....

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TCOU_temp = self.TCOUG.get_group((ac_type, country)).reset_index(drop=True)
        FL_temp = np.arange(0, TCOU_temp["alt"].max() + 1, 1)
        TCOUf_IAS = sc.interp1d(TCOU_temp.loc[:, "alt"].values, TCOU_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TCOUf_ROC = sc.interp1d(TCOU_temp.loc[:, "alt"].values, TCOU_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TCOU_temp["ias"].diff().max() / (TCOU_temp.at[1, "alt"] - TCOU_temp.at[0, "alt"])

        data = {"alt": FL_temp, "IAS": TCOUf_IAS, "cROCD": TCOUf_ROC}

        TCOU_df = pd.DataFrame(data=data)

        return TCOU_df, IAS_slope_max

    def TCONf(self, ac_type, continent):
        '''
        Function: Returns interpolate functions based upon destination country specific performance data.
        Args:
            ac_type:    Aircraft type. Use ICAO code (e.g. "B744")
            continent:  Continent. Use full name of continent (e.g. "South America")
        Returns:
            return_1: (Description of returned item 1)
            return_2: (Description of returned item 2)
            ....

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TCON_temp = self.TCONG.get_group((ac_type, continent)).reset_index(drop=True)
        FL_temp = np.arange(0, TCON_temp["alt"].max() + 1, 1)
        TCONf_IAS = sc.interp1d(TCON_temp.loc[:, "alt"].values, TCON_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TCONf_ROC = sc.interp1d(TCON_temp.loc[:, "alt"].values, TCON_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TCON_temp["ias"].diff().max() / (TCON_temp.at[1, "alt"] - TCON_temp.at[0, "alt"])

        data = {"alt": FL_temp, "IAS": TCONf_IAS, "cROCD": TCONf_ROC}

        TCON_df = pd.DataFrame(data=data)

        return TCON_df, IAS_slope_max

    def TTf(self, ac_type):
        '''
        Function: (Purpose of the function/method)
        Args:
            arg_1:    (Description of input 1)
            arg_2:    (Description of input 1)
            ...
        Returns:
            return_1: (Description of returned item 1)
            return_2: (Description of returned item 2)
            ....

        Created by: Lars Dijkstra
        Date: 14-10-2022
        '''

        TT_temp = self.TTG.get_group(ac_type).reset_index(drop=True)
        FL_temp = np.arange(0, TT_temp["alt"].max() + 1, 1)
        TTf_IAS = sc.interp1d(TT_temp.loc[:, "alt"].values, TT_temp.loc[:, "ias"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        TTf_ROC = sc.interp1d(TT_temp.loc[:, "alt"].values, TT_temp.loc[:, "cROCD"].values, kind=self.kind, fill_value="extrapolate")(FL_temp)
        IAS_slope_max = TT_temp["ias"].diff().max() / (TT_temp.at[1, "alt"] - TT_temp.at[0, "alt"])
        data = {"alt": FL_temp, "IAS": TTf_IAS, "cROCD": TTf_ROC}

        TT_df = pd.DataFrame(data=data)

        return TT_df, IAS_slope_max

    def IAS_ROC(self, dfs, alts):

        alts = alts/0.3048/100
        array = np.array([self.values(dfs[i], alts[i]) for i in range(len(alts))])

        return np.array([element[0]*self.kts for element in array]), np.array([element[1]*self.fpm for element in array])

    def values(self, df, alt):
        if isinstance(df, bool):
            return False, False

        flag = False

        if alt > df['alt'].max():
            alt = df['alt'].max()
            flag = True

        if alt < 0:
            alt = 0

        temp = df.loc[df['alt'] == int(alt)].iloc[:1]

        if temp.empty:
            return False, False

        if flag == True:
            return temp.iloc[0]["IAS"], 0
        else:
            return temp.iloc[0]["IAS"], abs(temp.iloc[0]["cROCD"])
