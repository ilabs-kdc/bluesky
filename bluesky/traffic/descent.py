import numpy as np
import bluesky as bs
from bluesky.tools.aero import ft, kts, gamma, gamma1, gamma2, R, beta, nm, fpm, vcasormach2tas, vcas2tas, vtas2cas, cas2tas, vcas2mach, g0, vmach2cas, density


def find_gamma(idx, altitude, tas):
    #Uitleg
    """
    simplifications:
    - Weight is kept constant
    - Gamma is per flight level of
    - decel. segments are calculated with 50x bigger timesteps

    """

    start_altitude = altitude + 100*ft
    final_altitude = 0

    segments = np.arange(final_altitude, start_altitude, 100*ft)
    speed = [speedschedule(idx, i) for i in segments]

    phase = [phases(idx, i, speed[index], final_altitude - i) for index, i in enumerate(segments)]
    esft = [esf(idx, i, speed[index]) for index, i in enumerate(segments)]
    td = [TandD(idx, i, speed[index], phase[index]) for index,i in enumerate(segments)]
    T,D = zip(*td)
    rod = ((np.array(T) - np.array(D)) * vcas2tas(np.array(speed), np.array(segments))) / (bs.traf.perf.mass[idx] * g0) * np.array(esft)
    gammatas = abs(rod/vcas2tas(np.array(speed), np.array(segments)))

    corr = np.sqrt(bs.traf.perf.mass[idx] / bs.traf.perf.mref[idx])
    spd = [corr * bs.traf.perf.vmld[idx] + 5 * kts,
           corr * bs.traf.perf.vmld[idx] + 10 * kts,
           corr * bs.traf.perf.vmld[idx] + 20 * kts,
           corr * bs.traf.perf.vmld[idx] + 50 * kts,
           min(bs.traf.perf.casdes[idx], 220 * kts),
           min(bs.traf.perf.casdes2[idx], 250 * kts),
           bs.traf.perf.casdes2[idx],
           vmach2cas(bs.traf.perf.mades[idx], altitude)]
    alts = [999 * ft, 1499 * ft, 1999 * ft, 2999 * ft, 5999 * ft, 9999 * ft, bs.traf.perf.hpdes[idx] / ft]
    cas = vtas2cas(tas, altitude)

    extra_dist = [ decelsegment(idx, i, spd[index], spd[index+1])  for index, i in reversed(list(enumerate(alts))) if spd[index] < cas]


    # for index, i in enumerate(segments):
    #     print('ALT:', segments[index]/ft/100, ' SPD:', speed[index]/0.5144, ' PHS:', phase[index], ' ESF:', esft[index],
    #           ' T:', T[index], ' D:', D[index], ' ROD:', rod[index]/fpm, ' Gm:', gammatas[index])

    return segments, gammatas, spd, extra_dist



def decelsegment(idx, alt, v0,v1):

    add_alt, add_dist = 0, 0
    v0n, v1n = v0*1., v1*1.

    if v1<3: v1 = vmach2cas(v1, alt)

    while np.round(v0,2) < np.round(v1,2):
        v0tas = vcasormach2tas(v0, alt + add_alt)
        v1tas = vcasormach2tas(v1, alt + add_alt)
        delspd = v0tas - v1tas
        need_ax = np.abs(delspd) > np.abs(bs.sim.simdt * 50 * bs.traf.perf.axmax[idx])
        ax = need_ax * np.sign(delspd) * bs.traf.perf.axmax[idx]
        tas = np.where(need_ax, v1tas + ax * bs.sim.simdt * 50, v0tas)
        cas = vtas2cas(tas, alt + add_alt)

        T,D = TandD(idx, alt + add_alt, cas, phases(idx, alt + add_alt, cas, 0))
        rod = ((T - D) * tas) / (bs.traf.perf.mass[idx] * g0) * 0.3

        add_alt += rod * bs.sim.simdt * 50
        add_dist += tas * bs.sim.simdt * 50

        v1 = cas

    add_alt_n, add_dist_n = 0, 0

    while abs(add_alt_n) < abs(add_alt):
        esf_n = esf(idx, alt + add_alt_n, v0n)
        T_n, D_n = TandD(idx, alt + add_alt_n, v0n, phases(idx, alt + add_alt_n, v0n, 0))
        v0tas = vcasormach2tas(v0n, alt + add_alt_n)
        rod_n = ((T_n - D_n) * v0tas) / (bs.traf.perf.mass[idx] * g0) * esf_n

        add_alt_n += rod_n * bs.sim.simdt * 50
        add_dist_n += v0tas * bs.sim.simdt * 50

    return add_dist - add_dist_n


# def speed_ax(idx, spds, alt, tas):
#
#     cas = []
#
#     for index, i in reversed(list(enumerate(spds))):
#         spds_tas = vcasormach2tas(i, alt[index])
#         delspd = spds_tas - tas
#         need_ax = np.abs(delspd) > np.abs(bs.sim.simdt * bs.traf.perf.axmax[idx])
#         ax = need_ax * np.sign(delspd) * bs.traf.perf.axmax
#         tas = np.where(need_ax, tas + ax * bs.sim.simdt, spds_tas)
#         cas.append(vtas2cas(tas, alt[index])[0])
#
#     return cas

