""" Revised BlueSky aircraft performance calculations using BADA 3.xx."""
import numpy as np
import bluesky as bs
from bluesky.tools.aero import kts, ft, g0, vtas2cas, vcas2tas
from bluesky.traffic.performance.perfbase import PerfBase
from bluesky.traffic.performance.wilabada.performance import esf, phases, calclimits, PHASE

from bluesky import settings
from . import coeff_bada

# Register settings defaults
settings.set_variable_defaults(perf_path_bada='data/performance/BADA',
                               performance_dt=1.0, verbose=False)

if not coeff_bada.check(settings.perf_path_bada):
    raise ImportError('BADA performance model: Error trying to find BADA files in ' + settings.perf_path_bada + '!')

class WILABADA(PerfBase):
    """
    Aircraft performance implementation based on BADA.
    Methods:

        reset()           : clear current database
        create(actype)    : initialize new aircraft with performance parameters
        delete(idx)       : remove performance parameters from deleted aircraft
        perf()            : calculate aircraft performance
        limits()          : calculate flight envelope

    Created by  : wila
    Note: This class is based on
        BADA 3.10
    """

    def __init__(self):
        super().__init__()
        # Load coefficient files if we haven't yet
        coeff_bada.init(settings.perf_path_bada)

        # self.warned = False     # Flag: Did we warn for default perf parameters yet?
        # self.warned2 = False    # Flag: Use of piston engine aircraft?
        #
        # # Flight performance scheduling
        # self.warned2 = False        # Flag: Did we warn for default engine parameters yet?

        # Register the per-aircraft parameter arrays
        with self.settrafarrays():
            # engine
            self.jet        = np.array([])
            self.turbo      = np.array([])
            self.piston     = np.array([])

            # masses and dimensions
            self.mass       = np.array([])  # effective mass [kg]
            self.mref = np.array([]) # ref. mass [kg]: 70% between min and max. mass
            self.mmin       = np.array([])  # OEW (or assumption) [kg]
            self.mmax       = np.array([])  # MTOW (or assumption) [kg]
            self.mpyld = np.array([]) # MZFW-OEW (or assumption) [kg]
            self.gw         = np.array([])  # weight gradient on max. alt [m/kg]
            self.Sref       = np.array([])  # wing reference surface area [m^2]

            # flight enveloppe
            self.vmto       = np.array([])  # min TO spd [m/s]
            self.vmic       = np.array([])  # min climb spd [m/s]
            self.vmcr       = np.array([])  # min cruise spd [m/s]
            self.vmap       = np.array([])  # min approach spd [m/s]
            self.vmld       = np.array([])  # min landing spd [m/s]

            self.vmo        = np.array([])   # max operating speed [m/s]
            self.mmo        = np.array([])   # max operating mach number [-]
            self.hmax       = np.array([])   # max. alt above standard MSL (ISA) at MTOW [m]
            self.hmaxact    = np.array([])   # max. alt depending on temperature gradient [m]
            self.hmo        = np.array([])   # max. operating alt abov standard MSL [m]
            self.gt         = np.array([])   # temp. gradient on max. alt [ft/k]
            self.maxthr     = np.array([])   # maximum thrust [N]

            # Buffet Coefficients
            self.clbo       = np.array([])    # buffet onset lift coefficient [-]
            self.k          = np.array([])    # buffet coefficient [-]
            self.cm16       = np.array([])    # CM16

            # reference CAS speeds
            self.cascl      = np.array([])    # climb [m/s]
            self.cascr      = np.array([])    # cruise [m/s]
            self.casdes     = np.array([])    # descent [m/s]

            #reference mach numbers [-]
            self.macl       = np.array([])    # climb
            self.macr       = np.array([])    # cruise
            self.mades      = np.array([])    # descent

            # parasitic drag coefficients per phase [-]
            self.cd0to      = np.array([])    # phase takeoff
            self.cd0ic      = np.array([])    # phase initial climb
            self.cd0cr      = np.array([])    # phase cruise
            self.cd0ap      = np.array([])    # phase approach
            self.cd0ld      = np.array([])    # phase land
            self.gear       = np.array([])    # drag due to gear down

            # induced drag coefficients per phase [-]
            self.cd2to      = np.array([])    # phase takeoff
            self.cd2ic      = np.array([])    # phase initial climb
            self.cd2cr      = np.array([])    # phase cruise
            self.cd2ap      = np.array([])    # phase approach
            self.cd2ld      = np.array([])    # phase land

            # max climb thrust coefficients
            self.ctcth1      = np.array([])   # jet/piston [N], turboprop [ktN]
            self.ctcth2      = np.array([])   # [ft]
            self.ctcth3      = np.array([])   # jet [1/ft^2], turboprop [N], piston [ktN]

            # reduced climb power coefficient
            self.cred       = np.array([])    # [-]

            # 1st and 2nd thrust temp coefficient
            self.ctct1      = np.array([])    # [k]
            self.ctct2      = np.array([])    # [1/k]
            self.dtemp      = np.array([])    # [k]

            # Descent Fuel Flow Coefficients
            # Note: Ctdes,app and Ctdes,lnd assume a 3 degree descent gradient during app and lnd
            self.ctdesl      = np.array([])   # low alt descent thrust coefficient [-]
            self.ctdesh      = np.array([])   # high alt descent thrust coefficient [-]
            self.ctdesa      = np.array([])   # approach thrust coefficient [-]
            self.ctdesld     = np.array([])   # landing thrust coefficient [-]

            # transition altitude for calculation of descent thrust
            self.hpdes       = np.array([])   # [m]

            # Energy Share Factor
            self.ESF         = np.array([])   # [-]

            # reference speed during descent
            self.vdes        = np.array([])   # [m/s]
            self.mdes        = np.array([])   # [-]

            # flight phase
            self.phase       = np.array([])
            self.post_flight = np.array([])   # taxi prior of post flight?
            self.pf_flag     = np.array([])

            # Thrust specific fuel consumption coefficients
            self.cf1         = np.array([])   # jet [kg/(min*kN)], turboprop [kg/(min*kN*knot)], piston [kg/min]
            self.cf2         = np.array([])   # [knots]
            self.cf3         = np.array([])   # [kg/min]
            self.cf4         = np.array([])   # [ft]
            self.cf_cruise   = np.array([])   # [-]

            # performance
            self.T      = np.array([])   # thrust
            self.D           = np.array([])   # drag
            self.fuelflow    = np.array([])   # fuel flow

            # ground
            self.tol         = np.array([])   # take-off length[m]
            self.ldl         = np.array([])   # landing length[m]
            self.ws          = np.array([])   # wingspan [m]
            self.len         = np.array([])   # aircraft length[m]
            self.gr_acc      = np.array([])   # ground acceleration [m/s^2]
            self.gr_dec      = np.array([])   # ground deceleration [m/s^2]

            # # limit settings
            # self.limspd      = np.array([])  # limit speed
            # self.limspd_flag = np.array([], dtype=np.bool)  # flag for limit spd - we have to test for max and min
            # self.limalt      = np.array([])  # limit altitude
            # self.limalt_flag = np.array([])  # A need to limit altitude has been detected
            # self.limvs       = np.array([])  # limit vertical speed due to thrust limitation
            # self.limvs_flag  = np.array([])  # A need to limit V/S detected

    def engchange(self, acid, engid=None):
        return False, "BADA performance model doesn't allow changing engine type"
    # Waarom niet?

    def create(self, n = 1):
        super().create(n)
        """
        Create new aircraft
        note: coefficients are initialized in SI units
        """


        actypes = bs.traf.type[-n:]

        # general
        # designate aircraft to its aircraft type
        for i, actype in enumerate(actypes):
            syn, coeff = coeff_bada.getCoefficients(actype)
            if syn:
                continue
            syn, coeff = coeff_bada.getCoefficients('B744')
            bs.traf.type[-n + i] = syn.accode

            # if not settings.verbose:
            #     if not self.warned:
            #         print("Aircraft is using default B747-400 performance.")
            #         self.warned = True
            # else:
            print("Flight " + bs.traf.id[
                                  -n:] + " has an unknown aircraft type, " + actype + ", BlueSky then uses default B747-400 performance.")

        # designate aicraft to its aircraft type
        self.jet[-n:] = 1 if coeff.engtype == 'Jet' else 0
        self.turbo[-n:] = 1 if coeff.engtype == 'Turboprop' else 0
        self.piston[-n:] = 1 if coeff.engtype == 'Piston' else 0

        # Initial aircraft mass is currently reference mass.
        # BADA 3.12 also supports masses between 1.2*mmin and mmax
        self.mass[-n:] = coeff.m_ref * 1000.0
        self.mmin[-n:] = coeff.m_min * 1000.0
        self.mmax[-n:] = coeff.m_max * 1000.0
        self.gw[-n:] = coeff.mass_grad * ft

        # Surface Area [m^2]
        self.Sref[-n:] = coeff.S

        # flight envelope
        # minimum speeds per phase
        self.vmto[-n:] = coeff.Vstall_to * coeff.CVmin_to * kts
        self.vmic[-n:] = coeff.Vstall_ic * coeff.CVmin * kts
        self.vmcr[-n:] = coeff.Vstall_cr * coeff.CVmin * kts
        self.vmap[-n:] = coeff.Vstall_ap * coeff.CVmin * kts
        self.vmld[-n:] = coeff.Vstall_ld * coeff.CVmin * kts
        self.vmin[-n:] = 0.0
        self.vmo[-n:] = coeff.VMO * kts
        self.mmo[-n:] = coeff.MMO
        self.vmax[-n:] = self.vmo[-n:]

        # max. altitude parameters
        self.hmo[-n:] = coeff.h_MO * ft
        self.hmax[-n:] = coeff.h_max * ft
        self.hmaxact[-n:] = coeff.h_max * ft  # initialize with hmax
        self.gt[-n:] = coeff.temp_grad * ft

        # max thrust setting
        self.maxthr[-n:] = 1e6  # initialize with excessive setting to avoid unrealistic limit setting

        # Buffet Coefficients
        self.clbo[-n:] = coeff.Clbo
        self.k[-n:] = coeff.k
        self.cm16[-n:] = coeff.CM16

        # reference speeds
        # reference CAS speeds
        self.cascl[-n:] = coeff.CAScl1[0] * kts
        self.cascr[-n:] = coeff.CAScr1[0] * kts
        self.casdes[-n:] = coeff.CASdes1[0] * kts

        # reference mach numbers
        self.macl[-n:] = coeff.Mcl[0]
        self.macr[-n:] = coeff.Mcr[0]
        self.mades[-n:] = coeff.Mdes[0]

        # reference speed during descent
        self.vdes[-n:] = coeff.Vdes_ref * kts
        self.mdes[-n:] = coeff.Mdes_ref

        # aerodynamics
        # parasitic drag coefficients per phase
        self.cd0to[-n:] = coeff.CD0_to
        self.cd0ic[-n:] = coeff.CD0_ic
        self.cd0cr[-n:] = coeff.CD0_cr
        self.cd0ap[-n:] = coeff.CD0_ap
        self.cd0ld[-n:] = coeff.CD0_ld
        self.gear[-n:] = coeff.CD0_gear

        # induced drag coefficients per phase
        self.cd2to[-n:] = coeff.CD2_to
        self.cd2ic[-n:] = coeff.CD2_ic
        self.cd2cr[-n:] = coeff.CD2_cr
        self.cd2ap[-n:] = coeff.CD2_ap
        self.cd2ld[-n:] = coeff.CD2_ld

        # reduced climb coefficient
        self.cred[-n:] = np.where(
            self.jet[-n:], coeff.Cred_jet,
            np.where(self.turbo[-n:], coeff.Cred_turboprop, coeff.Cred_piston)
        )

        # commented due to vectrization
        # # NOTE: model only validated for jet and turbo aircraft
        # if self.piston[-n:] and not self.warned2:
        #     print "Using piston aircraft performance.",
        #     print "Not valid for real performance calculations."
        #     self.warned2 = True

        # performance

        # max climb thrust coefficients
        self.ctcth1[-n:] = coeff.CTC[0]  # jet/piston [N], turboprop [ktN]
        self.ctcth2[-n:] = coeff.CTC[1]  # [ft]
        self.ctcth3[-n:] = coeff.CTC[2]  # jet [1/ft^2], turboprop [N], piston [ktN]

        # 1st and 2nd thrust temp coefficient
        self.ctct1[-n:] = coeff.CTC[3]  # [k]
        self.ctct2[-n:] = coeff.CTC[4]  # [1/k]
        self.dtemp[-n:] = 0.0  # [k], difference from current to ISA temperature. At the moment: 0, as ISA environment

        # Descent Fuel Flow Coefficients
        # Note: Ctdes,app and Ctdes,lnd assume a 3 degree descent gradient during app and lnd
        self.ctdesl[-n:] = coeff.CTdes_low
        self.ctdesh[-n:] = coeff.CTdes_high
        self.ctdesa[-n:] = coeff.CTdes_app
        self.ctdesld[-n:] = coeff.CTdes_land

        # transition altitude for calculation of descent thrust
        self.hpdes[-n:] = coeff.Hp_des * ft
        self.ESF[-n:] = 1.0  # neutral initialisation

        # flight phase
        self.phase[-n:] = PHASE["None"]
        self.post_flight[-n:] = False  # we assume prior
        self.pf_flag[-n:] = True

        # Thrust specific fuel consumption coefficients
        # prevent from division per zero in fuelflow calculation
        self.cf1[-n:] = coeff.Cf1
        self.cf2[-n:] = 1.0 if coeff.Cf2 < 1e-9 else coeff.Cf2
        self.cf3[-n:] = coeff.Cf3
        self.cf4[-n:] = 1.0 if coeff.Cf4 < 1e-9 else coeff.Cf4
        self.cf_cruise[-n:] = coeff.Cf_cruise

        self.thrust[-n:] = 0.0
        self.D[-n:] = 0.0
        self.fuelflow[-n:] = 0.0

        # ground
        self.tol[-n:] = coeff.TOL
        self.ldl[-n:] = coeff.LDL
        self.ws[-n:] = coeff.wingspan
        self.len[-n:] = coeff.length

        # for now, BADA aircraft have the same acceleration as deceleration
        self.gr_acc[-n:] = coeff.gr_acc
        self.gr_dec[-n:] = coeff.gr_acc ######### ik weet niet zeker of dit zomaar mag -winand

        return

    def update(self):

        pass

    def limits(self):

        pass


