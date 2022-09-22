"""
This python file is used to create traffic variables used by the LVNL

Created by: Bob van Dillen
Date: 24-12-2021
"""
import socket

import numpy as np
import bluesky as bs
from bluesky.core import Entity, timed_function
from bluesky.tools import misc, geo
from bluesky import stack

# from bluesky import settings


"""
Classes
"""


class LVNLVariables(Entity):
    """
    Definition: Class containing variables used by LVNL
    Methods:
        create():           Create an aircraft
        update():           Update LVNL variables
        selucocmd():        Set UCO for aircraft
        selrelcmd():        Set REL for aircraft
        setarr():           Set the arrival/stack
        setautolabel():     Set automatic label selection
        setflighttype():    Set the flight type
        setils():           Set the ILS route
        setmlabel():        Set the micro label
        setrwy():           Set the runway
        setsid():           Set the SID
        setssr():           Set the SSR code
        setssrlabel():      Set the SSR label
        settracklabel():    Set the track label
        setwtc():           Set the wtc

    Created by: Bob van Dillen
    Date: 24-12-2021
    """

    def __init__(self):
        super().__init__()

        self.swautolabel = False  # Auto label change

        with self.settrafarrays():
            self.arr        = []                           # Arrival/Stack
            self.autolabel  = np.array([], dtype=np.bool)  # Auto label change
            self.dtg        = np.array([])                 # Distance to T-Bar point
            self.dtg_route  = np.array([])                 # Route distance to go
            self.flighttype = []                           # Flight type
            self.mlbl       = np.array([], dtype=np.bool)  # Show micro label
            self.rel        = np.array([], dtype=np.bool)  # Release
            self.rwy        = []                           # Runway
            self.sid        = []                           # SID
            self.ssr        = np.array([], dtype=np.int)   # SSR code
            self.ssrlbl     = []                           # Show SSR label
            self.tracklbl   = np.array([], dtype=np.bool)  # Show track label
            self.uco        = np.array([], dtype=np.str)   # Under Control
            self.wtc        = []                           # Wake Turbulence Category

    def create(self, n=1):
        """
        Function: Create an aircraft
        Args:
            n:  number of aircraft
        Returns: -

        Created by: Bob van Dillen
        Date: 12-1-2022
        """

        super().create(n)

        self.autolabel[-n:] = True
        self.tracklbl[-n:]  = True
        self.mlbl[-n:]      = True   #False

    @timed_function(name='lvnlvars', dt=0.1)
    def update(self):
        """
        Function: Update LVNL variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 1-2-2022
        """

        # --------------- Automatic label selection ---------------

        if self.swautolabel:

            if bs.scr.atcmode == 'APP':
                # Indices
                itracklbl = np.nonzero(bs.traf.alt <= 7467.6)[0]
                issrlbl = np.setdiff1d(np.arange(len(bs.traf.id)), itracklbl)
                iautolabel = np.nonzero(self.autolabel)[0]
                itracklbl = np.intersect1d(itracklbl, iautolabel)
                issrlbl = np.intersect1d(issrlbl, iautolabel)

                # Set labels
                self.tracklbl[itracklbl] = True
                self.tracklbl[issrlbl] = False

                ssrlbl = np.array(self.ssrlbl)
                ssrlbl[itracklbl] = ''
                ssrlbl[issrlbl] = 'C'
                self.ssrlbl = ssrlbl.tolist()

            elif bs.scr.atcmode == 'ACC':
                # Indices
                itracklbl = np.nonzero(np.logical_and(bs.traf.alt <= 7467.6, bs.traf.alt >= 2438.4))[0]
                issrlbl = np.setdiff1d(np.arange(len(bs.traf.id)), itracklbl)
                iautolabel = np.nonzero(self.autolabel)[0]
                itracklbl = np.intersect1d(itracklbl, iautolabel)
                issrlbl = np.intersect1d(issrlbl, iautolabel)

                # Set labels
                self.tracklbl[itracklbl] = True
                self.tracklbl[issrlbl] = False

                ssrlbl = np.array(self.ssrlbl)
                ssrlbl[itracklbl] = ''
                ssrlbl[issrlbl] = 'C'
                self.ssrlbl = ssrlbl.tolist()

        # --------------- T-Bar DTG ---------------

        inirsi_gal1 = misc.get_indices(self.arr, "NIRSI_GAL01")
        inirsi_gal2 = misc.get_indices(self.arr, "NIRSI_GAL02")
        inirsi_603 = misc.get_indices(self.arr, "NIRSI_AM603")

        self.dtg[inirsi_gal1] = geo.kwikdist_matrix(bs.traf.lat[inirsi_gal1], bs.traf.lon[inirsi_gal1],
                                                         np.ones(len(inirsi_gal1))*52.47962777777778,
                                                         np.ones(len(inirsi_gal1))*4.513372222222222)
        self.dtg[inirsi_gal2] = geo.kwikdist_matrix(bs.traf.lat[inirsi_gal2], bs.traf.lon[inirsi_gal2],
                                                         np.ones(len(inirsi_gal2))*52.58375277777778,
                                                         np.ones(len(inirsi_gal2))*4.342225)
        self.dtg[inirsi_603] = geo.kwikdist_matrix(bs.traf.lat[inirsi_603], bs.traf.lon[inirsi_603],
                                                        np.ones(len(inirsi_603))*52.68805555555555,
                                                        np.ones(len(inirsi_603))*4.513333333333334)

        # --------------- GMP DTG ---------------

        # iatp_18c = misc.get_indices(self.arr, "ATP18C")
        # iriv_18c = misc.get_indices(self.arr, "RIV18C")
        # iriv_18r = misc.get_indices(self.arr, "RIV18R")
        # isug_18r = misc.get_indices(self.arr, "SUG18R")
        #
        # self.dtg[iatp_18c] = geo.kwikdist_matrix(bs.traf.lat[iatp_18c], bs.traf.lon[iatp_18c],
        #                                             np.ones(len(iatp_18c)) * 52.61224523851872,
        #                                             np.ones(len(iatp_18c)) * 4.890376355417231)
        # self.dtg[iriv_18c] = geo.kwikdist_matrix(bs.traf.lat[iriv_18c], bs.traf.lon[iriv_18c],
        #                                             np.ones(len(iriv_18c)) * 52.61224523851872,
        #                                             np.ones(len(iriv_18c)) * 4.890376355417231)
        # self.dtg[iriv_18r] = geo.kwikdist_matrix(bs.traf.lat[iriv_18r], bs.traf.lon[iriv_18r],
        #                                            np.ones(len(iriv_18r)) * 52.60490551344223,
        #                                            np.ones(len(iriv_18r)) * 4.581121278305933)
        # self.dtg[isug_18r] = geo.kwikdist_matrix(bs.traf.lat[isug_18r], bs.traf.lon[isug_18r],
        #                                          np.ones(len(isug_18r)) * 52.60490551344223,
        #                                          np.ones(len(isug_18r)) * 4.581121278305933)

        # --------------- RUNWAY DTG ---------------

        # i_18c = misc.get_indices(self.rwy, ['18R', '18R_E'])
        # i_18r = misc.get_indices(self.rwy, ['18C', '18C_E'])
        #
        # self.dtg[i_18c] = geo.kwikdist_matrix(bs.traf.lat[i_18c], bs.traf.lon[i_18c],
        #                                          np.ones(len(i_18c)) * 52.331388888888895,
        #                                          np.ones(len(i_18c)) * 4.74)
        # self.dtg[i_18r] = geo.kwikdist_matrix(bs.traf.lat[i_18r], bs.traf.lon[i_18r],
        #                                          np.ones(len(i_18r)) * 52.36027777777778,
        #                                          np.ones(len(i_18r)) * 4.711666666666667)

        # --------------- DTG ALONG ROUTE ---------------

        naircraft = len(bs.traf.lat)    # number of aircrafts

        for idx in range(naircraft):
            # Distance calculation
            iactwp = bs.traf.ap.route[idx].iactwp  #active waypoint
            if iactwp >= 0:
                dist_iactwp = geo.kwikdist(bs.traf.lat[idx], bs.traf.lon[idx],
                                           bs.traf.ap.route[idx].wplat[iactwp], bs.traf.ap.route[idx].wplon[iactwp])
                dist_wp = np.sum(bs.traf.ap.route[idx].wpdistto[iactwp+1:])
                self.dtg_route[idx] = dist_iactwp + dist_wp
        return

    @stack.command(name='UCO')
    def selucocmd(self, idx: 'acid', IP):
        """
        Function: Set UCO for aircraft
        Args:
            idx:    index for traffic arrays
        Returns: -

        Created by: Bob van Dillen
        Date: 1-2-2022

        Edited by: Mitchell de Keijzer
        Date: 10-5-2022
        Changed: IP address in UCO array to check for UCO with multiposition
        """

        # Autopilot modes (check if there is a route)
        if bs.traf.ap.route[idx].nwp > 0:
            # Enable autopilot modes
            bs.traf.swlnav[idx] = True
            bs.traf.swvnav[idx] = True
            bs.traf.swvnavspd[idx] = True
        else:
            # Set current heading/altitude/speed
            bs.traf.selhdg[idx] = bs.traf.hdg[idx]
            bs.traf.selalt[idx] = bs.traf.alt[idx]
            bs.traf.selspd[idx] = bs.traf.cas[idx]
            # Disable autopilot modes
            bs.traf.swlnav[idx] = False
            bs.traf.swvnav[idx] = False
            bs.traf.swvnavspd[idx] = False

        # Labels
        self.tracklbl[idx] = True
        self.ssrlbl[idx] = ''

        # Set UCO/REL
        bs.traf.trafdatafeed.uco(idx)
        self.uco[idx] = IP[-11:]
        self.rel[idx] = False
        print('UCO list', self.uco)
        # print('')

    @stack.command(name='REL',)
    def setrelcmd(self, idx: 'acid'):
        """
        Function: Set REL for aircraft
        Args:
            idx:    index for traffic arrays
        Returns: -

        Created by: Bob van Dillen
        """

        # Autopilot modes
        bs.traf.swlnav[idx] = True
        bs.traf.swvnav[idx] = True
        bs.traf.swvnavspd[idx] = True

        # Labels
        self.tracklbl[idx] = False
        self.ssrlbl[idx] = 'C'

        # Set UCO/REL
        self.uco[idx] = False
        self.rel[idx] = True
        print('REL list', self.rel)

    @stack.command(name='ARR', brief='ARR CALLSIGN ARRIVAL/STACK (ADDWPTS [ON/OFF])', aliases=('STACK',))
    def setarr(self, idx: 'acid', arr: str = '', addwpts: 'onoff' = True):
        """
        Function: Set the arrival/stack
        Args:
            idx:        index for traffic arrays [int]
            arr:        arrival/stack [str]
            addwpts:    add waypoints [bool]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """
        # IP = socket.gethostbyname(socket.gethostname())
        self.arr[idx] = arr.upper()
        # self.uco[idx] = IP[-11:]

        if addwpts:
            acid = bs.traf.id[idx]
            # self.uco[idx] = IP[-11:]
            cmd = 'PCALL LVNL/Routes/ARR/'+arr.upper()+' '+acid

            stack.stack(cmd)

    @stack.command(name='SETROUTE', brief='SETROUTE CALLSIGN ARRIVAL/STACK')
    def setroute(self, idx: 'acid', route: str = ''):
        """
        Function: Set the route for the wanted simulation
        Args:
            idx:        index for traffic arrays [int]
            route:      arrival/stack [str]
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 12-5-2022
        """
        # IP = socket.gethostbyname(socket.gethostname())
        acid = bs.traf.id[idx]
        # self.uco[idx] = IP[-11:]
        cmd = 'PCALL LVNL/Routes/' + route.upper() + ' ' + acid
        stack.stack(cmd)

    @stack.command(name='AUTOLABEL', brief='AUTOLABEL (ON/OFF or ACID or ACID ON/OFF)')
    def setautolabel(self, *args):
        """
        Function: Set automatic label selection
        Args:
            *args:  arguments [tuple]
        Returns: -

        Created by: Bob van Dillen
        Date: 27-2-2022
        """

        # No arguments
        if len(args) == 0:
            self.swautolabel = not self.swautolabel

        # ON/OFF
        if args[0].upper() == 'ON':
            self.swautolabel = True
        elif args[0].upper() == 'OFF':
            self.swautolabel = False

        # ACID
        elif bs.traf.id2idx(args[0]) > 0:
            idx = bs.traf.id2idx(args[0])

            # Other arguments
            if len(args) > 1:

                # ON/OFF
                if args[1].upper() == 'ON':
                    self.autolabel[idx] = True
                elif args[1].upper() == 'OFF':
                    self.autolabel[idx] = False
                else:
                    return False, 'AUTOLABEL: Not a valid input'

            else:
                self.autolabel[idx] = not self.autolabel[idx]

        else:
            return False, 'AUTOLABEL: Not a valid input'

    @stack.command(name='FLIGHTTYPE', brief='FLIGHTTYPE CALLSIGN TYPE')
    def setflighttype(self, idx: 'acid', flighttype: str):
        """
        Function: Set the flight type
        Args:
            idx:        index for traffic arrays [int]
            flighttype: flight type [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """

        if isinstance(flighttype, str):
            self.flighttype[idx] = flighttype.upper()

    @stack.command(name='ILS', brief='ILS CALLSIGN RWY', aliases=('STACK',))
    def setils(self, idx: 'acid', rwy: str):
        """
        Function: Set the ILS route
        Args:
            idx:        index for traffic arrays [int]
            rwy:        runway [str]
        Returns: -

        Created by: Mitchell de Keijzer
        Date: 16-02-2022
        """

        acid = bs.traf.id[idx]
        cmd = 'PCALL LVNL/Routes/ARR/ILS_' + rwy + ' ' + acid
        stack.stack(cmd)

    @stack.command(name='MICROLABEL', brief='MICROLABEL CALLSIGN')
    def setmlabel(self, idx: 'acid'):
        """
        Function: Set the micro label
        Args:
            idx:    index for traffic arrays [int]
        Returns: -

        Created by: Bob van Dillen
        Date: 24-1-2022
        """

        self.mlbl[idx] = not self.mlbl[idx]

    @stack.command(name='RWY', brief='RWY CALLSIGN RUNWAY', aliases=('RW',))
    def setrwy(self, idx: 'acid', rwy: str):
        """
        Function: Set the runway
        Args:
            idx:    index for traffic arrays [int]
            rwy:    runway [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """

        if isinstance(rwy, str):
            self.rwy[idx] = rwy.upper()

    @stack.command(name='SID', brief='SID CALLSIGN SID')
    def setsid(self, idx: 'acid', sid: str = '', addwpts: 'onoff' = True):
        """
        Function: Set the SID
        Args:
            idx:    index for traffic arrays [int]
            sid:    SID [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        Edited by: Mitchell de Keijzer
        Date: 25-02-2022
        Changes: small bug fix, added scenario files to scenario/lvnl/routes/sid
        """

        self.sid[idx] = sid.upper()

        if addwpts:
            acid = bs.traf.id[idx]
            cmd = 'PCALL LVNL/Routes/SID/'+sid.upper()+' '+acid
            stack.stack(cmd)

    @stack.command(name='SSRCODE', brief='SSRCODE CALLSIGN SSR')
    def setssr(self, idx: 'acid', ssr: float):
        """
        Function: Set the SSR code
        Args:
            idx:    index for traffic arrays [int]
            ssr:    SSR code [int]
        Returns: -

        Created by: Bob van Dillen
        Date: 25-1-2022
        """

        self.ssr[idx] = int(ssr)

    @stack.command(name='SSRLABEL', brief='SSRLABEL CALLSIGN')
    def setssrlabel(self, idx: 'acid', *args):
        """
        Function: Set the SSR label
        Args:
            idx:        index for traffic arrays [int]
            *args:      arguments [tuple]
        Returns: -

        Created by: Bob van Dillen
        Date: 24-1-2022
        """

        # No arguments passed
        if len(args) == 0:
            if self.ssrlbl[idx]:
                self.ssrlbl[idx] = ''
            else:
                self.ssrlbl[idx] = 'C'
            self.autolabel[idx] = False

        # Switch on/off
        elif args[0].upper() == 'ON' or args[0].upper() == 'TRUE':
            self.ssrlbl[idx] = 'C'
            self.autolabel[idx] = False
        elif args[0].upper() == 'OFF' or args[0].upper() == 'FALSE':
            self.ssrlbl[idx] = ''
            self.autolabel[idx] = False

        # Switch modes on/off
        else:
            for ssrmode in args:
                ssrmode = ssrmode.upper()

                # Check if it is a valid mode
                if ssrmode in ['A', 'C', 'ACID']:
                    # Get active modes
                    if self.ssrlbl[idx]:
                        actmodes = self.ssrlbl[idx].split(';')
                    else:
                        actmodes = []

                    # Remove/Append
                    if ssrmode in actmodes:
                        actmodes.remove(ssrmode)
                    else:
                        actmodes.append(ssrmode)

                    # Reconstruct ssrlbl
                    ssrlbl = ''
                    for mode in actmodes:
                        ssrlbl += mode+';'
                    ssrlbl = ssrlbl[:-1]  # Leave out last ';'

                    self.ssrlbl[idx] = ssrlbl
                    self.autolabel[idx] = False

            else:
                return False, 'SSRLABEL: Not a valid SSR label item'

    @stack.command(name='TRACKLABEL', brief='TRACKLABEL CALLSIGN')
    def settracklabel(self, idx: 'acid', *args):
        """
        Function: Set the track label
        Args:
            idx:        index for traffic arrays [int]
            *args:      arguments [tuple]
        Returns: -

        Created by: Bob van Dillen
        Date: 24-1-2022
        """

        # No arguments passed
        if len(args) == 0:
            self.tracklbl[idx] = not self.tracklbl[idx]
            self.autolabel[idx] = False

        # Switch on/off
        elif args[0].upper() == 'ON' or args[0].upper() == 'TRUE':
            self.tracklbl[idx] = True
            self.autolabel[idx] = False
        elif args[0].upper() == 'OFF' or args[0].upper() == 'FALSE':
            self.tracklbl[idx] = False
            self.autolabel[idx] = False

        else:
            return False, 'TRACKLABEL: Not a valid argument'

    @stack.command(name='WTC', brief='WTC CALLSIGN WTC')
    def setwtc(self, idx: 'acid', wtc: str = ''):
        """
        Function: Set the wtc
        Args:
            idx:    index for traffic arrays [int]
            wtc:    wtc [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 21-12-2021
        """

        if isinstance(wtc, str):
            self.wtc[idx] = wtc.upper()
