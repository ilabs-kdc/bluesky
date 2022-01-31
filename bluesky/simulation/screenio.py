""" ScreenIO is a screen proxy on the simulation side for the QTGL implementation of BlueSky."""
import time
import numpy as np

# Local imports
import bluesky as bs
from bluesky import stack
from bluesky.tools import areafilter, geo, misc
from bluesky.core.walltime import Timer

bs.settings.set_variable_defaults(screendt=0.2)

class ScreenIO:
    """Class within sim task which sends/receives data to/from GUI task"""

    # =========================================================================
    # Settings
    # =========================================================================
    # Update rate of simulation info messages [Hz]
    siminfo_rate = 1

    # Update rate of aircraft update messages [Hz]
    acupdate_rate = 5

    # =========================================================================
    # Functions
    # =========================================================================
    def __init__(self):
        # Screen state defaults
        self.def_pan     = (0.0, 0.0)
        self.def_zoom    = 1.0
        # Screen state overrides per client
        self.client_pan  = dict()
        self.client_zoom = dict()
        self.client_ar   = dict()
        self.route_acid  = dict()

        # Dicts of custom aircraft and group colors
        self.custacclr = dict()
        self.custgrclr = dict()

        # Timing bookkeeping counters
        self.prevtime    = 0.0
        self.samplecount = 0
        self.prevcount   = 0

        # Timing send aircraft data
        self.acdt = max(bs.settings.screendt, 1/self.acupdate_rate)
        self.prevactime = -self.acdt
        self.prevacdata = dict()

        # Output event timers
        self.slow_timer = Timer()
        self.slow_timer.timeout.connect(self.send_siminfo)
        self.slow_timer.timeout.connect(self.send_route_data)
        self.slow_timer.timeout.connect(self.send_trails)
        self.slow_timer.start(int(1000 / self.siminfo_rate))

        self.fast_timer = Timer()
        self.fast_timer.timeout.connect(self.send_aircraft_data)
        self.fast_timer.start(int(1000 / self.acupdate_rate))

    def step(self):
        if bs.sim.state == bs.OP:
            self.samplecount += 1

    def reset(self):
        self.custacclr = dict()
        self.custgrclr = dict()
        self.samplecount = 0
        self.prevcount   = 0
        self.prevtime    = 0.0

        self.prevactime = -bs.settings.screendt
        self.prevacdata = dict()

        # Communicate reset to gui
        bs.net.send_event(b'RESET', b'ALL')

    def echo(self, text='', flags=0):
        bs.net.send_event(b'ECHO', dict(text=text, flags=flags))

    def cmdline(self, text):
        bs.net.send_event(b'CMDLINE', text)

    def getviewctr(self):
        return self.client_pan.get(stack.sender()) or self.def_pan

    def getviewbounds(self):
        # Get appropriate lat/lon/zoom/aspect ratio
        sender   = stack.sender()
        lat, lon = self.client_pan.get(sender) or self.def_pan
        zoom     = self.client_zoom.get(sender) or self.def_zoom
        ar       = self.client_ar.get(sender) or 1.0

        lat0 = lat - 1.0 / (zoom * ar)
        lat1 = lat + 1.0 / (zoom * ar)
        lon0 = lon - 1.0 / (zoom * np.cos(np.radians(lat)))
        lon1 = lon + 1.0 / (zoom * np.cos(np.radians(lat)))
        return lat0, lat1, lon0, lon1

    def setscreenrange(self, screenr):
        """
        Function: Set the radar screen range (radius)
        Args:
            screenr:    screen radius (nm) [float]
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        # Get appropriate lat/lon/aspect ratio
        sender = stack.sender()
        lat, lon = self.client_pan.get(sender) or self.def_pan
        ar = self.client_ar.get(sender) or 1.0

        # Get maximum latitude and longitude
        latmax = geo.qdrpos(lat, lon, 0, screenr)[0] + 0.1
        lonmax = geo.qdrpos(lat, lon, 90, screenr)[1] + 0.03

        # Determine zoom
        zoomlat = 1/((latmax - lat)*ar)
        zoomlon = 1/((lonmax - lon)*np.cos(np.radians(lat)))

        zoom = min(zoomlat, zoomlon)

        self.zoom(zoom, True)

    def zoom(self, zoom, absolute=True):
        sender    = stack.sender()
        if sender:
            if absolute:
                self.client_zoom[sender] = zoom
            else:
                self.client_zoom[sender] = zoom * self.client_zoom.get(sender, self.def_zoom)
        else:
            self.def_zoom = zoom * (1.0 if absolute else self.def_zoom)
            self.client_zoom.clear()

        bs.net.send_event(b'PANZOOM', dict(zoom=zoom, absolute=absolute))

    def color(self, name, r, g, b):
        ''' Set custom color for aircraft or shape. '''
        data = dict(color=(r, g, b))
        if name in bs.traf.groups:
            groupmask = bs.traf.groups.groups[name]
            data['groupid'] = groupmask
            self.custgrclr[groupmask] = (r, g, b)
        elif name in bs.traf.id:
            data['acid'] = name
            self.custacclr[name] = (r, g, b)
        elif areafilter.hasArea(name):
            data['polyid'] = name
            areafilter.basic_shapes[name].raw['color'] = (r, g, b)
        else:
            return False, 'No object found with name ' + name
        bs.net.send_event(b'COLOR', data)
        return True

    def pan(self, *args):
        ''' Move center of display, relative of to absolute position lat,lon '''
        lat, lon = 0, 0
        absolute = False
        if args[0] == "LEFT":
            lon = -0.5
        elif args[0] == "RIGHT":
            lon = 0.5
        elif args[0] == "UP":
            lat = 0.5
        elif args[0] == "DOWN":
            lat = -0.5
        else:
            absolute = True
            lat, lon = args

        sender    = stack.sender()
        if sender:
            if absolute:
                self.client_pan[sender] = (lat, lon)
            else:
                ll = self.client_pan.get(sender) or self.def_pan
                self.client_pan[sender] = (lat + ll[0], lon + ll[1])
        else:
            self.def_pan = (lat,lon) if absolute else (lat + self.def_pan[0],
                                                       lon + self.def_pan[1])
            self.client_pan.clear()

        bs.net.send_event(b'PANZOOM', dict(pan=(lat,lon), absolute=absolute))

    def shownd(self, acid):
        bs.net.send_event(b'SHOWND', acid)

    def symbol(self):
        bs.net.send_event(b'DISPLAYFLAG', dict(flag='SYM'))

    def feature(self, switch, argument=None):
        bs.net.send_event(b'DISPLAYFLAG', dict(flag=switch, args=argument))

    def trails(self,sw):
        bs.net.send_event(b'DISPLAYFLAG', dict(flag='TRAIL', args=sw))

    def setatcmode(self, mode):
        """
        Function: Set the ATC mode
        Args:
            mode:   ATC mode
        Returns: -

        Created by: Bob van Dillen
        Date: 23-12-2021
        """

        if mode.upper() in ['APP', 'ACC', 'TWR', 'BLUESKY']:
            bs.net.send_event(b'DISPLAYFLAG', dict(flag='ATCMODE', args=mode.upper()))
        else:
            return False, 'SETATCMODE: ATC Mode not recognized'

    def showroute(self, acid):
        ''' Toggle show route for this aircraft '''
        self.route_acid[stack.sender()] = acid
        return True

    def addnavwpt(self, name, lat, lon):
        ''' Add custom waypoint to visualization '''
        bs.net.send_event(b'DEFWPT', dict(name=name, lat=lat, lon=lon))
        return True

    def show_file_dialog(self):
        bs.net.send_event(b'SHOWDIALOG', dict(dialog='OPENFILE'))
        return ''

    def show_cmd_doc(self, cmd=''):
        bs.net.send_event(b'SHOWDIALOG', dict(dialog='DOC', args=cmd))

    def filteralt(self, *args):
        bs.net.send_event(b'DISPLAYFLAG', dict(flag='FILTERALT', args=args))

    def objappend(self, objtype, objname, data):
        """Add a drawing object to the radar screen using the following inputs:
           objtype: "LINE"/"POLY" /"BOX"/"CIRCLE" = string with type of object
           objname: string with a name as key for reference
           objdata: lat,lon data, depending on type:
                    POLY/LINE: lat0,lon0,lat1,lon1,lat2,lon2,....
                    BOX : lat0,lon0,lat1,lon1   (bounding box coordinates)
                    CIRCLE: latctr,lonctr,radiusnm  (circle parameters)
        """
        bs.net.send_event(b'SHAPE', dict(name=objname, shape=objtype, coordinates=data))

    def event(self, eventname, eventdata, sender_rte):
        if eventname == b'PANZOOM':
            self.client_pan[sender_rte[-1]]  = eventdata['pan']
            self.client_zoom[sender_rte[-1]] = eventdata['zoom']
            self.client_ar[sender_rte[-1]]   = eventdata['ar']
            return True

        return False

    # =========================================================================
    # Slots
    # =========================================================================
    def send_siminfo(self):
        t  = time.time()
        dt = np.maximum(t - self.prevtime, 0.00001)  # avoid divide by 0
        speed = (self.samplecount - self.prevcount) / dt * bs.sim.simdt
        bs.net.send_stream(b'SIMINFO', (speed, bs.sim.simdt, bs.sim.simt,
            str(bs.sim.utc.replace(microsecond=0)), bs.traf.ntraf, bs.sim.state, stack.get_scenname()))
        self.prevtime  = t
        self.prevcount = self.samplecount

    def send_trails(self):
        # Trails, send only new line segments to be added
        if bs.traf.trails.active and len(bs.traf.trails.newlat0) > 0:
            data = dict(swtrails=bs.traf.trails.active,
                        traillat0=bs.traf.trails.newlat0,
                        traillon0=bs.traf.trails.newlon0,
                        traillat1=bs.traf.trails.newlat1,
                        traillon1=bs.traf.trails.newlon1)
            bs.traf.trails.clearnew()
            bs.net.send_stream(b'TRAILS', data)

    def send_aircraft_data(self):
        # Interval update data
        if bs.sim.simt - self.prevactime >= self.acdt:
            data = dict()

            data['simt']        = bs.sim.simt
            data['id']          = bs.traf.id
            data['lat']         = bs.traf.lat
            data['lon']         = bs.traf.lon
            data['alt']         = bs.traf.alt
            data['tas']         = bs.traf.tas
            data['cas']         = bs.traf.cas
            data['gs']          = bs.traf.gs
            data['ingroup']     = bs.traf.groups.ingroup
            data['inconf']      = bs.traf.cd.inconf
            data['type']        = bs.traf.type
            data['tcpamax']     = bs.traf.cd.tcpamax
            data['rpz']         = bs.traf.cd.rpz
            data['nconf_cur']   = len(bs.traf.cd.confpairs_unique)
            data['nconf_tot']   = len(bs.traf.cd.confpairs_all)
            data['nlos_cur']    = len(bs.traf.cd.lospairs_unique)
            data['nlos_tot']    = len(bs.traf.cd.lospairs_all)
            data['trk']         = bs.traf.trk
            data['vs']          = bs.traf.vs
            data['vmin']        = bs.traf.perf.vmin
            data['vmax']        = bs.traf.perf.vmax

            # LVNL Variables
            data['flighttype']  = bs.traf.lvnlvars.flighttype
            data['wtc']         = bs.traf.lvnlvars.wtc

            # Transition level as defined in traf
            data['translvl']    = bs.traf.translvl

            # ASAS resolutions for visualization. Only send when evaluated
            data['asastas']     = bs.traf.cr.tas
            data['asastrk']     = bs.traf.cr.trk

            # History symbols
            data['histsymblat'] = bs.traf.histsymb.lat
            data['histsymblon'] = bs.traf.histsymb.lon

            # Take start up into account
            if bs.sim.simt != 0:
                self.prevactime = bs.sim.simt
                self.prevacdata = data
        else:
            data = self.prevacdata

        # Always update data (take aircraft create/delete into account)
        if 'id' in data.keys():
            itrafsend = misc.get_indices(bs.traf.id, data['id'])  # aircraft that are in the previous data
        else:
            itrafsend = []

        data['arr']      = np.array(bs.traf.lvnlvars.arr)[itrafsend].tolist()
        data['idsel']    = bs.traf.id_select
        data['lblpos']   = np.array(bs.traf.lvnlvars.lblpos)[itrafsend].tolist()
        data['mlbl']     = bs.traf.lvnlvars.mlbl[itrafsend]
        data['rel']      = bs.traf.lvnlvars.rel[itrafsend]
        data['rwy']      = np.array(bs.traf.lvnlvars.rwy)[itrafsend].tolist()
        data['selhdg']   = bs.traf.selhdg[itrafsend]
        data['selalt']   = bs.traf.selalt[itrafsend]
        data['selspd']   = bs.traf.selspd[itrafsend]
        data['sid']      = np.array(bs.traf.lvnlvars.sid)[itrafsend].tolist()
        data['ssr']      = bs.traf.lvnlvars.ssr[itrafsend]
        data['ssrlbl']   = np.array(bs.traf.lvnlvars.ssrlbl)[itrafsend].tolist()
        data['tracklbl'] = bs.traf.lvnlvars.tracklbl[itrafsend]
        data['uco']      = bs.traf.lvnlvars.uco[itrafsend]

        # Send data
        bs.net.send_stream(b'ACDATA', data)

    def send_route_data(self):
        for sender, acid in self.route_acid.items():
            data               = dict()
            data['acid']       = acid
            idx   = bs.traf.id2idx(acid)
            if idx >= 0:
                route          = bs.traf.ap.route[idx]
                data['iactwp'] = route.iactwp

                # We also need the corresponding aircraft position
                data['aclat']  = bs.traf.lat[idx]
                data['aclon']  = bs.traf.lon[idx]

                data['wplat']  = route.wplat
                data['wplon']  = route.wplon

                data['wpalt']  = route.wpalt
                data['wpspd']  = route.wpspd

                data['wpname'] = route.wpname

            bs.net.send_stream(b'ROUTEDATA' + (sender or b'*'), data)  # Send route data to GUI
