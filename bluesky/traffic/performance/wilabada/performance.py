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


#------------------------------------------------------------------------------
#
# FLIGHT PHASES
# based on the BADA 3.12 User Manual, chapter 3.5, p. 19, adapted
#------------------------------------------------------------------------------


def phases(alt, gs, delalt, cas, vmto, vmic, vmap,
           vmcr, vmld, bank, bphase, swhdgsel, bada):

    # flight phases: TO (1), IC (2), CR (3), AP(4), LD(5), GD (6)
    #--> no holding phase yet
    #-------------------------------------------------

    # phase TO[1]: alt<400 and vs>0
    Talt = np.array(alt < (400. * ft))
    Tspd = np.array(gs > (30. * kts))
    Tvs  = np.array(delalt >= 0.) * 1.0

    to   = Talt * Tspd * Tvs * 1

    #-------------------------------------------------
    # phase IC[2]: 400<alt<2000, vs>0
    Ialt = np.array((alt >= (400. * ft)) & (alt < (2000. * ft)))
    Ivs  = np.array(delalt > 0.)

    ic   = Ialt*Ivs*2


    #-------------------------------------------------
    #phase CR[3]: in climb above 2000ft, in descent
    # above 8000ft and below 8000ft if V>=Vmincr + 10kts

    # a. climb
    Caalt = np.array(alt >= (2000. * ft))
    Cavs  = np.array(delalt >= 0.)
    cra   = np.logical_and.reduce([Caalt, Cavs]) * 1

    #b. above 8000ft
    crb   = np.array(alt > (8000. * ft)) * 1

    #c. descent
    Ccalt = np.array(alt <= (8000. * ft))
    Ccvs  = np.array(delalt <= 0.)
    Ccspd = np.array(cas >= (vmcr + 10. * kts))
    crc   = np.logical_and.reduce([Ccalt, Ccvs, Ccspd]) * 1

    # merge climb and descent phase
    cr = np.maximum(cra, np.maximum(crb, crc)) * 3

    #-------------------------------------------------
    # phase AP[4]

    #a. alt<8000, Speed between Vmcr+10 and Vmapp+10, v<>0
    #altitude check
    Aaalt = np.array((alt > ft) & (alt <= (8000. * ft)))
    Aaspd = np.array(cas < (vmcr + 10. * kts))
    Aavs  = np.array(delalt <= 0.)
    apa   = np.logical_and.reduce([Aaalt, Aaspd , Aavs]) * 1
    #b. alt<3000ft, Vmcr+10>V>Vmap+10
    Abalt = np.array((alt > ft) & (alt <= (3000. * ft)))
    if bada:
        Abspd = np.array((cas >= (vmap + 10. * kts)) & (cas < (vmcr + 10. * kts)))
    else:
        Abspd = np.array(cas >= (vmap + 10. * kts))
    Abvs = np.array(delalt <= 0.)
    apb  = np.logical_and.reduce([Abalt, Abspd , Abvs]) * 1

    # merge a. and b.
    ap   = np.maximum.reduce([apa, apb]) * 4

    #-------------------------------------------------
    # phase LD[5]: alt<3000, Speed below vmap (i.e. minimum approach speed) + 10kt
    Lalt = np.array(alt <= (3000.0 * ft))
    if bada:
        Lspd = np.array(cas < (vmap + 10.0 * kts))
    else:
        Lspd = np.array(gs >= (30.0 * kts))
    Lvs = np.array(delalt <= 0.0)
    ld  = np.logical_and.reduce([Lalt, Lspd, Lvs]) * 5

    #-------------------------------------------------
    # phase GND: alt < 1 ft, i.e. as soon as on ground
    gd = np.array(alt <= ft)* 6

    #-------------------------------------------------
    # combine all phases
    phase = np.maximum.reduce([to, ic, ap, ld, cr, gd])

    to2 = np.where(phase == 1)
    ic2 = np.where(phase == 2)
    cr2 = np.where(phase == 3)
    ap2 = np.where(phase == 4)
    ld2 = np.where(phase == 5)
    gd2 = np.where(phase == 6)

    # assign aircraft to their nominal bank angle per phase
    bank[to2] = bphase[0]
    bank[ic2] = bphase[1]
    bank[cr2] = bphase[2]
    bank[ap2] = bphase[3]
    bank[ld2] = bphase[4]
    # to be refined! find value that comes closest to 1 if tan or cos
    bank[gd2] = bphase[5]

    # not turning aircraft do not have a bank angle.
    #swhdgsel == True: Aircraft is turning
    noturn = np.array(swhdgsel) * 100.0
    bank   = np.minimum(noturn, bank)

    return (phase, bank)
#------------------------------------------------------------------------------
#
# ENERGY SHARE FACTOR
# (BADA User Manual 3.12, p.15)
#
#-----------------------------------------------------------------------------
def esf(alt, M, climb, descent, delspd, selmach, type='B744', tISA = 0):


    # test for acceleration / deceleration
    cspd  = np.array((delspd <= 0.001) & (delspd >= -0.001))

    # accelerating or decelerating
    acc   = np.array(delspd > 0.001)
    dec   = np.array(delspd < -0.001)

    # tropopause
    abtp  = np.array(alt > 11000.0)
    beltp = np.logical_not(abtp)

    selcas = np.logical_not(selmach)

    # tISA = (self.temp-self.dtemp)/self.temp

    # constant Mach/CAS
    # case a: constant MA above TP
    efa   = np.logical_and.reduce([cspd, selmach, abtp]) * 1

    # case b: constant MA below TP (at the moment just ISA: tISA = 1)
    efb   = 1.0 / ((1.0 + ((gamma * R * beta) / (2.0 * g0)) * M**2 * tISA)) \
        * np.logical_and.reduce([cspd, selmach, beltp]) * 1

    # case c: constant CAS below TP (at the moment just ISA: tISA = 1)
    efc = 1.0 / (1.0 + (((gamma * R * beta) / (2.0 * g0)) * (M**2) * tISA) +
        ((1.0 + gamma1 * (M**2))**(-1.0 / (gamma - 1.0))) *
        (((1.0 + gamma1 * (M**2))**gamma2) - 1)) * \
        np.logical_and.reduce([cspd, selcas, beltp]) * 1

    #case d: constant CAS above TP
    efd = 1.0 / (1.0 + ((1.0 + gamma1 * (M**2) * tISA)**(-1.0 / (gamma - 1.0))) *
        (((1.0 + gamma1 * (M**2))**gamma2) - 1.0)) * \
        np.logical_and.reduce([cspd, selcas, abtp]) * 1

    #case e: acceleration in climb
    efe    = 0.3 * np.logical_and.reduce([acc, climb])

    #case f: deceleration in descent
    eff    = 0.3 * np.logical_and.reduce([dec, descent])

    #case g: deceleration in climb
    efg    = 1.7 * np.logical_and.reduce([dec, climb])

    #case h: acceleration in descent
    efh    = 1.7 * np.logical_and.reduce([acc, descent])

    # combine cases
    ef = np.maximum.reduce([efa, efb, efc, efd, efe, eff, efg, efh])

    # ESF of non-climbing/descending aircraft is zero which
    # leads to an error. Therefore, ESF for non-climbing aircraft is 1
    return np.maximum(ef, np.array(ef == 0) * 1)

def calclimits():
    pass