def speedschedule(idx, alt):
    # Correction for minimum landing speed
    corr = np.sqrt(bs.traf.perf.mass[idx] / bs.traf.perf.mref[idx])

    if bs.traf.perf.piston[idx] != 1:
        if alt <= 999*ft:
            spd = corr * bs.traf.perf.vmld[idx] / kts + 5
            return spd * kts
        if alt > 999*ft and alt <= 1499*ft:
            spd = corr * bs.traf.perf.vmld[idx] / kts + 10
            return spd * kts
        if alt > 1499*ft and alt <= 1999*ft:
            spd = corr * bs.traf.perf.vmld[idx] / kts + 20
            return spd * kts
        if alt > 1999*ft and alt <= 2999*ft:
            spd = corr * bs.traf.perf.vmld[idx] / kts + 50
            return spd * kts
        if alt > 2999*ft and alt <= 5999*ft:
            spd = min(bs.traf.perf.casdes[idx] / kts, 220)
            return spd * kts
        if alt > 5999*ft and alt <= 9999*ft:
            spd = min(bs.traf.perf.casdes2[idx] / kts, 250)
            return spd * kts
        if alt > 9999*ft and alt <= bs.traf.perf.hpdes[idx] / 0.3048:
            spd = bs.traf.perf.casdes2[idx] / kts
            return spd * kts
        if alt > bs.traf.perf.hpdes[idx] / 0.3048:
            spd = bs.traf.perf.mades[idx]
            return spd

def phases(idx, alt, cas, delalt):

    vmap = bs.traf.perf.vmap[idx]
    vmcr = bs.traf.perf.vmcr[idx]

    #phase CR[3]: in climb above 2000ft, in descent
    # above 8000ft and below 8000ft if V>=Vmincr + 10kts
    # a. climb
    #b. above 8000ft
    #c. descent

    if (alt >= 2000 * ft and delalt >= 0) or \
            (alt > 8000 * ft) or \
            ( alt <= 8000 * ft and delalt <= 0 and  cas >= (vmcr + 10. * kts) ):
        return 3

    # phase AP[4]
    #a. alt<8000, Speed between Vmcr+10 and Vmapp+10, v<>0
    #b. alt<3000ft, Vmcr+10>V>Vmap+10

    # phase LD[5]: alt<3000, Speed below vmap (i.e. minimum approach speed) + 10kt
    if alt <= 3000 * ft and cas < (vmap + 10 * kts) and delalt <= 0:
        return 5

    if (alt > ft and alt <= 8000 * ft and cas < (vmcr + 10 * kts) and delalt <=0) or \
            (cas >= (vmap + 10. * kts) and cas < (vmcr + 10. * kts) and delalt <= 0):
        return 4

    # phase GND: alt < 1 ft, i.e. as soon as on ground
    if alt < ft:
        return 6



def esf(idx, alt, cas):

    M = vcas2mach(cas, alt)
    selmach = bs.traf.selspd[idx] < 2.0

    abtp  = alt > 11000.0
    beltp = np.logical_not(abtp)
    selcas = np.logical_not(selmach)

    if selmach and abtp:
        return 1

    if selmach and beltp:
        return 1.0 / ((1.0 + ((gamma * R * beta) / (2.0 * g0)) * M**2))

    if selcas and beltp:
        return 1.0 / (1.0 + (((gamma * R * beta) / (2.0 * g0)) * (M**2)) +
        ((1.0 + gamma1 * (M**2))**(-1.0 / (gamma - 1.0))) *
        (((1.0 + gamma1 * (M**2))**gamma2) - 1))

    if selcas and abtp:
        return 1.0 / (1.0 + ((1.0 + gamma1 * (M**2))**(-1.0 / (gamma - 1.0))) *
        (((1.0 + gamma1 * (M**2))**gamma2) - 1.0))

def TandD(idx, alt, cas, phase):
    tas = vcasormach2tas(cas, alt)
    mass = bs.traf.perf.mass[idx]

    rho = density(alt)

    qS = 0.5 * rho * np.maximum(1., tas) * np.maximum(1., tas) * bs.traf.perf.Sref[idx]
    cl = mass * g0 / qS

    delh = alt - bs.traf.perf.hpdes[idx]

    Tj = bs.traf.perf.ctcth1[idx] * (1 - (alt / ft) / bs.traf.perf.ctcth2[idx] + bs.traf.perf.ctcth3[idx] * (alt / ft) * (alt / ft))
    Tt = bs.traf.perf.ctcth1[idx] / np.maximum(1., tas / kts) * (1 - (alt / ft) / bs.traf.perf.ctcth2[idx]) + bs.traf.perf.ctcth3[idx]
    Tp = bs.traf.perf.ctcth1[idx] * (1 - (alt / ft) / bs.traf.perf.ctcth2[idx]) + bs.traf.perf.ctcth3[idx] / np.maximum(1., tas / kts)

    maxthr = Tj * bs.traf.perf.jet[idx] + Tt * bs.traf.perf.turbo[idx] + Tp * bs.traf.perf.piston[idx]

    # Phase 3 (cruise) calculations needed for 4 and 5
    cd = bs.traf.perf.cd0cr[idx] + bs.traf.perf.cd2cr[idx] * (cl * cl)
    if delh > 0:    T = maxthr * bs.traf.perf.ctdesh[idx]
    else:           T = maxthr * bs.traf.perf.ctdesl[idx]

    if phase == 4:
        cd = np.where(bs.traf.perf.cd0ap[idx] != 0, bs.traf.perf.cd0ap[idx] + bs.traf.perf.cd2ap[idx] * (cl * cl), cd)
        if delh <= 0:   T = maxthr * bs.traf.perf.ctdesa[idx]

    if phase == 5:
        cd = np.where(bs.traf.perf.cd0ld[idx] != 0, bs.traf.perf.cd0ld[idx] + bs.traf.perf.gear[idx] + bs.traf.perf.cd2ld[idx] * (cl * cl), cd)
        if delh <= 0:   T = maxthr * bs.traf.perf.ctdesld[idx]

    D = cd * qS

    return T,D
