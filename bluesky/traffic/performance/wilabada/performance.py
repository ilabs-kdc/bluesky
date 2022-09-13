import numpy as np
from bluesky.tools.aero import kts, ft, gamma, gamma1, gamma2, R, beta, g0, \
    vmach2cas

PHASE = {"None":0,
         "TO"  :1, # Take-off
         "IC"  :2, # Initial climb
         "CR"  :3, # Cruise
         "AP"  :4, # Approach
         "LD"  :5, # Landing
         "GD"  :6, # Ground
         "to"  :1,
         "ic"  :2,
         "cr"  :3,  # and lower case to be sure
         "ap"  :4,
         "ld"  :5,
         "gd"  :6}


def phases():
    pass

def esf():
    pass

def calclimits():
    pass