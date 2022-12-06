import numpy as np
import bluesky as bs
from bluesky.tools.aero import ft, kts, gamma, gamma1, gamma2, R, beta, nm, fpm, vcasormach2tas, vcas2tas, vtas2cas, cas2tas, vcas2mach, g0, vmach2cas, density, vatmos, vcasormach

class Descent():

    def __init__(self, idx, altitude, tas, concas= -1):
        #Uitleg
        """
        simplifications:
        - Weight is kept constant
        - Gamma is per flight level of
        - decel. segments are calculated with 50x bigger timesteps

        """
        start_altitude = altitude + 100*ft
        final_altitude = 0

        self.segments = np.arange(final_altitude, start_altitude, 100*ft)
        self.speed = np.array([self.speedschedule(idx, i) for i in self.segments])
        if concas>0: self.speed = np.array([concas for i in self.segments])

        self.phase = np.array([self.phases(idx, i, self.speed[index], final_altitude - i) for index, i in enumerate(self.segments)])
        self.esft = np.array([self.esf(idx, i, self.speed[index]) for index, i in enumerate(self.segments)])

        td = np.array([self.TandD(idx, i, self.speed[index], self.phase[index]) for index,i in enumerate(self.segments)], dtype=object)
        self.T, self.D, data = zip(*td)

        self.tasspeeds = vcasormach2tas(self.speed, self.segments)

        initialspeed = self.speed[-1]/0.514444

        # if not bs.traf.ap.initiallog[idx]:
        #     file = open('initialspeeds.dat', 'a')
        #     file.write(str(bs.traf.id[idx]) + ',' + str(initialspeed))
        #     file.write("\n")
        #     file.close()
        #     print(bs.traf.id[idx],initialspeed)
        #     bs.traf.ap.initiallog[idx] = True

        self.rod = ((np.array(self.T) - np.array(self.D)) * self.tasspeeds) / (bs.traf.perf.mass[idx] * g0) * self.esft

        self.gammatas = abs(self.rod/self.tasspeeds)

        self.decel_alts = np.array([999 * ft, 1499 * ft, 1999 * ft, 2999 * ft, 5999 * ft, 9999 * ft, 26000*ft]) # lenght of 7
        self.vsegm = np.array([self.speedschedule(idx, i) for i in self.decel_alts] + [self.speedschedule(idx, 26000 * 1.1)])

        cas = vtas2cas(tas, altitude)

        self.decel_altspd = []

        for index, i in enumerate(self.decel_alts):
            if i > altitude: continue
            if self.vsegm[index + 1] <= cas:
                self.decel_altspd.append( (i, self.vsegm[index], self.vsegm[index + 1]) )
            elif self.vsegm[index + 1] > cas and self.vsegm[index]< cas:
                self.decel_altspd.append((i, self.vsegm[index], cas))


        self.added_alt = 0

        # for index, i in enumerate(self.segments):
        #     print('ALT:', self.segments[index]/ft/100, 'T', self.T[index], ' D:', self.D[index], ' CAS:', self.speed[index]/0.5144, 'TAS', self.tasspeeds[index], ' ESF:', self.esft[index], 'ROD', self.rod[index]/0.00508 )
        #     # print('ALT:', self.segments[index]/ft/100, ' CAS:', self.speed[index]/0.5144, ' PHS:', self.phase[index], ' ESF:', self.esft[index],
        #     #       ' T:', self.T[index], ' D:', self.D[index], ' ROD:', self.rod[index]/fpm, ' Gm:', self.gammatas[index], data[index])


    def tasspeeds_func(self, mach, alt):
        if alt>26000*ft: max = 99999
        else: max = vmach2cas(mach, alt)
        return vcasormach2tas(np.where(self.speed>max, max, self.speed), self.segments)



    def decelsegment(self, idx, alt, v0,v1, gammatas, wind = 0):

        # print('added segment for', round(alt / 0.3048 / 100, 2), round(v0 / 0.514444, 2), round(v1 / 0.514444, 2))

        m = 1

        add_alt, add_dist = 0, 0

        if v1<3: v1 = vmach2cas(v1, alt) # Overbodig?

        while np.round(v0,2) < np.round(v1,2):
            v0tas = vcasormach2tas(v0, alt + add_alt)
            v1tas = vcasormach2tas(v1, alt + add_alt)
            delspd = v0tas - v1tas
            need_ax = np.abs(delspd) > np.abs(bs.sim.simdt * m * bs.traf.perf.axmax[idx])
            ax = need_ax * np.sign(delspd) * 0.5
            tas = np.where(need_ax, v1tas + ax * bs.sim.simdt * m, v0tas)
            cas = vtas2cas(tas, alt + add_alt)

            T,D, data = self.TandD(idx, alt + add_alt, cas, self.phases(idx, alt + add_alt, cas, 0))
            rod = ((T - D) * (tas)) / (bs.traf.perf.mass[idx] * g0) * 0.3

            add_alt += rod * bs.sim.simdt * m
            add_dist += (tas + wind) * bs.sim.simdt * m

            v1 = cas

        olddist = self.descentdistance(gammatas, alt+add_alt, alt)

        # print('   Added:', (add_dist-olddist)/1852, add_alt/0.3048)

        self.added_alt = add_alt

        return (add_dist - olddist, add_alt)

    # print('decel segm for', v0n, v1n, add_dist, add_alt)

    # add_alt_n, add_dist_n = 0, 0
    #
    # while abs(add_alt_n) < abs(add_alt):
    #     esf_n = esf(idx, alt + add_alt_n, v0n)
    #     T_n, D_n = TandD(idx, alt + add_alt_n, v0n, phases(idx, alt + add_alt_n, v0n, 0))
    #     v0tas = vcasormach2tas(v0n, alt + add_alt_n)
    #     rod_n = ((T_n - D_n) * v0tas) / (bs.traf.perf.mass[idx] * g0) * esf_n
    #
    #     add_alt_n += rod_n * bs.sim.simdt * m
    #     add_dist_n += v0tas * bs.sim.simdt * m
    # # print('+', add_dist_n, add_alt_n)

    # return add_dist - add_dist_n


    def descentdistance(self, gammatas, alt0, alt1):
        # calculate distance needed to travel between two different altitudes using nominal descent rates (gammaTAS)

        start = int(np.ceil(alt0 / (100 * ft))) # index in gammatas
        start_rem = (100 * ft) - alt0 % (100 * ft) # remainder in start - 1

        # from start
        # add rem*angle anders hele segm*angle

        end = int(np.floor(alt1 / (100 * ft))) # index in gamma tas
        end_rem = alt1 % (100 * ft) # remainder in end + 0

        # print('ssted', start, end)

        # for i in range(start, end):
        #     print('gammatas', i, gammatas[i], (100 * ft) / gammatas[i])

        # print(start_rem/0.3048/100, end_rem/0.3048/100)
        # print((start_rem) / gammatas[start - 1], (end_rem) / gammatas[end])

        dist = sum([(100 * ft) / gammatas[i] for i in range(start, end)])
        dist += (start_rem) / gammatas[start - 1]
        if end>start: dist += (end_rem) / gammatas[end]

        return dist


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

    def speedschedule(self, idx, alt):
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

            # if alt > 9999 * ft and alt <= bs.traf.perf.hpdes[idx]:
            #     spd = bs.traf.perf.casdes2[idx] / kts
            #     return spd * kts
            # if alt > bs.traf.perf.hpdes[idx]:
            #     spd = bs.traf.perf.mades[idx]
                return spd

    def phases(self, idx, alt, cas, delalt):

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



    # # phase LD[5]: alt<3000, Speed below vmap (i.e. minimum approach speed) + 10kt
    # if alt <= 3000 * ft and cas < (vmap + 10 * kts) and delalt <= 0:
    #     return 5
    #
    # # phase AP[4]
    # # a. alt<8000, Speed between Vmcr+10 and Vmapp+10, v<>0
    # # b. alt<3000ft, Vmcr+10>V>Vmap+10
    # if (alt > ft and alt <= 8000. * ft and cas < (vmcr + 10. * kts) and delalt <= 0) or \
    #         ((alt > ft) & (alt <= (3000. * ft)) and cas >= (vmap + 10. * kts) and cas < (vmcr + 10. * kts) and delalt <= 0):
    #     return 4
    #
    #
    #
    # # phase CR[3]: in climb above 2000ft, in descent
    # # above 8000ft and below 8000ft if V>=Vmincr + 10kts
    # # a. climb
    # # b. above 8000ft
    # # c. descent
    # if (alt >= 2000 * ft and delalt >= 0) or \
    #         (alt > 8000 * ft) or \
    #         ( alt <= 8000 * ft and delalt <= 0 and  cas >= (vmcr + 10. * kts) ):
    #     return 3
    #
    #
    #
    #
    #
    # # phase GND: alt < 1 ft, i.e. as soon as on ground
    # if alt < ft:
    #     return 6



    def esf(self, idx, alt, spd):

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
        tas = vcasormach2tas(cas, alt)
        mass = bs.traf.perf.mass[idx]

        # rho = density(alt)
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

        # print('ld', alt/0.3048/100, cd,cl)

        return T,D, [cd, rho, bs.traf.perf.cd0cr[idx], bs.traf.perf.cd2cr[idx], cl, qS]
