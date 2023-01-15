'''
Calculate the attributes needed to determine the descent path of an aircraft, such as ROD and TAS for 100 ft segments

Created by: Winand Mathoera
Date: 31/12/2022
'''

import numpy as np
import bluesky as bs
from bluesky.tools.aero import ft, kts, gamma, gamma1, gamma2, R, beta, nm, fpm, vcasormach2tas, vcas2tas, vtas2cas, \
    cas2tas, vcas2mach, g0, vmach2cas, density, vatmos, vcasormach


class Descent():
    '''
    Definition: (Purpose of the class)
    Methods:
        __init__(): produce all needed attributes from other functions

    '''

    def __init__(self, idx, altitude, tas, concas= -1):
        '''
        Function: Call the different functions in the class to calculate the descent path attributes
        Simplifications:
            Mass is kept constant for a calculation
            Altitude intervals of 100 ft are taken

        Args:
            idx:        a/c index
            altitude:   a/c altitude [m]
            tas:        a/c true airspeed [m/s]
            concas:     constant calibrated airspeed if given, else use -1 to dismiss
        '''


        start_altitude = altitude + 100 * ft
        final_altitude = 0

        # array of altitude segments of 100 ft
        self.segments = np.arange(final_altitude, start_altitude, 100*ft)

        # determine speed from speedschedule in each segment, reject if constant CAS is given
        self.speed = np.array([self.speedschedule(idx, i) for i in self.segments])
        if concas>0: self.speed = np.array([concas for i in self.segments])

        # determine phase in each segment
        self.phase = np.array([self.phases(idx, i, self.speed[index], final_altitude - i) for
                               index, i in enumerate(self.segments)])

        # determine energy share factor (ESF) in each segment
        self.esft = np.array([self.esf(idx, i, self.speed[index]) for index, i in enumerate(self.segments)])

        # determine thrust and drag in each segment and separate into two arrays
        td = np.array([self.TandD(idx, i, self.speed[index], self.phase[index]) for
                       index,i in enumerate(self.segments)], dtype=object)
        self.T, self.D, data = zip(*td)

        # convert speeds from speedschedule to true airspeed
        self.tasspeeds = vcasormach2tas(self.speed, self.segments)

        # determine rate of descent (ROD) using total-energy equation
        self.rod = ((np.array(self.T) - np.array(self.D)) * self.tasspeeds) / (bs.traf.perf.mass[idx] * g0) * self.esft

        # determine angle between horizontal and vertical components
        self.gammatas = abs(self.rod/self.tasspeeds)

        # determine the speeds below and above the deceleration altitudes (from BADA manual)
        self.decel_alts = np.array([999 * ft, 1499 * ft, 1999 * ft, 2999 * ft, 5999 * ft, 9999 * ft, 26000*ft])
        self.vsegm = np.array([self.speedschedule(idx, i) for i in self.decel_alts] +
                              [self.speedschedule(idx, 26000 * ft * 1.1)])  #(x1.1 to go above last altitude)

        cas = vtas2cas(tas, altitude)

        self.decel_altspd = []


        # determine at which altitudes a deceleration segment is needed, format: (alt, new speed, old speed)
        # 1. if altitude is higher than 26000 ft, use all altitudes
        if altitude > self.decel_alts[-1]:
            self.decel_altspd = [(i, self.vsegm[index], self.vsegm[index + 1]) for
                                 index, i in enumerate(self.decel_alts)]
        # 2. if below 26000 ft
        else:
            for index, i in enumerate(self.decel_alts):
                # skip higher altitudes
                if i > altitude: continue
                # use segment if own speed is higher
                if self.vsegm[index + 1] <= cas:
                    self.decel_altspd.append( (i, self.vsegm[index], self.vsegm[index + 1]) )
                # use segment if speed is lower, however decelerate from own speed, instead of supposed speed
                elif self.vsegm[index + 1] > cas and self.vsegm[index]< cas:
                    self.decel_altspd.append((i, self.vsegm[index], cas))

        # Used for other functions
        self.added_alt = 0


        # USEFUL FOR DEBUGGING
        # print all attributes for all flight segments

        # for index, i in enumerate(self.segments):
        #     print('ALT:', self.segments[index]/ft/100, 'T', self.T[index], ' D:', self.D[index], ' CAS:', self.speed[index]/0.5144, 'TAS', self.tasspeeds[index], ' ESF:', self.esft[index], 'ROD', self.rod[index]/0.00508 )
        #     # print('ALT:', self.segments[index]/ft/100, ' CAS:', self.speed[index]/0.5144, ' PHS:', self.phase[index], ' ESF:', self.esft[index],
        #     #       ' T:', self.T[index], ' D:', self.D[index], ' ROD:', self.rod[index]/fpm, ' Gm:', self.gammatas[index], data[index])


    def tasspeeds_func(self, mach, alt):
        '''
        Function: Calculate true airspeed based on current Mach. Clip speed schedule to own speed
        Args:
            mach:       mach speed
            alt:        altitude of a/c
        '''
        if alt>26000*ft: max = 99999
        else: max = vmach2cas(mach, alt)
        return vcasormach2tas(np.where(self.speed>max, max, self.speed), self.segments)


    def decelsegment(self, idx, alt, v0,v1, gammatas, wind = 0):
        '''
        Function: Determine added distance and altitude from deceleration segment
        Args:
            idx:        a/c id
            alt:        altitude of a/c
            v0:         calibrated airspeed to be reached
            v1:         current calibrated airspeed
            gammatas:   array of gammatas angles
            wind:       speed of wind in flight direction m/s
        '''

        # multiplier to speed up calculations (set to 1 as base step)
        m = 1

        add_alt, add_dist = 0, 0

        # convert speed to cas if mach
        if v1<3: v1 = vmach2cas(v1, alt)

        # while CAS not reached yet
        while np.round(v0,2) < np.round(v1,2):

            # convert to TAS
            v0tas = vcasormach2tas(v0, alt + add_alt)
            v1tas = vcasormach2tas(v1, alt + add_alt)

            # find difference
            delspd = v0tas - v1tas

            # determine if acceleration is needed (transition longer than sim-timestep)
            need_ax = np.abs(delspd) > np.abs(bs.sim.simdt * m * bs.traf.perf.axmax[idx])

            # determine acceleration: +-0.5 or 0
            ax = need_ax * np.sign(delspd) * 0.5

            # calcualte new TAS and CAS
            tas = np.where(need_ax, v1tas + ax * bs.sim.simdt * m, v0tas)
            cas = vtas2cas(tas, alt + add_alt)

            # find new ROD
            T,D, data = self.TandD(idx, alt + add_alt, cas, self.phases(idx, alt + add_alt, cas, 0))
            rod = ((T - D) * (tas)) / (bs.traf.perf.mass[idx] * g0) * 0.3

            # calculate added altitude and added distance
            add_alt += rod * bs.sim.simdt * m
            add_dist += (tas + wind) * bs.sim.simdt * m

            # update speed for loop
            v1 = cas

        # find distance flown without deceleration segment
        olddist = self.descentdistance(gammatas, alt+add_alt, alt)

        self.added_alt = add_alt

        # return difference in distance, altitude should be the same as old altitude
        return (add_dist - olddist, add_alt)


    def descentdistance(self, gammatas, alt0, alt1):
        '''
        Function: calculate distance needed to travel between two different altitudes using nominal descent rates
        Args:
            gammatas:   array of gammatas angles
            alt0:       altitude to be reached
            alt1:       current altitude
        '''

        # calculate altitudes in starting and ending segments
        start = int(np.ceil(alt0 / (100 * ft))) # index in gammatas
        start_rem = (100 * ft) - alt0 % (100 * ft) # remainder in start - 1

        end = int(np.floor(alt1 / (100 * ft))) # index in gamma tas
        end_rem = alt1 % (100 * ft) # remainder in end + 0

        # sum up distances for all other segments in between
        dist = sum([(100 * ft) / gammatas[i] for i in range(start, end)])

        # add distance of starting segment
        dist += (start_rem) / gammatas[start - 1]

        # only add final altitude if end-index is greater than start-index
        if end>start: dist += (end_rem) / gammatas[end]

        return dist

    def speedschedule(self, idx, alt):
        '''
        Function: determine CAS based on speed schedule from the BADA manual
        Args:
            idx:    a/c id
            alt:    a/c altitude
        '''

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
            if alt > 9999*ft and alt <= 26000*ft:
                spd = 280
                return spd * kts
            if alt > 26000*ft:
                if bs.traf.perf.mmax[idx]>7000: spd = 0.78
                else: spd = 0.82

                return spd

    def phases(self, idx, alt, cas, delalt):
        '''
        Function: determine phase based on method taken from perfwlb.py, for single a/c
        Args:
            idx:    a/c id
            alt:    a/c altitude
            cas:    a/c calibrated airspeed
            delalt: difference in altitude
        '''

        vmap = bs.traf.perf.vmap[idx]
        vmcr = bs.traf.perf.vmcr[idx]

        # a. climb
        Caalt = np.array(alt >= (2000. * ft))
        Cavs = np.array(delalt >= 0.)
        cra = np.logical_and.reduce([Caalt, Cavs]) * 1

        # b. above 8000ft
        crb = np.array(alt > (8000. * ft)) * 1

        # c. descent
        Ccalt = np.array(alt <= (8000. * ft))
        Ccvs = np.array(delalt <= 0.)
        Ccspd = np.array(cas >= (vmcr + 10. * kts))
        crc = np.logical_and.reduce([Ccalt, Ccvs, Ccspd]) * 1

        # merge climb and descent phase
        cr = np.maximum(cra, np.maximum(crb, crc)) * 3

        Aaalt = np.array((alt > ft) & (alt <= (8000. * ft)))
        Aaspd = np.array(cas < (vmcr + 10. * kts))
        Aavs = np.array(delalt <= 0.)
        apa = np.logical_and.reduce([Aaalt, Aaspd, Aavs]) * 1
        # b. alt<3000ft, Vmcr+10>V>Vmap+10
        Abalt = np.array((alt > ft) & (alt <= (3000. * ft)))
        Abspd = np.array((cas >= (vmap + 10. * kts)) & (cas < (vmcr + 10. * kts)))
        Abvs = np.array(delalt <= 0.)
        apb = np.logical_and.reduce([Abalt, Abspd, Abvs]) * 1
        # merge a. and b.
        ap = np.maximum.reduce([apa, apb]) * 4

        # -------------------------------------------------
        # phase LD[5]: alt<3000, Speed below vmap (i.e. minimum approach speed) + 10kt
        Lalt = np.array(alt <= (3000.0 * ft))
        Lspd = np.array(cas < (vmap + 10.0 * kts))
        Lvs = np.array(delalt <= 0.0)
        ld = np.logical_and.reduce([Lalt, Lspd, Lvs]) * 5

        # -------------------------------------------------
        # phase GND: alt < 1 ft, i.e. as soon as on ground
        gd = np.array(alt <= ft) * 6

        return np.maximum.reduce([ap, ld, cr, gd])


    def esf(self, idx, alt, spd):
        '''
        Function: determine energy share factor based on method taken from performance.py, for single a/c
        Args:
            idx:    a/c id
            alt:    a/c altitude
            spd:    a/c CAS or Mach
        '''

        if spd < 3: M = spd
        else: M = vcas2mach(spd, alt)

        selmach = spd < 2.0

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

    def TandD(self, idx, alt, cas, phase):
        '''
        Function: determine thrust and drag based on method taken from perfwlb.py, for single a/c
        Args:
            idx:    a/c id
            alt:    a/c altitude
            cas:    a/c calibrated airspeed
            phase:  a/c phase
        '''

        tas = vcasormach2tas(cas, alt)
        mass = bs.traf.perf.mass[idx]

        p, rho, temp = vatmos(alt)

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

        return T,D, [cd, rho, bs.traf.perf.cd0cr[idx], bs.traf.perf.cd2cr[idx], cl, qS]
