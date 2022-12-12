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
from itertools import combinations
from bluesky import settings

bs.settings.set_variable_defaults(scenario_path_SIDs = 'scenario/LVNL/Routes/SID_NO_SPDCMDS')

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
        setsymbol():        Set the symbol

    Created by: Bob van Dillen
    Date: 24-12-2021
    """

    def __init__(self):
        super().__init__()

        self.atcIP = {'TWR': [],
                      'APP': [],
                      'ACC': []}

        with self.settrafarrays():
            self.arr        = []                           # Arrival/Stack
            self.dtg        = np.array([])                 # Distance to T-Bar point
            self.dtg_route  = np.array([])                 # Route DTG for GMPEOR
            self.flighttype = []                           # Flight type
            self.rwy        = []                           # Runway
            self.sid        = []                           # SID
            self.ssr        = np.array([], dtype=np.int)   # SSR code
            self.uco        = np.array([], dtype=np.str)   # Under Control
            self.symbol     = np.array([], dtype=np.str)   # UCO symbol to draw
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

        self.symbol[-n:]    = ''
        self.uco[-n:]       = '0'

    @timed_function(name='lvnlvars', dt=0.1)
    def update(self):
        """
        Function: Update LVNL variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 1-2-2022
        """

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

        i_18c = misc.get_indices(self.rwy, ['18R', '18R_E'])
        i_18r = misc.get_indices(self.rwy, ['18C', '18C_E'])

        self.dtg[i_18c] = geo.kwikdist_matrix(bs.traf.lat[i_18c], bs.traf.lon[i_18c],
                                                 np.ones(len(i_18c)) * 52.331388888888895,
                                                 np.ones(len(i_18c)) * 4.74)
        self.dtg[i_18r] = geo.kwikdist_matrix(bs.traf.lat[i_18r], bs.traf.lon[i_18r],
                                                 np.ones(len(i_18r)) * 52.36027777777778,
                                                 np.ones(len(i_18r)) * 4.711666666666667)

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
            # print('Route ',bs.traf.id[idx], bs.traf.ap.route[idx].wpname)
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

        # Check if already UCO
        if not self.uco[idx] == IP[-11:]:
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

            # Set UCO/REL
            bs.traf.trafdatafeed.uco(idx)
            self.uco[idx] = IP[-11:]

            # Set the symbol
            if IP[-11:] in self.atcIP['TWR']:
                if self.flighttype[idx] == 'OUTBOUND':
                    self.symbol[idx] = 'TWROUT'
                else:
                    self.symbol[idx] = 'TWRIN'
            elif IP[-11:] in self.atcIP['APP']:
                self.symbol[idx] = 'APP'
            elif IP[-11:] in self.atcIP['ACC']:
                self.symbol[idx] = 'ACC'
        else:
            bs.scr.echo(bs.traf.id[idx] + ' already UCO')

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

        # Set UCO/REL
        self.uco[idx] = '0'

        # Set the symbol
        if self.flighttype[idx] == 'INBOUND':
            if self.symbol[idx] == 'ACC':
                self.symbol[idx] = 'APP'
            elif self.symbol[idx] == 'APP':
                self.symbol[idx] = 'TWRIN'
        elif self.flighttype[idx] == 'OUTBOUND':
            if self.symbol[idx] == 'TWROUT':
                self.symbol[idx] = 'APP'
            elif self.symbol[idx] == 'APP':
                self.symbol[idx] = 'ACC'
        else:
            if bs.scr.atcmode == 'APP':
                self.symbol[idx] = 'TWRIN'
            else:
                self.symbol[idx] = 'ACC'

    @stack.command(name='ATCIP', brief='ATCIP ATCMODE IP')
    def setatcIP(self, atcmode, IP):
        """
        Function: Connect IP-address to ATC mode
        Args:
            atcmode:    ATC mode [str]
            IP:         IP-address [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 25-9-2022
        """

        # Delete IP from previous mode
        for mode in ['TWR', 'APP', 'ACC']:
            if IP in self.atcIP[mode]:
                self.atcIP[mode].remove(IP)

        # Set IP
        if atcmode != 'BLUESKY':
            self.atcIP[atcmode].append(IP)

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

        id = bs.traf.id[idx]
        bs.traf.lvnlvars.setgrp(idx, 'INBOUND')
        bs.traf.lvnlvars.setgrp(idx, id, color=(np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255)))

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
            if self.flighttype[idx] == 'OUTBOUND':
                self.symbol[idx] = 'TWROUT'
            elif self.flighttype[idx] == 'INBOUND':
                self.symbol[idx] = 'ACC'

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
        self.rwy[idx] = rwy

    @stack.command(name='WPTARR', brief='HDGARR CALLSIGN WPT', aliases=('STACK',))
    def setWPTARR(self, idx: 'acid', WPT: str):
        """
        Function: Function used for the "Programma Luchtruim Herziening (PLRH). Issues a direct to the waypoints,
                  and pcalls the scenarios such that it follows the trajectory to the runway.
        Args:
            idx:        index for traffic arrays [int]
            wpt:        waypoint [str]
        Returns: -

        Created by: Lars Dijkstra
        Date: 18-11-2022
        """

        acid = bs.traf.id[idx]

        # Remove the old route of acid. Executing the cmd at function level allows for more easy changes to
        # waypoint restrictions.
        cmd = 'delrte' + ' ' + acid
        stack.stack(cmd)

        cmd = 'PCALL LVNL/PLRH/TID_SCN/' + WPT + '.scn' + ' ' + acid
        stack.stack(cmd)
        bs.traf.ap.dpswitch[idx] = True


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

        id = bs.traf.id[idx]
        bs.traf.lvnlvars.setgrp(idx, 'INBOUND')
        bs.traf.lvnlvars.setgrp(idx, id, color=(np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255)))

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
            cmd = 'PCALL '+ settings.scenario_path_SIDs + "/" + sid.upper()+' '+acid
            stack.stack(cmd)

    @stack.command(name='SIDTO', brief='SID CALLSIGN SID')
    def setsidTO(self, idx: 'acid', sid: str = '', addwpts: 'onoff' = True):
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
            cmd = 'PCALL ' + settings.scenario_path_SIDs + "/" + sid.upper()+' '+acid
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

    @stack.command(name='SYMBOL', brief='SYMBOL CALLSIGN MODE[ACC/APP/TWRIN/TWROUT]')
    def setsymbol(self, idx: 'acid', symbol: str = ''):
        """
        Function: Set the symbol
        Args:
            idx:      index for traffic arrays [int]
            symbol:   symbol controller responsible [ACC/APP/TWRIN/TWROUT] [str]
        Returns: -

        Created by: Ajay Kumbhar
        """

        if isinstance(symbol, str):
            self.symbol[idx] = symbol.upper()

    @stack.command(name='SETGRP', brief='SETGRP CALLSIGN GRP')
    def setgrp(self, idx: 'acid', grp: str = '', **kwargs):
        """
        Function: Assign aircraft to group used for trails
        Args:
            idx:    index for traffic arrays [int]
            grp:    group aircraft should belong to
        Returns: -

        Created by: Lars Dijkstra
        Date: 29-11-2022
        """
        acid = bs.traf.id[idx]
        if grp.upper() not in bs.traf.iTrails.setgrp:
            bs.traf.iTrails.setgrp[grp.upper()] = []
        if grp.upper() not in bs.traf.iTrails.swgrp:
            bs.traf.iTrails.swgrp[grp.upper()] = False
        if grp.upper() not in bs.traf.iTrails.clrs:
            bs.traf.iTrails.clrs[grp.upper()] = (0, 255, 255)
            if 'color' in kwargs:
                bs.traf.iTrails.clrs[grp.upper()] = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
        if acid in bs.traf.iTrails.setgrp[grp.upper()]:
            bs.scr.echo('{} is already assigned to group {}'.format(acid, grp.upper()))
        else:
            bs.traf.iTrails.setgrp[grp.upper()].append(acid)
            if bs.traf.iTrails.swgrp[grp.upper()]:
                self.overlap(grp.upper(), callsign = acid)
        bs.traf.iTrails.grpchange = True
        bs.traf.iTrails.change = True

    @stack.command(name='DELGRP', brief='SETGRP CALLSIGN GRP')
    def delgrp(self, idx: 'acid', grp: str = ''):
        """
        Function: delete aircraft from group
        Args:
            idx:    index for traffic arrays [int]
            grp:    group aircraft should belong to
        Returns: -

        Created by: Lars Dijkstra
        Date: 29-11-2022
        """

        acid = bs.traf.id[idx]

        if grp.upper() in bs.traf.iTrails.setgrp:
            if acid in bs.traf.iTrails.setgrp[grp.upper()]:
                bs.traf.iTrails.setgrp[grp.upper()].remove(acid)
                if len(bs.traf.iTrails.setgrp[grp.upper()]) == 0:
                    bs.traf.iTrails.setgrp.pop(grp.upper())
                    bs.traf.iTrails.swgrp.pop(grp.upper())
                    bs.traf.iTrails.clrs.pop(grp.upper())
            else:
                bs.scr.echo('Could not find {} in group {}'.format(acid, grp.upper()))
        else:
            bs.scr.echo('Group {} does not exist'.format(grp.upper()))

        bs.traf.iTrails.grpchange = True
        bs.traf.iTrails.change = True


    def overlap(self, grp, **kwargs):

        grp_combinations = [list(map(str, comb)) for comb in combinations(bs.traf.iTrails.setgrp, 2)]

        for combination in grp_combinations:
            if bs.traf.iTrails.swgrp[combination[0]] and bs.traf.iTrails.swgrp[combination[1]]:
                if bool(set(bs.traf.iTrails.setgrp[combination[0]]) & set(bs.traf.iTrails.setgrp[combination[1]])):
                    if combination[0] == grp:
                        in_conflict = combination[1]
                    elif combination[1] == grp:
                        in_conflict = combination[0]
                    bs.traf.iTrails.swgrp[in_conflict] = False
                    if 'callsign' in kwargs:
                        bs.scr.echo('Turned off trails for group {} due to a conflict with group {}. {} cannot be part of two active groups.'.format(in_conflict, grp, kwargs['callsign']))
                    else:
                        bs.scr.echo('Turned off trails for group {} due to a conflict with group {}. An aircraft cannot be part of two active groups.'.format(in_conflict, grp))


    @stack.command(name='SWGRP', brief='SWGRP GRP ON/OFF')
    def swgrp(self, grp: str = '', sw: str = ''):
        """
        Function: turn trails on for grp
        Args:
            grp:    group
        Returns: -

        Created by: Lars Dijkstra
        Date: 29-11-2022
        """

        if sw.upper() == 'ON':
            sw = True
        elif sw.upper() == 'OFF':
            sw = False
        else:
            bs.scr.echo('Please use on/off to turn trails off or on for group {}'.format(grp.upper()))
            return

        if grp.upper() not in bs.traf.iTrails.setgrp:
            bs.traf.iTrails.setgrp[grp.upper()] = []
        if grp.upper() not in bs.traf.iTrails.clrs:
            bs.traf.iTrails.clrs[grp.upper()] = 'DEFAULT'
        if grp.upper() in bs.traf.iTrails.swgrp:
            if bs.traf.iTrails.swgrp[grp.upper()] != sw:
                bs.traf.iTrails.swgrp[grp.upper()] = sw
            else:
                if sw:
                    bs.scr.echo('Trails are already on for group {}'.format(grp))
                else:
                    bs.scr.echo('Trails are already off for group {}'.format(grp))
                return
        else:
            bs.traf.iTrails.swgrp[grp.upper()] = sw

        if sw:
            self.overlap(grp.upper())

        bs.traf.iTrails.flag_swgrp = True
        bs.traf.iTrails.change = True

    @stack.command(name='SETCLR', brief='SETCLR GRP COLOR')
    def setclr(self, grp: str = '', color: str = ''):
        """
        Function: set color for trails
        Args:
            grp:    group
        Returns: -

        Created by: Lars Dijkstra
        Date: 29-11-2022
        """

        if grp.upper() not in bs.traf.iTrails.setgrp:
            bs.traf.iTrails.setgrp[grp.upper()] = []
            bs.traf.iTrails.swgrp[grp.upper()] = False

        color_dict = {'RED': (255, 0, 0), 'ORANGE': (255, 165, 0), 'CYAN': (0, 255, 255), 'BLACK': (0, 0, 0),
                      'YELLOW': (255, 255, 0), 'MAGENTA': (255, 0, 255), 'TEAL': (0, 128, 128), 'NAVY': (0, 0, 128),
                      'LIME': (0, 255, 0), 'GREEN': (0, 255, 0), 'GRAY': (169, 169, 169)}

        color = color.upper()
        if color in color_dict:
            color = color_dict[color]
        else:
            bs.scr.echo('Color {} was not defined in the color dictionary. No changes applied.'.format(color))
            return

        bs.traf.iTrails.clrs[grp.upper()] = color

        bs.traf.iTrails.flag_clrchange = True
        bs.traf.iTrails.change = True

    @stack.command(name='TRLTIME', brief='TRLTIME SIMTIME')
    def settrailtime(self, time: str = ''):
        """
        Function: set timestep from which group trails are shown
        Args:
            time:    timestep from which trails are shown on screen
        Returns: -

        Created by: Lars Dijkstra
        Date: 29-11-2022
        """

        if time[0] == '-':
            time = bs.sim.simt - int(time[1:])
            if time < 0:
                time = 0
        if time != bs.traf.iTrails.time:
            bs.traf.iTrails.time = int(time)

    @stack.command(name='TRLOFF', brief='TRLOFF')
    def trloff(self):
        """
        Function: set all trail switches to false
        Args:
            -
        Returns: -

        Created by: Lars Dijkstra
        Date: 29-11-2022
        """

        for group in bs.traf.iTrails.swgrp:
            bs.traf.iTrails.swgrp[group] = False

        bs.traf.iTrails.flag_swgrp = True
        bs.traf.iTrails.change = True

    @stack.command(name='DISCO', brief='TRLOFF')
    def atrloff(self):
        """
        Function: set all trail switches to false
        Args:
            -
        Returns: -

        Created by: Lars Dijkstra
        Date: 29-11-2022
        """

        for group in bs.traf.iTrails.swgrp:
            bs.traf.iTrails.swgrp[group] = False

        bs.traf.iTrails.flag_swgrp = True
        bs.traf.iTrails.change = True
