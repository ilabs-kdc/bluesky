""" Autopilot Implementation."""
from math import sin, cos, radians, sqrt, atan, floor, ceil, tan
import numpy as np
try:
    from collections.abc import Collection
except ImportError:
    # In python <3.3 collections.abc doesn't exist
    from collections import Collection
import bluesky as bs
from bluesky import stack
from bluesky.tools import geo
from bluesky.tools.misc import degto180, angleFromCoordinate
from bluesky.tools.position import txt2pos
from bluesky.tools.aero import ft, nm, fpm, vcasormach2tas, vcas2tas, tas2cas, cas2tas, g0, vmach2cas
from bluesky.tools.geo import latlondist, qdrdist
from bluesky.core import Entity, timed_function
from .route import Route
from bluesky.traffic.performance.wilabada.performance import esf_d, PHASE
from bluesky.traffic.performance.wilabada.ESTIMATOR import EEI
from bluesky.stack.simstack import pcall
# from .descent import find_gamma
from .descentv2 import Descent


bs.settings.set_variable_defaults(fms_dt=10.5)


class Autopilot(Entity, replaceable=True):
    ''' BlueSky Autopilot implementation. '''
    def __init__(self):
        super().__init__()

        # Standard self.steepness for descent
        self.steepness = 3000. * ft / (10. * nm)

        # From here, define object arrays
        with self.settrafarrays():

            # FMS directions
            self.trk = np.array([])
            self.spd = np.array([])
            self.tas = np.array([])
            self.alt = np.array([])
            self.vs  = np.array([])

            # Speed Schedule #ADDED
            self.spds = np.array([])
            # self.swdescent = np.array([])

            # VNAV variables
            self.dist2vs  = np.array([])  # distance from coming waypoint to TOD
            self.dist2accel = np.array([]) # Distance to go to acceleration(decelaration) for turn next waypoint [nm]
            self.dist2vscount = np.array([]) #ADDED
            self.dist2vscountpassed = np.array([])

            self.swvnavvs = np.array([])  # whether to use given VS or not
            self.vnavvs   = np.array([])  # vertical speed in VNAV

            # LNAV variables
            self.qdr2wp      = np.array([]) # Direction to waypoint from the last time passing was checked
                                            # to avoid 180 turns due to updated qdr shortly before passing wp
            self.dist2wp     = np.array([]) # [nm] Distance to active waypoint


             # Traffic navigation information
            self.orig = []  # Four letter code of origin airport
            self.dest = []  # Four letter code of destination airport

            # Default values
            self.bankdef = np.array([])  # nominal bank angle, [radians]
            self.vsdef = np.array([]) # [m/s]default vertical speed of autopilot

            # Currently used roll/bank angle [rad]
            self.turnphi = np.array([])  # [rad] bank angle setting of autopilot

            # Route objects
            self.route = []

            self.EEI = EEI()
            self.TOsw = np.array([])
            self.TOdf = np.array([], dtype='object')
            self.TO_slope = np.array([])
            self.EEI_IAS = np.array([])
            self.EEI_ROC = np.array([])

            # Descent path switch
            self.dpswitch = np.array([])
            self.geodescent = np.array([])
            self.steepnessv2 = np.array([])
            self.prevconst = np.array([], dtype=bool)   # Remember if wpt can be flown in continuous descent
            self.prevwptgeo = np.array([], dtype=bool)  # Remember if last wpt has geo/tod switch

            self.altdismiss = np.array([], dtype=bool)
            self.faltdismiss = np.array([], dtype=bool)
            self.hdgdismiss = np.array([], dtype=bool)
            self.spddismiss = np.array([], dtype=bool)

            self.initiallog = np.array([], dtype=bool)

    def create(self, n=1):
        super().create(n)

        # FMS directions
        self.tas[-n:] = bs.traf.tas[-n:]
        self.trk[-n:] = bs.traf.trk[-n:]
        self.alt[-n:] = bs.traf.alt[-n:]

        self.TOsw[-n:] = False
        self.TOdf[-n:] = False
        self.TO_slope[-n:] = False
        self.EEI_IAS[-n:] = 0
        self.EEI_ROC[-n:] = 0

        self.dpswitch[-n:] = True
        self.geodescent[-n:] = False
        self.steepnessv2[-n:] = self.steepness
        self.prevconst[-n:] = False
        self.prevconst[-n:] = None

        self.altdismiss[-n:] = False
        self.faltdismiss[-n:] = False
        self.hdgdismiss[-n:] = False
        self.spddismiss[-n:] = False

        self.initiallog[-n:] = False

        # LNAV variables
        self.qdr2wp[-n:] = -999.   # Direction to waypoint from the last time passing was checked
        self.dist2wp[-n:]  = -999. # Distance to go to next waypoint [nm]

        # to avoid 180 turns due to updated qdr shortly before passing wp

        # VNAV Variables
        self.dist2vs[-n:] = -999.
        self.dist2accel[-n:] = -999.  # Distance to go to acceleration(decelaration) for turn next waypoint [nm]
        self.dist2vscount [-n:] = -999.
        self.dist2vscountpassed[-n:] = True

        # Traffic performance data
        #(temporarily default values)
        self.vsdef[-n:] = 1500. * fpm   # default vertical speed of autopilot
        self.bankdef[-n:] = np.radians(25.)

        # Route objects
        for ridx, acid in enumerate(bs.traf.id[-n:]):
            self.route[ridx - n] = Route(acid)

    #no longer timed @timed_function(name='fms', dt=bs.settings.fms_dt, manual=True)
    def update_fms(self, qdr, dist):
        # Check which aircraft i have reached their active waypoint
        # Shift waypoints for aircraft i where necessary
        # Reached function return list of indices where reached logic is True
        for i in bs.traf.actwp.Reached(qdr, dist, bs.traf.actwp.flyby,
                                       bs.traf.actwp.flyturn,bs.traf.actwp.turnrad,bs.traf.actwp.swlastwp):

            # Save current wp speed for use on next leg when we pass this waypoint
            # VNAV speeds are always FROM-speeds, so we accelerate/decellerate at the waypoint
            # where this speed is specified, so we need to save it for use now
            # before getting the new data for the next waypoint

            # Get speed for next leg from the waypoint we pass now
            bs.traf.actwp.spd[i]    = bs.traf.actwp.nextspd[i]
            bs.traf.actwp.spdcon[i] = bs.traf.actwp.nextspd[i]

            # Execute stack commands for the still active waypoint, which we pass
            self.route[i].runactwpstack()

            # If specified, use the given turn radius of passing wp for bank angle
            if bs.traf.actwp.flyturn[i]:
                if bs.traf.actwp.turnspd[i]>=0.:
                    turnspd = bs.traf.actwp.turnspd[i]
                else:
                    turnspd = bs.traf.tas[i]

                if bs.traf.actwp.turnrad[i] > 0.:
                    self.turnphi[i] = atan(turnspd*turnspd/(bs.traf.actwp.turnrad[i]*nm*g0)) # [rad]
                else:
                    self.turnphi[i] = 0.0  # [rad] or leave untouched???

            else:
                self.turnphi[i] = 0.0  #[rad] or leave untouched???

            # Get next wp, if there still is one
            if not bs.traf.actwp.swlastwp[i]:

                r = self.route[i]
                if r.wpalt[r.iactwp] > -999:
                    # bs.traf.actwp.altconst[i] = True
                    self.dpswitch[i] = True
                else:
                    # bs.traf.actwp.altconst[i] = False
                    self.dpswitch[i] = False

                if self.dist2vscount[i] >= 0: self.dist2vscount[i] -= 1

                lat, lon, alt, bs.traf.actwp.nextspd[i], bs.traf.actwp.xtoalt[i], toalt, \
                    bs.traf.actwp.xtorta[i], bs.traf.actwp.torta[i], \
                    lnavon, flyby, flyturn, turnrad, turnspd,\
                    bs.traf.actwp.next_qdr[i], bs.traf.actwp.swlastwp[i] =      \
                    self.route[i].getnextwp()  # note: xtoalt,toalt in [m]

            # Prevent trying to activate the next waypoint when it was already the last waypoint
            else:
                bs.traf.swlnav[i] = False
                bs.traf.swvnav[i] = False
                bs.traf.swvnavspd[i] = False
                continue # Go to next a/c which reached its active waypoint

            # End of route/no more waypoints: switch off LNAV using the lnavon
            # switch returned by getnextwp
            if not lnavon and bs.traf.swlnav[i]:
                bs.traf.swlnav[i] = False
                # Last wp: copy last wp values for alt and speed in autopilot
                if bs.traf.swvnavspd[i] and bs.traf.actwp.nextspd[i]>= 0.0:
                    bs.traf.selspd[i] = bs.traf.actwp.nextspd[i]

            # In case of no LNAV, do not allow VNAV mode on its own
            bs.traf.swvnav[i] = bs.traf.swvnav[i] and bs.traf.swlnav[i]

            bs.traf.actwp.lat[i] = lat  # [deg]
            bs.traf.actwp.lon[i] = lon  # [deg]
            # 1.0 in case of fly by, else fly over
            bs.traf.actwp.flyby[i] = int(flyby)

            # User has entered an altitude for this waypoint
            if alt >= -0.01 and not bs.traf.actwp.tempaltconst[i]:
                bs.traf.actwp.nextaltco[i] = alt  # [m]

            #if not bs.traf.swlnav[i]:
            #    bs.traf.actwp.spd[i] = -997.

            # VNAV spd mode: use speed of this waypoint as commanded speed
            # while passing waypoint and save next speed for passing next wp
            # Speed is now from speed! Next speed is ready in wpdata
            if bs.traf.swvnavspd[i] and bs.traf.actwp.spd[i]>= 0.0:
                    bs.traf.selspd[i] = bs.traf.actwp.spd[i]

            # Update qdr and turndist for this new waypoint for ComputeVNAV
            qdr[i], distnmi = geo.qdrdist(bs.traf.lat[i], bs.traf.lon[i],
                                        bs.traf.actwp.lat[i], bs.traf.actwp.lon[i])

            dist[i] = distnmi*nm
            self.dist2wp[i] = distnmi*nm

            bs.traf.actwp.curlegdir[i] = qdr[i]
            bs.traf.actwp.curleglen[i] = distnmi

            # Update turndist so ComputeVNAV works, is there a next leg direction or not?
            if bs.traf.actwp.next_qdr[i] < -900.:
                local_next_qdr = qdr[i]
            else:
                local_next_qdr = bs.traf.actwp.next_qdr[i]

            # Get flyturn switches and data
            bs.traf.actwp.flyturn[i]     = flyturn
            bs.traf.actwp.turnrad[i]     = turnrad

            # Pass on whether currently flyturn mode:
            # at beginning of leg,c copy tonextwp to lastwp
            # set next turn False
            bs.traf.actwp.turnfromlastwp[i] = bs.traf.actwp.turntonextwp[i]
            bs.traf.actwp.turntonextwp[i]   = False

            # Keep both turning speeds: turn to leg and turn from leg
            bs.traf.actwp.oldturnspd[i]  = bs.traf.actwp.turnspd[i] # old turnspd, turning by this waypoint
            if bs.traf.actwp.flyturn[i]:
                bs.traf.actwp.turnspd[i] = turnspd                  # new turnspd, turning by next waypoint
            else:
                bs.traf.actwp.turnspd[i] = -990.

            # Calculate turn dist (and radius which we do not use) now for scalar variable [i]
            bs.traf.actwp.turndist[i], dummy = \
                bs.traf.actwp.calcturn(bs.traf.tas[i], self.bankdef[i],
                                        qdr[i], local_next_qdr,turnrad)  # update turn distance for VNAV

            # Reduce turn dist for reduced turnspd
            if bs.traf.actwp.flyturn[i] and bs.traf.actwp.turnrad[i]<0.0 and bs.traf.actwp.turnspd[i]>=0.:
                turntas = cas2tas(bs.traf.actwp.turnspd[i], bs.traf.alt[i])
                bs.traf.actwp.turndist[i] = bs.traf.actwp.turndist[i]*turntas*turntas/(bs.traf.tas[i]*bs.traf.tas[i])

            # VNAV = FMS ALT/SPD mode incl. RTA
            self.ComputeVNAV(i, toalt, bs.traf.actwp.xtoalt[i], bs.traf.actwp.torta[i],
                             bs.traf.actwp.xtorta[i])



        # End of per waypoint i switching loop
        # Update qdr2wp with up-to-date qdr, now that we have checked passing wp
        self.qdr2wp = qdr%360.

        # Continuous guidance when speed constraint on active leg is in update-method

        # If still an RTA in the route and currently no speed constraint
        for iac in np.where((bs.traf.actwp.torta > -99.)*(bs.traf.actwp.spdcon<0.0))[0]:
            iwp = bs.traf.ap.route[iac].iactwp
            if bs.traf.ap.route[iac].wprta[iwp]>-99.:

                 # For all a/c flying to an RTA waypoint, recalculate speed more often
                dist2go4rta = geo.kwikdist(bs.traf.lat[iac],bs.traf.lon[iac], \
                                           bs.traf.actwp.lat[iac],bs.traf.actwp.lon[iac])*nm \
                               + bs.traf.ap.route[iac].wpxtorta[iwp] # last term zero for active wp rta

                # Set bs.traf.actwp.spd to rta speed, if necessary
                self.setspeedforRTA(iac,bs.traf.actwp.torta[iac],dist2go4rta)

                # If VNAV speed is on (by default coupled to VNAV), use it for speed guidance
                if bs.traf.swvnavspd[iac] and bs.traf.actwp.spd[iac]>=0.0:
                     bs.traf.selspd[iac] = bs.traf.actwp.spd[iac]

    def dismiss_command(self):
        '''
        Function: Find minimum time needed to decelerate to landing speed. If speed command is given and landing
        speed cannot be met, override speed command with speed schedule speeds.

        Created by: Winand Mathoera
        Date: 26/09/2022
        '''

        for i,route in enumerate(self.route):
            if len(route.wpname) == 0:
                continue

            if bs.traf.swvnavspd[i] == True and bs.traf.swvnav[i] == True:
                continue

            # random number LOOK FOR ALTERNATIVE
            max_decel = 0.3

            # Landing speed based on BADA 3.10
            kts = 0.5144
            spd_landing = bs.traf.perf.vmld + 5 * kts

            # Time needed to decelerate to landing speed
            preferred_time = (bs.traf.cas[i] - spd_landing) / max_decel

            preferred_distance = bs.traf.alt[i] / self.steepness
            dist2vs = abs(bs.traf.alt[i] - bs.traf.actwp.nextaltco[i]) / self.steepness  # + bs.traf.actwp.turndist

            # Find distance to destination
            dist = latlondist(bs.traf.lat[i], bs.traf.lon[i], route.wplat[0], route.wplon[0])
            dist2wpt = dist * 1.
            for j in range (len(route.wplat)-1):
                dist += latlondist(route.wplat[j], route.wplon[j], route.wplat[j+1], route.wplon[j+1])

            # Estimate travel time based on current speed and final speed
            estimated_time = dist/ ((bs.traf.tas[i] + spd_landing[i]) / 2)

            ### Dismiss speed command before landing
            if estimated_time < preferred_time[i] * 1.1 and bs.traf.swdescent[i] and not bs.traf.swvnavspd[i]:
                bs.traf.swvnavspd[i] = True

            ### Dismiss altitude command before landing
            if dist2wpt < dist2vs and bs.traf.swdescent[i] and not bs.traf.swvnav[i]:
                print(bs.traf.id[i], 'Turned on VNAV')
                bs.traf.swvnav[i] = True
                self.dist2vs[i] = dist2vs

    def update(self):
        # FMS LNAV mode:
        # qdr[deg],distinnm[nm]
        qdr, distinnm = geo.qdrdist(bs.traf.lat, bs.traf.lon,
                                    bs.traf.actwp.lat, bs.traf.actwp.lon)  # [deg][nm])
        self.qdr2wp  = qdr
        self.dist2wp = distinnm*nm  # Conversion to meters

        # FMS route update and possibly waypoint shift. Note: qdr, dist2wp will be updated accordingly in case of wp switch
        self.update_fms(qdr, self.dist2wp) # Updates self.qdr2wp when necessary

        # print((self.altdismiss))
        # print((abs(bs.traf.alt-bs.traf.selalt)<10))
        # print((self.altdismiss) & (abs(bs.traf.alt-bs.traf.selalt)<10))
        bs.traf.swvnav = np.where( (self.altdismiss) & (abs(bs.traf.alt-bs.traf.selalt)<10), True, bs.traf.swvnav)

        for index, i in enumerate(bs.traf.id):
            if self.altdismiss[index] and bs.traf.swvnav[index]:
                self.setVNAV(index, True)
                self.altdismiss[index] = False

        #================= Continuous FMS guidance ========================

        # Waypoint switching in the loop above was scalar (per a/c with index i)
        # Code below is vectorized, with arrays for all aircraft

        # Do VNAV start of descent check
        #dy = (bs.traf.actwp.lat - bs.traf.lat)  #[deg lat = 60 nm]
        #dx = (bs.traf.actwp.lon - bs.traf.lon) * bs.traf.coslat #[corrected deg lon = 60 nm]
        #self.dist2wp   = 60. * nm * np.sqrt(dx * dx + dy * dy) # [m]

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # bs.traf.actwp.tempaltconst = np.where(self.dist2vscount < 1, False, bs.traf.actwp.tempaltconst)

        self.dist2vs = np.where( (self.dist2vscount<0)*self.dist2vscountpassed*(self.dist2vs<99990), self.dist2wp-self.dist2vs, self.dist2vs)
        self.dist2vscountpassed = np.where( self.dist2vscount<0, False, self.dist2vscountpassed)
        startdescent = (self.dist2wp < self.dist2vs) * (self.dist2vscount < 1)

        # print(1, self.dist2wp, self.dist2vs, self.dist2vscount, self.dist2vscountpassed)

        self.swvnavvs = bs.traf.swvnav * np.where(bs.traf.swlnav, startdescent,
                                                  self.dist2wp <= np.maximum(185.2, bs.traf.actwp.turndist))
        bs.traf.actwp.vs = np.where(self.geodescent, self.steepnessv2*bs.traf.gs, -999)

        self.vnavvs = np.where(self.swvnavvs, bs.traf.actwp.vs, self.vnavvs)
        selvs = np.where(abs(bs.traf.selvs) > 0.1, bs.traf.selvs, self.vsdef)  # m/s
        self.vs = np.where(self.swvnavvs, self.vnavvs, selvs)
        self.alt = np.where(self.swvnavvs, bs.traf.actwp.nextaltco, bs.traf.selalt)
        # When descending or climbing in VNAV also update altitude command of select/hold mode
        bs.traf.selalt = np.where(self.swvnavvs, bs.traf.actwp.nextaltco, bs.traf.selalt)


        """ 
        # VNAV logic: descend as late as possible, climb as soon as possible
        startdescent = (self.dist2wp < self.dist2vs) + (bs.traf.actwp.nextaltco > bs.traf.alt)

        # If not lnav:Climb/descend if doing so before lnav/vnav was switched off
        #    (because there are no more waypoints). This is needed
        #    to continue descending when you get into a conflict
        #    while descending to the destination (the last waypoint)
        #    Use 0.1 nm (185.2 m) circle in case turndist might be zero
        self.swvnavvs = bs.traf.swvnav * np.where(bs.traf.swlnav, startdescent,
                                        self.dist2wp <= np.maximum(185.2,bs.traf.actwp.turndist))

        #Recalculate V/S based on current altitude and distance to next alt constraint
        # How much time do we have before we need to descend?

        t2go2alt = np.maximum(0.,(self.dist2wp + bs.traf.actwp.xtoalt - bs.traf.actwp.turndist)) \
                                    / np.maximum(0.5,bs.traf.gs)

        # use steepness to calculate V/S unless we need to descend faster
        bs.traf.actwp.vs = np.maximum(self.steepness*bs.traf.gs, \
                                np.abs((bs.traf.actwp.nextaltco-bs.traf.alt))  \
                                /np.maximum(1.0,t2go2alt))

        self.vnavvs  = np.where(self.swvnavvs, bs.traf.actwp.vs, self.vnavvs)
        #was: self.vnavvs  = np.where(self.swvnavvs, self.steepness * bs.traf.gs, self.vnavvs)

        # self.vs = np.where(self.swvnavvs, self.vnavvs, self.vsdef * bs.traf.limvs_flag)
        selvs    = np.where(abs(bs.traf.selvs) > 0.1, bs.traf.selvs, self.vsdef) # m/s
        self.vs  = np.where(self.swvnavvs, self.vnavvs, selvs)
        self.alt = np.where(self.swvnavvs, bs.traf.actwp.nextaltco, bs.traf.selalt)

        # When descending or climbing in VNAV also update altitude command of select/hold mode
        bs.traf.selalt = np.where(self.swvnavvs,bs.traf.actwp.nextaltco,bs.traf.selalt)
        """
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # LNAV commanded track angle
        self.trk = np.where(bs.traf.swlnav, self.qdr2wp, self.trk)

        # FMS speed guidance: anticipate accel/decel distance for next leg or turn

        # Calculate actual distance it takes to decelerate/accelerate based on two cases: turning speed (decel)

        # Normally next leg speed (actwp.spd) but in case we fly turns with a specified turn speed
        # use the turn speed

        # Is turn speed specified and are we not already slow enough? We only decelerate for turns, not accel.
        turntas       = np.where(bs.traf.actwp.turnspd>0.0, vcas2tas(bs.traf.actwp.turnspd, bs.traf.alt),
                                 -1.0+0.*bs.traf.tas)
        swturnspd     = bs.traf.actwp.flyturn*(turntas>0.0)*(bs.traf.actwp.turnspd>0.0)
        turntasdiff   = np.maximum(0.,(bs.traf.tas - turntas)*(turntas>0.0))

        # t = (v1-v0)/a ; x = v0*t+1/2*a*t*t => dx = (v1*v1-v0*v0)/ (2a)
        dxturnspdchg = distaccel(turntas,bs.traf.tas, bs.traf.perf.axmax)
