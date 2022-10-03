import pandas as pd
import os
import numpy as np
from LOG_READER import LOG_READER
from EEI import EEI
import matplotlib.pyplot as plt
from copy import deepcopy
from matplotlib.backends.backend_pdf import PdfPages

SMALL_SIZE = 14
MEDIUM_SIZE = 15
BIGGER_SIZE = 18

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=8)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

EEI = EEI()

fpm = 0.00508

limited = ["KDD3S", "LOP3S", "REN2S", "ARN3S", "AND2S", "SPY4K", "WDY3W", "OGI4W", "KDD2V", "LOP4V"]

def data_import(filename, header):
    names = list(pd.read_csv(header, sep=";").columns)
    data = pd.read_csv(filename, sep=";", header = None, names = names)

    data_dict = {}
    for column_i in range(len(list(data.columns))):
        data_dict[list(data.columns)[column_i]] = data.iloc[:,column_i].values

    return data_dict

def split_SID(filename, header):
    data = data_import(filename, header)

    split_dict = {}

    for i in range(len(data["SID_id"])):
        if type(data["SID_id"][i]) == str:
            split_dict[data["acid"][i]] = {}
            for column in data:
                split_dict[data["acid"][i]][column] = data[column][i]

    SIDs = os.listdir(r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\scenario\WILABADA\SID")
    for SID_i in range(len(SIDs)):
        SIDs[SID_i] = SIDs[SID_i].replace(".scn", "")

    remove = []
    for i in split_dict:
        counter = 0
        while split_dict[i]["SID_id"] not in SIDs:
            counter = counter + 1
            split_dict[i]["SID_id"] = split_dict[i]["SID_id"][:3] + str(int(split_dict[i]["SID_id"][3]) + 1) + split_dict[i]["SID_id"][4:]

            if counter > 5:
                remove.append(i)
                break

    for i in remove:
        split_dict.pop(i)

    return split_dict

def SURR_dicts(folderlocation, header):
    filenames = os.listdir(folderlocation)

    data_dict = {}

    for file in filenames:
        if file == "artas.fields":
            continue
        data_dict[file.split("_")[1]] = data_import(folderlocation + r"\\" + file, header)

    return data_dict

def BADA_aircraft():
    BADA_ac = os.listdir(r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\data\performance\BADA")
    inBADA = []
    for aircraft in range(len(BADA_ac)):
        if BADA_ac[aircraft][-3:] != "APF":
            continue
        inBADA.append(BADA_ac[aircraft].replace("__.APF", ""))
    return inBADA

def scenario(filename, header):
    data = split_SID(filename, header)

    BADA_ac = BADA_aircraft()

    scenariolines = []

    NUMAC = 1600

    for aircraft in data:
        if data[aircraft]["a_c_type"] not in BADA_ac or data[aircraft]["a_c_type"] not in EEI.dict:
            continue
        if len(scenariolines)/2 > NUMAC:
            break
        heading = "".join((x for x in data[aircraft]["trwy"] if x.isdigit()))
        if data[aircraft]["trwy"][-1] != "L" and data[aircraft]["trwy"][-1] != "C" and data[aircraft]["trwy"][-1] != "R":
            line = "00:00:00.00>cre " + aircraft + " " + data[aircraft]["a_c_type"] + " " + "THR" + str(data[aircraft]["trwy"]) + " " + str(int(heading)*10) + " " + "0" + " " + "0" + "\n"
            scenariolines.append(line)
        else:
            line = "00:00:00.00>cre " + aircraft + " " + data[aircraft]["a_c_type"] + " " + "TH" + str(data[aircraft]["trwy"]) + " " + str(int(heading)*10) + " " + "0" + " " + "0" + "\n"
            scenariolines.append(line)
        line = "00:00:00.00>TO " + " " + aircraft + " " + data[aircraft]["SID_id"] + "\n"
        # line = "00:00:00.00>PCALL " + "WILABADA/SID/"+data[aircraft]["SID_id"] + " " + aircraft + "\n"
        scenariolines.append(line)
    scenariolines.append("00:00:00.00>crelog log1 5 \n 00:00:00.00>log1 add traf.id, traf.lat, traf.lon, traf.alt, traf.hdg, traf.tas, traf.cas, traf.vs, \n \
                          00:00:00.00>log1 on")
    with open("../../../../../scenario/OUTBOUND_Scenario.scn", "w", encoding="utf-8") as f:
        f.writelines(scenariolines)

def split_SID_AC(filename, header):
    data = split_SID(filename, header)

    S_dict = {}

    BADA_ac = BADA_aircraft()

    for aircraft in data:
        if data[aircraft]["a_c_type"] not in BADA_ac or data[aircraft]["a_c_type"] not in EEI.dict:
            continue
        if data[aircraft]["SID_id"] not in S_dict:
            S_dict[data[aircraft]["SID_id"]] = {}
        if data[aircraft]["a_c_type"] not in S_dict[data[aircraft]["SID_id"]]:
            S_dict[data[aircraft]["SID_id"]][data[aircraft]["a_c_type"]] = []
        S_dict[data[aircraft]["SID_id"]][data[aircraft]["a_c_type"]].append(aircraft)

    return S_dict

def mother_of_all_plots(FP_file, FP_header, SURR_folderlocation, SURR_header, logfile):
    FP_data = split_SID(FP_file, FP_header)
    SID_AC = split_SID_AC(FP_file, FP_header)
    SURR_data = SURR_dicts(SURR_folderlocation, SURR_header)
    LOG_data = LOG_READER(logfile)
    linewidth = 2
    linestyle = (0, (5, 5))
    BS_linewidth = 3

    pp = PdfPages('Take-off_8_CAS_ALL_ALT.pdf')

    for i in LOG_data:
        for element in LOG_data[i]:
            LOG_data[i][element] = np.array(LOG_data[i][element])

    for SID in SID_AC:
        for actype in SID_AC[SID]:
            # if actype != "B738":
            #     continue
            if len(SID_AC[SID][actype]) >= 2:


                BS_callsign = SID_AC[SID][actype][0]

                # if FP_data[BS_callsign]["trwy"] != "36L":
                #     continue

                alt_bs = LOG_data[BS_callsign]["FL"][(LOG_data[BS_callsign]["FL"] < 90)]

                time_bs = LOG_data[BS_callsign]["simt"][(LOG_data[BS_callsign]["FL"] < 90)]
                alt_temp = deepcopy(alt_bs)
                alt_bs = alt_bs[(alt_bs > 0)]
                try:
                    time_bs = time_bs[(alt_temp > 0)] - time_bs[(alt_temp > 0)][0]
                except:
                    continue
                fig, axs = plt.subplots(3, figsize=(12, 12))
                if SID in limited:
                    fig.suptitle("ACType: " + actype + ", SID_ID: " + SID + ", RWY: " + FP_data[BS_callsign]["trwy"], color="red")
                else:
                    fig.suptitle("ACType: " + actype + ", SID_ID: " + SID + ", RWY: " + FP_data[BS_callsign]["trwy"])

                ROC_bs = LOG_data[BS_callsign]["vs"][(LOG_data[BS_callsign]["FL"] < 90)]
                ROC_bs = ROC_bs[(alt_temp > 0)] / fpm

                SPD_bs = LOG_data[BS_callsign]["cas"][(LOG_data[BS_callsign]["FL"] < 90)]
                SPD_bs = SPD_bs[(alt_temp > 0)] / 0.514444

                axs[0].plot(time_bs, alt_bs, label="BlueSky", linewidth=BS_linewidth)
                # axs[0].plot(alt_bs, SPD_bs, label="BlueSky", linewidth=BS_linewidth)
                axs[1].plot(time_bs, SPD_bs, label="BlueSky", linewidth=BS_linewidth)
                axs[2].plot(time_bs, ROC_bs, label="BlueSky", linewidth=BS_linewidth)

                for callsign in SID_AC[SID][actype]:
                    try:
                        FL_DATA = SURR_data[callsign]["fl"][(SURR_data[callsign]["fl"] < 90)]
                    except:
                        continue

                    time_DATA = SURR_data[callsign]["uxsec"][(SURR_data[callsign]["fl"] < 90)] - \
                                SURR_data[callsign]["uxsec"][0]

                    ROC_DATA = SURR_data[callsign]["cROCD"][(SURR_data[callsign]["fl"] < 90)]
                    SPD_DATA = SURR_data[callsign]["ias"][(SURR_data[callsign]["fl"] < 90)]

                    FL_DATA = FL_DATA[time_DATA < 300]
                    ROC_DATA = ROC_DATA[time_DATA < 300]
                    SPD_DATA = SPD_DATA[time_DATA < 300]
                    time_DATA = time_DATA[time_DATA < 300]

                    axs[0].plot(time_DATA, FL_DATA, label=callsign, linestyle=linestyle, linewidth=linewidth)
                    # axs[0].plot(FL_DATA, SPD_DATA, label=callsign, linestyle=linestyle, linewidth=linewidth)

                    axs[1].plot(time_DATA, SPD_DATA, label=callsign, linestyle=linestyle, linewidth=linewidth)
                    axs[2].plot(time_DATA, ROC_DATA, label=callsign, linestyle=linestyle,  linewidth=linewidth)

                axs[0].set(xlabel="Time [s]", ylabel="Altitude [FL]")
                axs[1].set(xlabel="Time [s]", ylabel="Speed [CAS]")
                axs[2].set(xlabel="Time [s]", ylabel="ROC [fpm]")
                axs[0].grid()
                axs[1].grid()
                axs[2].grid()
                axs[0].legend()
                axs[1].legend()
                axs[2].legend()
                # plt.show()
                pp.savefig(fig)
            else:
                continue
    pp.close()

def mother_of_all_plots_2(FP_file, FP_header, SURR_folderlocation, SURR_header, logfile):
    FP_data = split_SID(FP_file, FP_header)
    SID_AC = split_SID_AC(FP_file, FP_header)
    SURR_data = SURR_dicts(SURR_folderlocation, SURR_header)
    LOG_data = LOG_READER(logfile)
    linewidth = 2
    linestyle = (0, (5, 5))
    BS_linewidth = 3

    # pp = PdfPages('Take-off_7_CAS_ALL_ALT.pdf')

    for i in LOG_data:
        for element in LOG_data[i]:
            LOG_data[i][element] = np.array(LOG_data[i][element])

    aircraft_types = []
    for SID in SID_AC:
        for aircraft in SID_AC[SID]:
            if aircraft not in aircraft_types:
                aircraft_types.append(aircraft)

    for actype in aircraft_types:
        rwylst = []
        limsids = []
        succes = False
        fig, axs = plt.subplots(3, figsize=(12, 16))

        for SID in SID_AC:
            if SID in limited:
                continue
            if actype not in SID_AC[SID]:
                continue
            if len(SID_AC[SID][actype]) >= 2:
                limsids.append(SID)
                BS_callsign = SID_AC[SID][actype][0]
                if FP_data[BS_callsign]["trwy"] not in rwylst:
                    rwylst.append(FP_data[BS_callsign]["trwy"])
                for callsign in SID_AC[SID][actype]:
                    try:
                        FL_DATA = SURR_data[callsign]["fl"][(SURR_data[callsign]["fl"] < 90)]
                    except:
                        continue

                    time_DATA = SURR_data[callsign]["uxsec"][(SURR_data[callsign]["fl"] < 90)] - \
                                SURR_data[callsign]["uxsec"][0]

                    ROC_DATA = SURR_data[callsign]["cROCD"][(SURR_data[callsign]["fl"] < 90)]
                    SPD_DATA = SURR_data[callsign]["ias"][(SURR_data[callsign]["fl"] < 90)]

                    FL_DATA = FL_DATA[time_DATA < 300]
                    ROC_DATA = ROC_DATA[time_DATA < 300]
                    SPD_DATA = SPD_DATA[time_DATA < 300]
                    time_DATA = time_DATA[time_DATA < 300]

                    axs[0].plot(time_DATA, FL_DATA, label=callsign, linestyle=linestyle, linewidth=linewidth)
                    axs[1].plot(time_DATA, SPD_DATA, label=callsign, linestyle=linestyle, linewidth=linewidth)
                    axs[2].plot(time_DATA, ROC_DATA, label=callsign, linestyle=linestyle, linewidth=linewidth)
                    succes = True
            else:
                continue
        if succes:
            fig.suptitle("ACType: " + actype + ", SID_IDs: " + " ".join(limsids) + "\n RWYs: " + " ".join(rwylst) , color="red")
            axs[0].set(xlabel="Time [s]", ylabel="Altitude [FL]")
            axs[1].set(xlabel="Time [s]", ylabel="Speed [CAS]")
            axs[2].set(xlabel="Time [s]", ylabel="ROC [fpm]")
            axs[0].grid()
            axs[1].grid()
            axs[2].grid()
            axs[0].legend()
            axs[1].legend()
            axs[2].legend()
            plt.show()
        else:
            continue

# scenario("fp20190101", "hdr.fpdata")
# mother_of_all_plots_2("fp20190101", "hdr.fpdata", r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Compare\Surr", "artas.fields", r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\output\LOG1__20220930_10-36-51.log")
mother_of_all_plots("fp20190101", "hdr.fpdata", r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Compare\Surr", "artas.fields", r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\output\LOG1__20221003_11-38-31.log")


