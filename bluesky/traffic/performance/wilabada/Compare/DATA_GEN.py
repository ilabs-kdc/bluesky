from OUTBOUND_FUNCS import *
from copy import deepcopy
import os
import re

def FP_SPLIT_SID_M(FP_folderlocation, FP_header):
    """"
    Returns all acid and their respective data that have a SID on day X. Keys are the dates of the files in the FP_fold-
    er location.
    """

    FP_filenames = os.listdir(FP_folderlocation)

    FP_data = {}
    for FP_file in FP_filenames:
        FP_SIDs = split_SID(FP_file, FP_header)
        FP_data["".join(re.findall(r'\d+', FP_file))] = FP_SIDs

    return FP_data

def SURR_Import(FP_folderlocation, FP_header, SURR_folderlocation, SURR_header):
    """"
    Only imports the SURR files of which the coefficients of the aircraft type are known. Keys are str(date_callsign).
    """
    FP_data = FP_SPLIT_SID_M(FP_folderlocation, FP_header)

    SURR_files = os.listdir(SURR_folderlocation)

    SURR_keys = [file.split("_")[0] + "_" + file.split("_")[1] for file in SURR_files]

    SURR_data = {}

    for date in FP_data:
        for callsign in FP_data[date]:
            if date + "_" + callsign in SURR_keys:
                SURR_data[date + "_" + callsign] = data_import(SURR_folderlocation + r"\\" + SURR_files[SURR_keys.index(
                    date + "_" + callsign)], SURR_header)

    return SURR_data

def SID_i(FP_folderlocation, FP_header, SURR_folderlocation, SURR_header):


SID_i(r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Compare\FP",
               r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Compare\hdr.fpdata",
            r"C:\Users\LVNL_ILAB3\PycharmProjects\bluesky\bluesky\traffic\performance\wilabada\Compare\Surr",
            "artas.fields")