#        dxturnspdchg = 0.5*np.abs(turntas*turntas-bs.traf.tas*bs.traf.tas)/(np.sign(turntas-bs.traf.tas)*np.maximum(0.01,np.abs(ax)))
#        dxturnspdchg  = np.where(swturnspd, np.abs(turntasdiff)/np.maximum(0.01,ax)*(bs.traf.tas+0.5*np.abs(turntasdiff)),
#                                                                   0.0*bs.traf.tas)

        # Decelerate or accelerate for next required speed because of speed constraint or RTA speed
        # Note that because nextspd comes from the stack, and can be either a mach number or
        # a calibrated airspeed, it can only be converted from Mach / CAS [kts] to TAS [m/s]
        # once the altitude is known.
        nexttas = vcasormach2tas(bs.traf.actwp.nextspd, bs.traf.alt)

#       tasdiff   = (nexttas - bs.traf.tas)*(bs.traf.actwp.spd>=0.) # [m/s]


        # t = (v1-v0)/a ; x = v0*t+1/2*a*t*t => dx = (v1*v1-v0*v0)/ (2a)

        dxspdconchg = distaccel(bs.traf.tas, nexttas, bs.traf.perf.axmax)

        # ADDED Update speed schedule speeds
        self.speedschedule()



        # ADDED Turn on speed schedule bool
        usespds = (self.spds < bs.traf.actwp.spdcon) * bs.traf.swdescent #or bs.traf.actwp.spdcon < 0)
        # ADDED During descent, speed schedule can be overwritten if own speed is already slower than schedule
        self.spds = np.where( (vcasormach2tas(self.spds, bs.traf.alt) > (1.01 * vcasormach2tas(bs.traf.selspd, bs.traf.alt))) * (bs.traf.selspd > 1),
            bs.traf.selspd, self.spds)

        # Check also whether VNAVSPD is on, if not, SPD SEL has override for next leg
        # and same for turn logic
        usenextspdcon = (self.dist2wp < dxspdconchg)*(bs.traf.actwp.nextspd>-990.) * \
                            bs.traf.swvnavspd*bs.traf.swvnav*bs.traf.swlnav* ( self.spds > (bs.traf.actwp.nextspd * bs.traf.swdescent ))
        useturnspd = np.logical_or(bs.traf.actwp.turntonextwp,\
                                   (self.dist2wp < dxturnspdchg+bs.traf.actwp.turndist) * \
                                        swturnspd*bs.traf.swvnavspd*bs.traf.swvnav*bs.traf.swlnav)

        # Hold turn mode can only be switched on here, cannot be switched off here (happeps upon passing wp)
        bs.traf.actwp.turntonextwp = np.logical_or(bs.traf.actwp.turntonextwp,useturnspd)

        # Which CAS/Mach do we have to keep? VNAV, last turn or next turn?
        oncurrentleg = (abs(degto180(bs.traf.trk - qdr)) < 2.0) # [deg]
        inoldturn    = (bs.traf.actwp.oldturnspd > 0.) * np.logical_not(oncurrentleg)

        # Avoid using old turning speeds when turning of this leg to the next leg
        # by disabling (old) turningspd when on leg
        bs.traf.actwp.oldturnspd = np.where(oncurrentleg*(bs.traf.actwp.oldturnspd>0.), -998.,
                                            bs.traf.actwp.oldturnspd)

        # turnfromlastwp can only be switched off here, not on (latter happens upon passing wp)
        bs.traf.actwp.turnfromlastwp = np.logical_and(bs.traf.actwp.turnfromlastwp,inoldturn)

        # Select speed: turn sped, next speed constraint, or current speed constraint
        # bs.traf.selspd = np.where(useturnspd,bs.traf.actwp.turnspd,
        #                           np.where(usenextspdcon, bs.traf.actwp.nextspd,
        #                                    np.where((bs.traf.actwp.spdcon>=0)*bs.traf.swvnavspd,bs.traf.actwp.spd,
        #                                                                     bs.traf.selspd)))

        # # ADDED
        bs.traf.selspd = np.where(useturnspd, bs.traf.actwp.turnspd,
                                  np.where(usenextspdcon, bs.traf.actwp.nextspd,
                                           np.where((bs.traf.actwp.spdcon >= 0) * bs.traf.swvnavspd,
                                                    np.where(usespds, self.spds, bs.traf.actwp.spdcon),
                                                    np.where(bs.traf.swvnavspd & bs.traf.swdescent, self.spds, bs.traf.selspd))))

        # Temporary override when still in old turn
        bs.traf.selspd = np.where(inoldturn*(bs.traf.actwp.oldturnspd>0.)*bs.traf.swvnavspd*bs.traf.swvnav*bs.traf.swlnav,
                                  bs.traf.actwp.oldturnspd,bs.traf.selspd)

        # Another overwrite
        self.ESTspeeds()
        spdcon = np.logical_not(bs.traf.actwp.nextspd <= 0)
        self.EEI_IAS = np.where(spdcon, np.minimum(bs.traf.actwp.nextspd, self.EEI_IAS), self.EEI_IAS)
        bs.traf.selspd = np.where(self.TOsw, self.EEI_IAS, bs.traf.selspd)

        sw = np.logical_not(bs.traf.cas < bs.traf.perf.vmto*0.97)
        # bs.traf.actwp.vs = np.where(self.TOsw, self.EEI_ROC, selvs)
        bs.traf.actwp.vs = np.where(self.TOsw, self.EEI_ROC, bs.traf.actwp.vs)
        sw_alt = np.logical_not(bs.traf.alt < 1)
        sw = np.where(sw_alt, True, sw)
        sw_vs_restr = np.logical_not(self.alt == bs.traf.alt)

        bs.traf.vs = np.where(self.TOsw, np.where(sw_vs_restr, np.where(self.TOsw, np.where(sw, self.EEI_ROC, 0), selvs), 0), bs.traf.vs)
        # self.vs = np.where(self.TOsw, self.EEI_ROC, selvs)
        self.vs = np.where(self.TOsw, self.EEI_ROC, self.vs)
        self.tas = vcasormach2tas(bs.traf.selspd, bs.traf.alt)

    @timed_function(dt=3, manual = True)
    def ESTspeeds(self):
        self.EEI_IAS, self.EEI_ROC = self.EEI.IAS_ROC(self.TOdf, bs.traf.alt)

    def ComputeVNAV(self, idx, toalt, xtoalt, torta, xtorta):
        # debug print ("ComputeVNAV for",bs.traf.id[idx],":",toalt/ft,"ft  ",xtoalt/nm,"nm")

        # Check if there is a target altitude and VNAV is on, else return doing nothing
        if toalt < 0 or not bs.traf.swvnav[idx]:
            self.dist2vs[idx] = -999. #dist to next wp will never be less than this, so VNAV will do nothing
            return

        # Flat earth distance to next wp
        dy = (bs.traf.actwp.lat[idx] - bs.traf.lat[idx])  # [deg lat = 60. nm]
        dx = (bs.traf.actwp.lon[idx] - bs.traf.lon[idx]) * bs.traf.coslat[idx]  # [corrected deg lon = 60. nm]
        legdist = 60. * nm * np.sqrt(dx * dx + dy * dy)  # [m]

        # Check  whether active waypoint speed needs to be adjusted for RTA
        # sets bs.traf.actwp.spd, if necessary
        #debug print("xtorta+legdist =",(xtorta+legdist)/nm)
        self.setspeedforRTA(idx, torta, xtorta+legdist) # all scalar

        # So: somewhere there is an altitude constraint ahead
        # Compute proper values for bs.traf.actwp.nextaltco, self.dist2vs, self.alt, bs.traf.actwp.vs
        # Descent VNAV mode (T/D logic)
        #
        # xtoalt  =  distance to go to next altitude constraint at a waypoint in the route
        #           (could be beyond next waypoint) [m]
        #
        # toalt   = altitude at next waypoint with an altitude constraint
        #
        # dist2vs = autopilot starts climb or descent when the remaining distance to next waypoint
        #           is this distance
        #
        #
        # VNAV Guidance principle:
        #
        #
        #                          T/C------X---T/D
        #                           /    .        \
        #                          /     .         \
        #       T/C----X----.-----X      .         .\
        #       /           .            .         . \
        #      /            .            .         .  X---T/D
        #     /.            .            .         .        \
        #    / .            .            .         .         \
        #   /  .            .            .         .         .\
        # pos  x            x            x         x         x X
        #
        #
        #  X = waypoint with alt constraint  x = Wp without prescribed altitude
        #
        # - Ignore and look beyond waypoints without an altitude constraint
        # - Climb as soon as possible after previous altitude constraint
        #   and climb as fast as possible, so arriving at alt earlier is ok
        # - Descend at the latest when necessary for next altitude constraint
        #   which can be many waypoints beyond current actual waypoint


        # VNAV Descent mode
        if bs.traf.alt[idx] > toalt + 10. * ft and not self.TOsw[idx]:

            r = self.route[idx]
            icurr = r.iactwp  # index of active waypoint

            # print('kom ik wel bij alle punten? ik ben nu bij :', r.wpname[icurr])
            # print('wat zijn mn bools? :', bs.traf.actwp.altconst[idx], self.dpswitch[idx])

            # if bs.traf.actwp.altconst[idx] and self.dpswitch[idx]:
            if self.dpswitch[idx]:
                self.descentpath(idx)
                self.dpswitch[idx] = False

            # Turn on descent switch for speed schedule
            bs.traf.swdescent[idx] = True

            # #Calculate max allowed altitude at next wp (above toalt)
            # bs.traf.actwp.nextaltco[idx] = min(bs.traf.alt[idx],toalt + xtoalt * self.steepness) # [m] next alt constraint
            # bs.traf.actwp.xtoalt[idx]    = xtoalt # [m] distance to next alt constraint measured from next waypoint
            #
            # # Dist to waypoint where descent should start [m]
            # self.dist2vs[idx] = bs.traf.actwp.turndist[idx] + \
            #                    np.abs(bs.traf.alt[idx] - bs.traf.actwp.nextaltco[idx]) / (self.steepness)
            #
            # # Flat earth distance to next wp
            # dy = (bs.traf.actwp.lat[idx] - bs.traf.lat[idx])   # [deg lat = 60. nm]
            # dx = (bs.traf.actwp.lon[idx] - bs.traf.lon[idx]) * bs.traf.coslat[idx] # [corrected deg lon = 60. nm]
            # legdist = 60. * nm * np.sqrt(dx * dx + dy * dy)  # [m]
            #
            #
            # # If the descent is urgent, descend with maximum steepness
            # if legdist < self.dist2vs[idx]: # [m]
            #     self.alt[idx] = bs.traf.actwp.nextaltco[idx]  # dial in altitude of next waypoint as calculated
            #
            #     t2go         = max(0.1, legdist + xtoalt) / max(0.01, bs.traf.gs[idx])
            #     bs.traf.actwp.vs[idx]  = (bs.traf.actwp.nextaltco[idx] - bs.traf.alt[idx]) / t2go
            #
            # else:
            #     # Calculate V/S using self.steepness,
            #     # protect against zero/invalid ground speed value
            #
            #     bs.traf.actwp.vs[idx] = -self.steepness * (bs.traf.gs[idx] +
            #           (bs.traf.gs[idx] < 0.2 * bs.traf.tas[idx]) * bs.traf.tas[idx])

        # VNAV climb mode: climb as soon as possible (T/C logic)
        elif bs.traf.alt[idx] < toalt - 10. * ft:

            # Turn off descent switch for speed schedule
            bs.traf.swdescent[idx] = False

            # Altitude we want to climb to: next alt constraint in our route (could be further down the route)
            bs.traf.actwp.nextaltco[idx] = toalt   # [m]
            bs.traf.actwp.xtoalt[idx]    = xtoalt  # [m] distance to next alt constraint measured from next waypoint
            self.alt[idx]          = bs.traf.actwp.nextaltco[idx]  # dial in altitude of next waypoint as calculated
            self.dist2vs[idx]      = 99999.*nm #[m] Forces immediate climb as current distance to next wp will be less

            # Flat earth distance to next wp
            dy = (bs.traf.actwp.lat[idx] - bs.traf.lat[idx])
            dx = (bs.traf.actwp.lon[idx] - bs.traf.lon[idx]) * bs.traf.coslat[idx]
            legdist = 60. * nm * np.sqrt(dx * dx + dy * dy) # [m]
            t2go = max(0.1, legdist+xtoalt) / max(0.01, bs.traf.gs[idx])
            bs.traf.actwp.vs[idx]  = np.maximum(self.steepness*bs.traf.gs[idx], \
                            (bs.traf.actwp.nextaltco[idx] - bs.traf.alt[idx])/ t2go) # [m/s]
            if self.EEI_ROC[idx] != False and self.EEI_ROC[idx] != 0:
                bs.traf.actwp.vs[idx] = np.where(self.TOsw[idx], self.EEI_ROC[idx], bs.traf.actwp.vs[idx])
        else:
            self.dist2vs[idx] = -999. # [m]


        return

    def descentpath(self, idx):
        '''
        Function: Calculate the descent path of an aircraft to determine the top of descent.
        Ordinary waypoint: waypoint without altitude constraint
        Restricted waypoint: waypoint with an altitude constraint ( AT, AT/BELOW, AT/ABOVE)
        Created by: Winand Mathoera
        Date: 12/10/2022
        '''



        # Altitude segments and corresponding gamma angles
        concas = -1
        if self.spddismiss[idx]: concas = bs.traf.selspd[idx]

        ds = Descent(idx, bs.traf.alt[idx], bs.traf.tas[idx], concas)

        r = self.route[idx]

        ilast = len(r.wpalt) - 1    # index of last waypoint
        icurr = r.iactwp            # index of active waypoint

        # print('My active wpt is: ', r.wpname[icurr])

        # indexes of altitude constrained waypoints
        ialtconst = [index for index,i in enumerate(r.wpalt) if i > -999 and index >= icurr]

        # Last waypoint altitude; destination = 0
        altlast = 0
        cont = False
        prevgeo = False
        extra_dist = 0
        wpalt_correction = 0

        for i in reversed(ialtconst):

            if i >= ilast: continue # failsafe

            self.route[idx].wptoalt[i] = altlast  # set toalt at WPT

            for j in range(i+1, ilast):
                self.route[idx].wptoalt[j] = 0    # clear toalts from any intermediate WPTs

            altconst = r.wpalt[i]  # altitude constraint of given waypoint

            # Depending on the altitude restriction, approve predicted altitude or restrict to constraint
            if r.wpaltres[i] == 'AT' or r.wpaltres[i] == '':
                altlast = altconst
                cont = False
            else:
                # distance from given altres waypoint to next altres waypoint
                wpdist = sum([latlondist(r.wplat[k], r.wplon[k], r.wplat[k + 1], r.wplon[k + 1]) for k in
                 range(i, ilast)]) - extra_dist

                interlatlon = []    # create intermediate points for wind calculations
                wpqdr = []          # complementary bearings/distances

                for k in range(i, ilast):
                    latlon, qdr = self.interlatlon(r.wplat[k], r.wplon[k], r.wplat[k + 1], r.wplon[k + 1])
                    interlatlon += latlon
                    wpqdr += qdr

                wpqdr = np.array(wpqdr)
                interlatlon = np.array(interlatlon)

                # predicted altitude needed to travel between the two waypoints
                alt_req, extra_dist, wpalt_correction = self.descentaltitude(idx, altlast, ds, self.spddismiss[idx] ,wpdist, wpqdr, interlatlon)

                if r.wpaltres[i] == 'B':
                    if alt_req <= altconst:
                        altlast = alt_req
                        cont = True
                    else:
                        altlast = altconst
                        cont = False

                elif r.wpaltres[i] == 'A':
                    if alt_req >= altconst:
                        altlast = alt_req
                        cont = True
                    else:
                        altlast = altconst
                        cont = False

            prevgeo = r.wpgeo[i]

            ilast = i   # set latest altitude constraint waypoint as start point for new loop


        """Aircraft find top of descent distance to next ordinary waypoint"""
        # print('current')

        # Skip calculations if continuous descent is possible
        if self.prevconst[idx]:
            self.dist2vs[idx] = 99999. * nm  # descent now
            self.dist2vscount[idx] = 0
            self.dist2vscountpassed[idx] = True
            bs.traf.actwp.tempaltconst[idx] = True  # Do not reset alt constraint when passing ordinary waypoints
            self.geodescent[idx] = False
            bs.traf.actwp.nextaltco[idx] = altlast - wpalt_correction
            # print('next altco', (altlast-wpalt_correction) / 0.3048)
            # Remember if a/c can fly continuous descent after next waypoint
            self.prevconst[idx] = cont
            self.prevwptgeo[idx] = prevgeo
            # print('Houd vorig pad aan!')
            return

        # Remember if a/c can fly continuous descent after next waypoint
        self.prevconst[idx] = cont

        # Distance from next ordinary waypoint to first restricted waypoint
        wpdist_list = [latlondist(r.wplat[k], r.wplon[k], r.wplat[k + 1], r.wplon[k + 1]) for k in
                      range(icurr, ilast)]
        wpdist = sum(wpdist_list)

        interlatlon = []
        wpqdr = []

        for k in range(icurr, ilast):
            latlon, qdr = self.interlatlon(r.wplat[k], r.wplon[k], r.wplat[k + 1], r.wplon[k + 1])
            interlatlon += latlon
            wpqdr += qdr

        ac_latlon, ac_qdr = self.interlatlon(bs.traf.lat[idx], bs.traf.lon[idx], r.wplat[icurr], r.wplon[icurr])

        latlon = list(ac_latlon)
        latlon += interlatlon
        ac_qdr += wpqdr

        wpqdr = np.array(ac_qdr)
        interlatlon = np.array(latlon)

        # Distance from aircraft to next ordinary waypoint
        ac_wptdist = latlondist(bs.traf.lat[idx], bs.traf.lon[idx], r.wplat[icurr], r.wplon[icurr])

        # Distance from a/c to first restricted waypoint
        ac_dist = wpdist + ac_wptdist

        alti = int(bs.traf.alt[idx] / ft / 100 - 1)

        vsaxalt, vsaxdist = self.verticalax( ds.rod[alti], ds.tasspeeds[alti])#ds.speed[alti])
        # print('vsax', vsaxalt, vsaxdist)


        # Predicted distance needed to reach altitude of restricted waypoint
        descent_distance = self.descentdistance(idx, altlast, bs.traf.alt[idx] - vsaxalt, wpqdr, ds, self.spddismiss[idx], interlatlon, r.wpspd[ilast]) + vsaxdist + extra_dist

        # print('Altitude to reach', round(altlast/0.3048/100,2))
        # print('Distance needed', round(descent_distance/nm,2), round(ac_dist/nm,2))


        # If required descent distance is greater than available, use geo descent
        if descent_distance > ac_dist or (not self.prevconst[idx] and self.prevwptgeo[idx]):
            self.dist2vs[idx] = 99999.*nm   # descent now
            self.geodescent[idx] = True            # Geometric descent, with following steepness
            self.steepnessv2[idx] = (bs.traf.alt[idx]-altlast) / ac_dist
            self.dist2vscount[idx] = 0
            self.dist2vscountpassed[idx] = False

        else:
            # Other wise find distance to top of descent
            dist2vs = descent_distance - wpdist
            dist2vscount = 0

            bs.traf.actwp.tempaltconst[idx] = True  # Do not reset alt constraint when passing ordinary waypoints

            # Count the number of ordinary waypoints before the top of descent occurs
            for k in wpdist_list:
                if dist2vs >= 0: break
                dist2vs += k
                dist2vscount += 1

            self.dist2vs[idx] = dist2vs # bs.traf.actwp.turndist[idx] +  turndistance nakijken
            self.dist2vscount[idx] = dist2vscount
            self.geodescent[idx] = False
            self.dist2vscountpassed[idx] = True

        bs.traf.actwp.nextaltco[idx] = altlast - wpalt_correction

        # if self.geodescent[idx]: print('GEO on')

        self.prevwptgeo[idx] = prevgeo

        return

    def descentaltitude(self, idx, altlast, ds, spddismiss, wpdist, qdrdist, latlon):
        # calculate altitude reached within given distance using nominal descent rates (gammaTAS)

        # print('Altitude from:', altlast/0.3048, wpdist/1852)


        dsegmi = 0  # Index of decel. segment altitudes

        # Remove decel. segments outside current altitude region
        for i in ds.decel_altspd:
            if i[0]<altlast: dsegmi += 1

        # info of intermediate WPTs
        lat, lon = zip(*latlon)
        bearing, wpdist_sep = zip(*qdrdist)

        step = 0   # steps for intermediate WPTs

        # Update gammatas for new bearing/wind
        step, cutoff, windbearing, gammatas = self.gammatas_update(step, wpdist_sep, lat, lon, altlast, bearing, ds.rod,
                                                                 ds.tasspeeds_func(bs.traf.M[idx], bs.traf.alt[idx]))

        start_break = len(gammatas)

        start = ceil(altlast / (100 * ft))  # index in gammatas
        start_rem = (100 * ft) - altlast % (100 * ft)  # remainder in start - 1

        dist = (start_rem) / gammatas[start - 1]
        alt = start_rem + altlast

        dsegmi, dist = self.add_decelsegm(idx, dsegmi, dist, ds, alt, gammatas, spddismiss, windbearing)

        if dist > wpdist:
            return wpdist * gammatas[start - 1], 0, 0 # Altitude for close wpt

        if dist > cutoff:
            step, cutoff, windbearing, gammatas = self.gammatas_update(step, wpdist_sep, lat, lon, alt, bearing,
                                                                     ds.rod, ds.tasspeeds_func(bs.traf.M[idx], bs.traf.alt[idx]))

        while dist < wpdist:
            add_dist = (100 * ft) / gammatas[start]

            if dist + add_dist > wpdist:
                add_alt = (wpdist - dist) * gammatas[start]
                alt += add_alt
                dist += add_dist

                #todo if decel alts do geo
                # dsegmi, dist = self.add_decelsegm(idx, dsegmi, dist, ds, alt, gammatas, spddismiss, windbearing)
                # if dist > wpdist: return alt + abs(ds.added_alt), (dist-wpdist), -abs(ds.added_alt)

                # print('return 1', wpdist/1852, dist/1852, add_dist/1852, add_alt/0.3048, alt/0.3048)
                return alt, 0, 0

            dist += add_dist
            alt += 100 * ft
            start += 1

            if dist > cutoff:
                step, cutoff, windbearing, gammatas = self.gammatas_update(step, wpdist_sep, lat, lon, alt, bearing,
                                                                         ds.rod, ds.tasspeeds_func(bs.traf.M[idx], bs.traf.alt[idx]))

            old_dist = dist * 1.
            dsegmi, dist = self.add_decelsegm(idx, dsegmi, dist, ds, alt, gammatas, spddismiss, windbearing)

            # If you are higher than aircraft altitude, take altitude to aircraft
            if start >= start_break:
                # print('return 3')
                return bs.traf.alt[idx] - altlast, 0, 0

        wpalt_correction = (1-(wpdist-old_dist)/(dist-old_dist))*abs(ds.added_alt)

        # print('corr', wpdist, old_dist, dist, ds.added_alt, alt)
        #
        # print('return 2', dist, wpdist)
        return alt, (dist-wpdist), wpalt_correction

    def gammatas_update(self, step, wpdist_sep, lat, lon, altlast, bearing, rod, tas):
        step -= 1
        cutoff = sum(wpdist_sep[step:]) * nm
        wind = bs.traf.wind.getnewdata(lat[step], lon[step], altlast)
        windbearing = wind[0] * np.cos(np.radians(bearing[step])) + wind[1] * np.sin(np.radians(bearing[step]))
        gammatas = abs(rod / (tas + windbearing))
        return step, cutoff, windbearing, gammatas


    def interlatlon(self, lat1, lon1, lat2, lon2):
        bearing, dist = qdrdist(lat1, lon1, lat2, lon2)
        sep = ceil(dist/1)
        coords = list(zip(np.linspace(lat1, lat2, sep + 1), np.linspace(lon1, lon2, sep + 1)))
        wpqdr = [qdrdist(coords[k][0], coords[k][1], coords[k+1][0], coords[k+1][1]) for k in range(sep)]
        return coords, wpqdr


    # def gammatas_wind(self, rod, tas, qdrdist, wind, ):
    #     vnorth, veast = wind
    #     gamma = np.array([ abs(rod / (tas + vnorth*np.cos(np.radians(bearing)) + veast*np.sin(np.radians(bearing)))) for
    #                        bearing, dist in qdrdist])
    #     # gamma1 = np.array([abs(rod / (tas)) for bearing, dist in qdrdist])
    #     return gamma
    #
    # def gammatas_windv2(self, idx, rod, tas, bearing, dist, wind, ):
    #     gamma = abs(rod / (tas + wind))
    #     return gamma

    def descentdistance(self, idx, altlast, altconst, qdrdist, ds, spddismiss, latlon, wpspd):
        # calculate distance needed to travel between two different altitudes using nominal descent rates (gammaTAS)


        dsegmi = 0  # Index of decel. segment altitudes

        # Remove decel. segments outside current altitude region
        for i in ds.decel_altspd:
            # print(1, i[0], altlast, dsegmi)
            if i[0] < altlast: dsegmi += 1

        # info of intermediate WPTs
        lat, lon = zip(*latlon)
        bearing, wpdist_sep = zip(*qdrdist)

        step = 0    # steps for intermediate WPTs

        step, cutoff, windbearing, gammatas = self.gammatas_update(step, wpdist_sep, lat, lon, altlast, bearing,
                                                                   ds.rod, ds.tasspeeds_func(bs.traf.M[idx], bs.traf.alt[idx]))


        # print(1, list(zip( np.round(ds.segments/0.3048/100,2), np.round(np.degrees(np.arctan(gammatas)),2),  np.round(  vtas2cas(ds.tasspeeds_func(vmach2cas(bs.traf.M[idx], bs.traf.alt[idx])), ds.segments  )/0.514444,2)  )))



        start = ceil(altlast / (100 * ft)) # index in gammatas
        start_rem = (100 * ft) - altlast % (100 * ft) # remainder in start - 1

        dist = 0

        if wpspd >-999:
            if dsegmi >= len(ds.decel_altspd):
                if ds.decel_altspd[-1][2] > wpspd:
                    dist_add, alt_trash = ds.decelsegment(idx, altlast, wpspd, ds.decel_altspd[-1][2] , gammatas, windbearing)
                    dist += dist_add
            else:
                if ds.decel_altspd[dsegmi][1] > wpspd:
                    dist_add, alt_trash = ds.decelsegment(idx, altlast, wpspd, ds.decel_altspd[dsegmi][1], gammatas, windbearing)
                    dist += dist_add

        added_dist = (start_rem) / gammatas[start - 1]
        dist += added_dist
        alt = start_rem * 1. + altlast

        dsegmi, dist = self.add_decelsegm(idx, dsegmi, dist, ds, alt, gammatas, spddismiss, windbearing, added_dist)

        end = floor(altconst / (100 * ft)) # index in gamma tas
        end_rem = altconst % (100 * ft) # remainder in end + 0

        for i in range(start, end):
            added_dist = (100 * ft) / gammatas[i]
            dist += added_dist
            alt += 100 * ft

            if dist > cutoff and abs(step) < len(bearing):
                step, cutoff, windbearing, gammatas = self.gammatas_update(step, wpdist_sep, lat, lon, altlast, bearing,
                                                                           ds.rod, ds.tasspeeds_func(bs.traf.M[idx], bs.traf.alt[idx]))

            dsegmi, dist = self.add_decelsegm(idx, dsegmi, dist, ds, alt, gammatas, spddismiss, windbearing, added_dist)

        if end>start:
            step = 1
            step, cutoff, windbearing, gammatas = self.gammatas_update(step, wpdist_sep, lat, lon, altlast, bearing,
                                                                       ds.rod, ds.tasspeeds_func(bs.traf.M[idx], bs.traf.alt[idx]))
            dist += (end_rem) / gammatas[end]
            alt += end_rem

        return dist

    def add_decelsegm(self, idx, dsegmi, dist, ds, alt, gammatas, spddismiss, wind, added_dist = 0):
        if dsegmi < len(ds.decel_altspd):
            if alt > ds.decel_altspd[dsegmi][0] and not spddismiss and vmach2cas(bs.traf.M[idx], bs.traf.alt[idx])>=ds.decel_altspd[dsegmi][2]:
                # Should have crossed transition level, and not flying slower than CAS schedule speed
                d_alt, d_v0, d_v1 = ds.decel_altspd[dsegmi]
                dsegm_dist, dsegm_alt = ds.decelsegment(idx, d_alt, d_v0, d_v1, gammatas, wind)
                dist += dsegm_dist - added_dist*(ds.decel_altspd[dsegmi][0]-(alt-100*ft))/(100*ft)
                dsegmi += 1
        return dsegmi, dist

    def verticalax(self, rod, spd, ax = 300 * fpm):
        alt = (0 + rod)/2 * rod/ax
        dist = spd * abs(rod)/ax
        return alt, dist

    def speedschedule(self):
        '''
        Function: Calculate the speeds corresponding to the speed schedule of BADA manual 3.10
        For either jet/turboprop or piston aircraft
        Only for descent currently!

        Created by: Winand Mathoera
        Date: 26/09/2022
        '''

        kts = 0.5144
        alt = bs.traf.alt / 0.3048

        # Correction for minimum landing speed
        corr = np.sqrt(bs.traf.perf.mass / bs.traf.perf.mref)

        # Calculate the speeds for each altitude segment based on either
        # the minimum landing speed or the standard descent speed
        l1 = corr * bs.traf.perf.vmld/kts + 5
        l2 = corr * bs.traf.perf.vmld/kts + 10
        l3 = corr * bs.traf.perf.vmld/kts + 20
        l4 = corr * bs.traf.perf.vmld/kts + 50
        l5 = np.where(bs.traf.perf.casdes / kts <= 220, bs.traf.perf.casdes / kts, 220)
        l6 = np.where(bs.traf.perf.casdes2 / kts <= 250, bs.traf.perf.casdes2 / kts, 250)
        l7 = 280
        l8 = np.where(bs.traf.perf.mmax>7000, 0.78, 0.82)

        # l7 = bs.traf.perf.casdes2/kts
        # l8 = bs.traf.perf.mades

        # Piston aircraft speeds
        l9 = corr * bs.traf.perf.vmld / kts + 0
        l10 = corr * bs.traf.perf.vmld / kts + 0
        l11 = corr * bs.traf.perf.vmld / kts + 0
        l12 = bs.traf.perf.casdes
        l13 = bs.traf.perf.casdes2
        l14 = bs.traf.perf.mades

        # Find the segment of each aircraft and obtain correct speed for that segment
        spds = np.where(alt<=999, 1, 0) * l1 * kts + \
               np.logical_and(alt > 999, alt <= 1499) * l2 * kts + \
               np.logical_and(alt > 1499, alt <= 1999) * l3 * kts + \
               np.logical_and(alt > 1999, alt <= 2999) * l4 * kts + \
               np.logical_and(alt > 2999, alt <= 5999) * l5 * kts + \
               np.logical_and(alt > 5999, alt <= 9999) * l6 * kts + \
               np.logical_and(alt > 9999, alt <= 26000) * l7 * kts + \
               np.where(alt>26000, 1, 0) * l8

        # spds = np.where(alt<=999, 1, 0) * l1 * kts + \
        #        np.logical_and(alt > 999, alt <= 1499) * l2 * kts + \
        #        np.logical_and(alt > 1499, alt <= 1999) * l3 * kts + \
        #        np.logical_and(alt > 1999, alt <= 2999) * l4 * kts + \
        #        np.logical_and(alt > 2999, alt <= 5999) * l5 * kts + \
        #        np.logical_and(alt > 5999, alt <= 9999) * l6 * kts + \
        #        np.logical_and(alt > 9999, alt <= bs.traf.perf.hpdes/0.3048) * l7 * kts + \
        #        np.where(alt>bs.traf.perf.hpdes/0.3048, 1, 0) * l8

        # Segments for piston aircraft
        spds_p = np.where(alt <= 499, 1, 0) * l9 *kts + \
                 np.logical_and(alt > 499, alt <= 999) * l10 * kts + \
                 np.logical_and(alt > 999, alt <= 1499) * l11 * kts + \
                 np.logical_and(alt > 1499, alt <= 9999) * l12 * kts + \
                 np.logical_and(alt > 9999, alt <= bs.traf.perf.hpdes/0.3048) * l13 * kts + \
                 np.where(alt > bs.traf.perf.hpdes / 0.3048, 1, 0) * l14

        self.spds = np.where(bs.traf.perf.piston == 1, spds_p, spds)

        # print('spds', self.spds, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, bs.traf.perf.piston)

        # l1 = corr * bs.traf.perf.vmto / kts + 5
        # l2 = corr * bs.traf.perf.vmto / kts + 10
        # l3 = corr * bs.traf.perf.vmto / kts + 30
        # l4 = corr * bs.traf.perf.vmto / kts + 60
        # l5 = corr * bs.traf.perf.vmto / kts + 80
        # l6 = np.where(bs.traf.perf.vcl1 / kts <= 250, bs.traf.perf.vcl1, 250)
        # l7 = bs.traf.perf.vcl2 / kts
        # l8 = bs.traf.perf.Mcl
        #
        # # Find the segment of each aircraft and obtain correct speed for that segment
        # spds = np.where(alt <= 1499, 1, 0) * l1 * kts + \
        #        np.logical_and(alt > 1499, alt <= 2999) * l2 * kts + \
        #        np.logical_and(alt > 2999, alt <= 3999) * l3 * kts + \
        #        np.logical_and(alt > 3999, alt <= 4999) * l4 * kts + \
        #        np.logical_and(alt > 4999, alt <= 5999) * l5 * kts + \
        #        np.logical_and(alt > 5999, alt <= 9999) * l6 * kts + \
        #        np.logical_and(alt > 9999, alt <= bs.traf.perf.hpdes / 0.3048) * l7 * kts + \
        #        np.where(alt > bs.traf.perf.hpdes / 0.3048, 1, 0) * l8

    def setspeedforRTA(self, idx, torta, xtorta):
        #debug print("setspeedforRTA called, torta,xtorta =",torta,xtorta/nm)

        # Calculate required CAS to meet RTA
        # for aircraft nr. idx (scalar)
        if torta < -90. : # -999 signals there is no RTA defined in remainder of route
            return False

        deltime = torta-bs.sim.simt # Remaining time to next RTA [s] in simtime
        if deltime>0: # Still possible?
            gsrta = calcvrta(bs.traf.gs[idx], xtorta,
                             deltime, bs.traf.perf.axmax[idx])

            # Subtract tail wind speed vector
            tailwind = (bs.traf.windnorth[idx]*bs.traf.gsnorth[idx] + bs.traf.windeast[idx]*bs.traf.gseast[idx]) / \
                        bs.traf.gs[idx]

            # Convert to CAS
            rtacas = tas2cas(gsrta-tailwind,bs.traf.alt[idx])

            # Performance limits on speed will be applied in traf.update
            if bs.traf.actwp.spdcon[idx]<0. and bs.traf.swvnavspd[idx]:
                bs.traf.actwp.spd[idx] = rtacas
                #print("setspeedforRTA: xtorta =",xtorta)

            return rtacas
        else:
            return False

    @stack.command(name='ALT')
    def selaltcmd(self, idx: 'acid', alt: 'alt', vspd: 'vspd' = None):
        """ ALT acid, alt, [vspd]

            Select autopilot altitude command."""
        bs.traf.selalt[idx] = alt
        bs.traf.swvnav[idx] = False

        # Check for optional VS argument
        if vspd:
            bs.traf.selvs[idx] = vspd
        else:
            if not isinstance(idx, Collection):
                idx = np.array([idx])
            delalt = alt - bs.traf.alt[idx]
            # Check for VS with opposite sign => use default vs
            # by setting autopilot vs to zero
            oppositevs = np.logical_and(bs.traf.selvs[idx] * delalt < 0., abs(bs.traf.selvs[idx]) > 0.01)
            bs.traf.selvs[idx[oppositevs]] = 0.
            if delalt < 0:
                self.vs[idx] = -999
                bs.traf.selvs[idx] = -999

    # @stack.command(name='ALT')
    # def selaltcmd(self, idx: 'acid', alt: 'alt', vspd: 'vspd' = None):
    #     """ ALT acid, alt, [vspd]
    #
    #         Select autopilot altitude command."""
    #     bs.traf.selalt[idx] = alt
    #     if bs.traf.swvnav[idx]: self.altdismiss[idx] = True
    #     if not self.dpswitch[idx]: self.dpswitch[idx] = True
    #     bs.traf.swvnav[idx] = False
    #
    #
    #     # Check for optional VS argument
    #     if vspd:
    #         bs.traf.selvs[idx] = vspd
    #     else:
    #         if not isinstance(idx, Collection):
    #             idx = np.array([idx])
    #         delalt = alt - bs.traf.alt[idx]
    #         # Check for VS with opposite sign => use default vs
    #         # by setting autopilot vs to zero
    #         oppositevs = np.logical_and(bs.traf.selvs[idx] * delalt < 0., abs(bs.traf.selvs[idx]) > 0.01)
    #         bs.traf.selvs[idx[oppositevs]] = 0.
    #
    # @stack.command(name='FORCEALT')
    # def selaltcmd(self, idx: 'acid', alt: 'alt', vspd: 'vspd' = None):
    #     """ ALT acid, alt, [vspd]
    #
    #         Select autopilot altitude command."""
    #     bs.traf.selalt[idx] = alt
    #     if bs.traf.swvnav[idx]: self.faltdismiss[idx] = True
    #     if not self.dpswitch[idx]: self.dpswitch[idx] = True
    #     bs.traf.swvnav[idx] = False
    #
    #     # Check for optional VS argument
    #     if vspd:
    #         bs.traf.selvs[idx] = vspd
    #     else:
    #         if not isinstance(idx, Collection):
    #             idx = np.array([idx])
    #         delalt = alt - bs.traf.alt[idx]
    #         # Check for VS with opposite sign => use default vs
    #         # by setting autopilot vs to zero
    #         oppositevs = np.logical_and(bs.traf.selvs[idx] * delalt < 0., abs(bs.traf.selvs[idx]) > 0.01)
    #         bs.traf.selvs[idx[oppositevs]] = 0.
    #         if delalt<0:
    #             self.vs[idx] = -999
    #             bs.traf.selvs[idx] = -999

    @stack.command(name='TO')
    def TOcmd(self, idx: 'acid', SID = None):
        """ TO acid

            Select autopilot altitude command."""
        self.TOsw[idx] = True
        bs.traf.swvnav[idx] = False
        id = bs.traf.id[idx]
        AC_type = bs.traf.type[idx]

        self.TOdf[idx], self.TO_slope[idx] = self.EEI.select(id, AC_type, airline=id[:3])
        if SID != None:
            string = "WILABADA/SID/"+SID
            # string = "LVNL/Routes/SID/"+SID
            pcall(string, id)

    @stack.command(name='TOD', annotations = "acid,SID,txt")
    def TODcmd(self, idx: 'acid', SID: 'SID', dest: 'dest'):
        """ TO acid

            Select autopilot altitude command."""

        self.TOsw[idx] = True
        bs.traf.swvnav[idx] = False
        id = bs.traf.id[idx]
        AC_type = bs.traf.type[idx]

        self.setdest(acidx = idx, wpname = dest)

        self.TOdf[idx], self.TO_slope[idx] = self.EEI.select(id, AC_type, airline = id[:3], dest = dest)
        print(idx, SID)
        if SID != None:
            # string = "WILABADA/SID/" + SID
            string = "LVNL/PLRH/SID/" + SID
            pcall(string, id)
            bs.traf.lvnlvars.sid[idx] = SID.upper()
            bs.traf.lvnlvars.flighttype[idx] = 'OUTBOUND'
            bs.traf.lvnlvars.symbol[idx] = 'TWROUT'

    @stack.command(name='VS')
    def selvspdcmd(self, idx: 'acid', vspd:'vspd'):
        """ VS acid,vspd (ft/min)
            Vertical speed command (autopilot) """
        bs.traf.selvs[idx] = vspd #[fpm]
        # bs.traf.vs[idx] = vspd
        bs.traf.swvnav[idx] = False
        self.TOsw[idx] = False

    @stack.command(name='PHASE', annotations='acid,int')
    def selphasecmd(self, idx: 'acid', phase: 'int'):
        bs.traf.selphase[idx] = phase

    @stack.command(name='RESUME', annotations='acid')
    def resumecmd(self, idx: 'acid'):
        # Forget heading command
        if self.hdgdismiss[idx]:
            bs.traf.swlnav[idx] = True
            # Only recalculate descentpath if not currently descending
            if not self.altdismiss[idx]:
                bs.traf.swvnav[idx] = True
                self.setVNAV(idx, True)
            self.hdgdismiss[idx] = False

        # Forget speed command
        if self.spddismiss[idx]:
            bs.traf.swvnavspd[idx] = True
            self.spddismiss[idx] = False

        # Forget forced altitude command
        if self.faltdismiss[idx]:
            bs.traf.swvnav[idx] = True
            self.setVNAV(idx, True)
            self.altdismiss[idx] = False


    @stack.command(name='DESCENT', annotations='acid,onoff')
    def setdescent(self, idx: 'acid', flag: 'onoff' = None):

        if not isinstance(idx, Collection):
            if idx is None:
                # All aircraft are targeted
                bs.traf.swdescent = np.array(bs.traf.ntraf * [flag])
            else:
                # Prepare for the loop
                idx = np.array([idx])

        output = []
        for i in idx:
            if flag is None:
                output.append(bs.traf.id[i] + ": DESCENT is " + ("ON" if bs.traf.swdescent[i] else "OFF"))
            else:
                bs.traf.swdescent[i] = flag
        if flag is None:
            return True, '\n'.join(output)

    @stack.command(name='HDG', aliases=("HEADING", "TURN"))
    def selhdgcmd(self, idx: 'acid', hdg: 'hdg'):  # HDG command
        """ HDG acid,hdg (deg,True or Magnetic)
            Autopilot select heading command. """
        if hdg.upper() in bs.navdb.wpid:
            index = bs.navdb.wpid.index(hdg.upper())
            templat_hdg = bs.navdb.wplat[index]
            templon_hdg = bs.navdb.wplon[index]
            templat_ac = bs.traf.lat[idx]
            templon_ac = bs.traf.lon[idx]

            hdg = angleFromCoordinate(templat_ac, templon_ac, templat_hdg, templon_hdg) % 360.0
        else:
            hdg = float(hdg) % 360.0

        if not isinstance(idx, Collection):
            idx = np.array([idx])
        if not isinstance(hdg, Collection):
            hdg = np.array([hdg])
        # If there is wind, compute the corresponding track angle
        if bs.traf.wind.winddim > 0:
            ab50 = bs.traf.alt[idx] > 50.0 * ft
            bel50 = np.logical_not(ab50)
            iab = idx[ab50]
            ibel = idx[bel50]

            tasnorth = bs.traf.tas[iab] * np.cos(np.radians(hdg[ab50]))
            taseast = bs.traf.tas[iab] * np.sin(np.radians(hdg[ab50]))
            vnwnd, vewnd = bs.traf.wind.getdata(bs.traf.lat[iab], bs.traf.lon[iab], bs.traf.alt[iab])
            gsnorth = tasnorth + vnwnd
            gseast = taseast + vewnd
            self.trk[iab] = np.degrees(np.arctan2(gseast, gsnorth))%360.
            self.trk[ibel] = hdg
        else:
            self.trk[idx] = hdg
        bs.traf.selhdg[idx] = hdg
        if bs.traf.swlnav[idx]: self.hdgdismiss[idx] = True # to later turn back on swlnav
        bs.traf.swlnav[idx] = False
        if not self.dpswitch[idx]: self.dpswitch[idx] = True # makes sure to recalculate descentpath
        # Everything went ok!

        bs.traf.selalt[idx] = bs.traf.alt[idx]

        return True

    @stack.command(name='SPD', aliases=("SPEED",))
    def selspdcmd(self, idx: 'acid', casmach: 'spd'):  # SPD command
        """ SPD acid, casmach (= CASkts/Mach)

            Select autopilot speed. """
        # Depending on or position relative to crossover altitude,
        # we will maintain CAS or Mach when altitude changes
        # We will convert values when needed
        bs.traf.selspd[idx] = casmach

        # Used to be: Switch off VNAV: SPD command overrides
        if bs.traf.swvnavspd[idx]: self.spddismiss[idx] = True  # to later turn back on swvnavspd
        bs.traf.swvnavspd[idx]   = False
        if not self.dpswitch[idx]:
            self.descentpath(idx)   # recalculate descentpath if it has been calculated already

        return True

    @stack.command(name='DEST')
    def setdest(self, acidx: 'acid', wpname:'wpt' = None):
        ''' DEST acid, latlon/airport

            Set destination of aircraft, aircraft wil fly to this airport. '''
        if wpname is None:
            return True, 'DEST ' + bs.traf.id[acidx] + ': ' + self.dest[acidx]
        route = self.route[acidx]
        apidx = bs.navdb.getaptidx(wpname)
        if apidx < 0:
            if bs.traf.ap.route[acidx].nwp > 0:
                reflat = bs.traf.ap.route[acidx].wplat[-1]
                reflon = bs.traf.ap.route[acidx].wplon[-1]
            else:
                reflat = bs.traf.lat[acidx]
                reflon = bs.traf.lon[acidx]

            success, posobj = txt2pos(wpname, reflat, reflon)
            if success:
                lat = posobj.lat
                lon = posobj.lon
            else:
                return False, "DEST: Position " + wpname + " not found."

        else:
            lat = bs.navdb.aptlat[apidx]
            lon = bs.navdb.aptlon[apidx]

        self.dest[acidx] = wpname
        # iwp = route.addwpt(acidx, self.dest[acidx], route.dest,
        #                    lat, lon, 0.0, bs.traf.cas[acidx])

        # ADDED
        iwp = route.addwpt(acidx, self.dest[acidx], route.dest,
                           lat, lon, 0.0, 0.0)

        # If only waypoint: activate
        if (iwp == 0) or (self.orig[acidx] != "" and route.nwp == 2):
            bs.traf.actwp.lat[acidx] = route.wplat[iwp]
            bs.traf.actwp.lon[acidx] = route.wplon[iwp]
            bs.traf.actwp.nextaltco[acidx] = route.wpalt[iwp]
            bs.traf.actwp.spd[acidx] = route.wpspd[iwp]

            bs.traf.swlnav[acidx] = True
            bs.traf.swvnav[acidx] = True
            route.iactwp = iwp
            route.direct(acidx, route.wpname[iwp])

        # If not found, say so
        elif iwp < 0:
            return False, ('DEST'+self.dest[acidx] + " not found.")

    @stack.command(name='ORIG')
    def setorig(self, acidx: 'acid', wpname: 'wpt' = None):
        ''' ORIG acid, latlon/airport

            Set origin of aircraft. '''
        if wpname is None:
            return True, 'ORIG ' + bs.traf.id[acidx] + ': ' + self.orig[acidx]
        route = self.route[acidx]
        apidx = bs.navdb.getaptidx(wpname)
        if apidx < 0:
            if bs.traf.ap.route[acidx].nwp > 0:
                reflat = bs.traf.ap.route[acidx].wplat[-1]
                reflon = bs.traf.ap.route[acidx].wplon[-1]
            else:
                reflat = bs.traf.lat[acidx]
                reflon = bs.traf.lon[acidx]

            success, posobj = txt2pos(wpname, reflat, reflon)
            if success:
                lat = posobj.lat
                lon = posobj.lon
            else:
                return False, ("ORIG: Position " + wpname + " not found.")

        else:
            lat = bs.navdb.aptlat[apidx]
            lon = bs.navdb.aptlon[apidx]

        # Origin: bookkeeping only for now, store in route as origin
        self.orig[acidx] = wpname
        iwp = route.addwpt(acidx, self.orig[acidx], route.orig,
                           lat, lon, 0.0, bs.traf.cas[acidx])
        if iwp < 0:
            return False, (self.orig[acidx] + " not found.")

    @stack.command(name='LNAV')
    def setLNAV(self, idx: 'acid', flag: 'onoff' = None):
        """ LNAV acid,[ON/OFF]
        
            LNAV (lateral FMS mode) switch for autopilot """
        if not isinstance(idx, Collection):
            if idx is None:
                # All aircraft are targeted
                bs.traf.swlnav = np.array(bs.traf.ntraf * [flag])
            else:
                # Prepare for the loop
                idx = np.array([idx])

        # Set LNAV for all aircraft in idx array
        output = []
        for i in idx:
            if flag is None:
                output.append(bs.traf.id[i] + ": LNAV is " + ("ON" if bs.traf.swlnav[i] else "OFF"))

            elif flag:
                route = self.route[i]
                if route.nwp <= 0:
                    return False, ("LNAV " + bs.traf.id[i] + ": no waypoints or destination specified")
                elif not bs.traf.swlnav[i]:
                   bs.traf.swlnav[i] = True
                   route.direct(i, route.wpname[route.findact(i)])
            else:
                bs.traf.swlnav[i] = False
        if flag is None:
            return True, '\n'.join(output)

    @stack.command(name='VNAV')
    def setVNAV(self, idx: 'acid', flag: 'onoff' = None):
        """ VNAV acid,[ON/OFF]
        
            Switch on/off VNAV mode, the vertical FMS mode (autopilot) """
        if not isinstance(idx, Collection):
            if idx is None:
                # All aircraft are targeted
                bs.traf.swvnav    = np.array(bs.traf.ntraf * [flag])
                bs.traf.swvnavspd = np.array(bs.traf.ntraf * [flag])
            else:
                # Prepare for the loop
                idx = np.array([idx])

        # Set VNAV for all aircraft in idx array
        output = []
        for i in idx:
            if flag is None:
                msg = bs.traf.id[i] + ": VNAV is " + "ON" if bs.traf.swvnav[i] else "OFF"
                if not bs.traf.swvnavspd[i]:
                    msg += " but VNAVSPD is OFF"
                output.append(bs.traf.id[i] + ": VNAV is " + "ON" if bs.traf.swvnav[i] else "OFF")

            elif flag:
                if not bs.traf.swlnav[i]:
                    return False, (bs.traf.id[i] + ": VNAV ON requires LNAV to be ON")

                route = self.route[i]
                if route.nwp > 0:
                    bs.traf.swvnav[i]    = True
                    bs.traf.swvnavspd[i] = True
                    self.route[i].calcfp()
                    actwpidx = self.route[i].iactwp
                    self.ComputeVNAV(i,self.route[i].wptoalt[actwpidx],self.route[i].wpxtoalt[actwpidx],\
                                     self.route[i].wptorta[actwpidx],self.route[i].wpxtorta[actwpidx])
                    # REMOVED ?                    #bs.traf.actwp.nextaltco[i] = self.route[i].wptoalt[actwpidx]

                else:
                    return False, ("VNAV " + bs.traf.id[i] + ": no waypoints or destination specified")
            else:
                bs.traf.swvnav[i]    = False
                bs.traf.swvnavspd[i] = False
        if flag == None:
            return True, '\n'.join(output)

def calcvrta(v0, dx, deltime, trafax):
    # Calculate required target ground speed v1 [m/s]
    # to meet an RTA at this leg
    #
    # Arguments are scalar
    #
    #   v0      = current ground speed [m/s]
    #   dx      = leg distance [m]
    #   deltime = time left till RTA[s]
    #   trafax  = horizontal acceleration [m/s2]

    # Set up variables
    dt = deltime

    # Do we need decelerate or accelerate
    if v0 * dt < dx:
        ax = max(0.01,abs(trafax))
    else:
        ax = -max(0.01,abs(trafax))

    # Solve 2nd order equation for v1 which results from:
    #
    #   dx = 0.5*(v0+v1)*dtacc + v1 * dtconst
    #   dt = trta - tnow = dtacc + dtconst
    #   dtacc = (v1-v0)/ax
    #
    # with unknown dtconst, dtacc, v1
    #
    # -.5/ax * v1**2  +(v0/ax+dt)*v1 -0.5*v0**2 / ax - dx =0

    a = -0.5 / ax
    b = (v0 / ax + dt)
    c = -0.5 * v0 * v0 / ax - dx

    D = b * b - 4. * a * c

    # Possibly two v1 solutions
    vlst = []

    if D >= 0.:
        x1 = (-b - sqrt(D)) / (2. * a)
        x2 = (-b + sqrt(D)) / (2. * a)

        # Check solutions for v1
        for v1 in (x1, x2):
            dtacc = (v1 - v0) / ax
            dtconst = dt - dtacc

            # Physically possible: both dtacc and dtconst >0
            if dtacc >= 0 and dtconst >= 0.:
                vlst.append(v1)

    if len(vlst) == 0:  # Not possible? Maybe borderline, so then simple calculation
        vtarg = dx/dt

    # Just in case both would be valid, take closest to v0
    elif len(vlst) == 2:
        vtarg = vlst[int(abs(vlst[1] - v0) < abs(vlst[0] - v0))]

    # Normal case is one solution
    else:
        vtarg = vlst[0]

    return vtarg

def distaccel(v0,v1,axabs):
    """Calculate distance travelled during acceleration/deceleration
    v0 = start speed, v1 = endspeed, axabs = magnitude of accel/decel
    accel/decel is detemremind by sign of v1-v0
    axabs is acceleration/deceleration of which absolute value will be used
    solve for x: x = vo*t + 1/2*a*t*t    v = v0 + a*t """
    return 0.5*np.abs(v1*v1-v0*v0)/np.maximum(.001,np.abs(axabs))
